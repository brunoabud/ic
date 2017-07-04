# coding: utf-8
# Copyright (C) 2016 Bruno Abude Cardoso
#
# Imagem Cinemática is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Imagem Cinemática is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from PyQt4.QtCore import QThread, pyqtSlot, pyqtSignal, QMutex, QWaitCondition
from PyQt4.QtGui import QImage
import numpy as np
import cv2

from ic.queue import Queue, Empty, Full
from ic import messages
from ic import settings
from ic.filter_rack import FilterPageFlowError

LOG = logging.getLogger(__name__)

def valid_frame(f):
    return all([i is not None for i in f])

class FSWorkerThread(QThread):
    """Base class for FrameStream worker threads.

    """
    # The worker threads are modeled as Finite State Machines.
    # At each iteration of the main loop, it will try to process a state and the
    # next one, until it fails or reachs the last state. So, instead of doing
    # long and locking operations, its splitted into smaller non-locking operations.
    # If a state fails, the next iteration will try to process that state again, if
    # the thread is still active.

    STATE_IDLE = 0x00
    _SLEEP_TIME = 25

    def __init__(self, fs):
        super(FSWorkerThread, self).__init__()
        self._fs = fs
        # The flag used to tell the main loop to exit as soon as possible, lea-
        # ding to the end of the thread
        self.abort_flag = False
        self.state = FSWorkerThread.STATE_IDLE
        self.error_flag = False
        self.work_done = False
        self.old_state = self.state

    def run(self):
        # Tell the FS that the thread is becoming active
        self._fs._worker_activated()
        while not self.abort_flag:
            # Lock the mutex
            self._fs.mutex.lock()
            # Check for the freezing condition
            if self._fs.frozen:
                self._fs._worker_freezed()
                self._fs.freeze_condition.wait(self._fs.mutex)
                self._fs._worker_unfreezed()

            if not self._fs.active or self.error_flag or self._fs.single_shot:
                if self._fs.single_shot and not self.work_done:
                    pass
                else:
                    self.error_flag = False
                    # Tell the FS that this thread is not active
                    self._fs._worker_deactived()
                    # Wait to be woken up
                    self._fs.startCondition.wait(self._fs.mutex)
                    # Check if it is a single shot work
                    if self._fs.single_shot:
                        self.work_done = False
                    # Check if it woke up just to die :(
                    if self.abort_flag:
                        self._fs.mutex.unlock()
                        break
                    # Tell the FS that this thread is active
                    self._fs._worker_activated()
                    # Reset the worker states
                    self.work_started()

            # Unlock the mutex
            self._fs.mutex.unlock()
            try:
                # Do the damn work
                self.work_done = self.do_work()
            except:
                LOG.error("Error when doing work", exc_info=True)
                self.error_flag = True
            # Give it a break
            self.msleep(FSWorkerThread._SLEEP_TIME)

    # This should be overrided by the subclasses
    def do_work(self):
        return True

    # Call this when the thread wakes up from an idle state. This is necessary
    # because the thread can be stopped in the middle of the work.
    def work_started(self):
        pass

class VideoInputThread(FSWorkerThread):
    """Worker thread responsible for getting frames from the video source.

    """
    # The states of this worker. Each state is considered a step of the work.
    # Trying to get the frame from the plugin
    VI_GETTING_RAW_FRAME = 0x01
    # Trying to put the frame into the raw queue
    VI_PUTTING_FRAME     = 0x02

    def __init__(self, fs):
        super(VideoInputThread, self).__init__(fs)

    def do_work(self):
        plugin = self._fs._engine.input_plugin
        if self.state == VideoInputThread.VI_GETTING_RAW_FRAME:
            try:
                plugin = self._fs._engine.input_plugin
                self.frame = plugin.next()

                self.state = VideoInputThread.VI_PUTTING_FRAME
            except EOFError:
                if self._fs.loop:
                    plugin.seek(0)
                else:
                    self.error_flag = True
            except:
                raise

        if self.state == VideoInputThread.VI_PUTTING_FRAME:
            try:
                self._fs._engine.raw_queue.put(self.frame, False)
                self.frame = None
                self.state = VideoInputThread.VI_GETTING_RAW_FRAME
                # Signal end of the work
                return True
            except:
                pass

    def work_started(self):
        self.state = VideoInputThread.VI_GETTING_RAW_FRAME
        self.frame = None

class VideoProcessingThread(FSWorkerThread):
    """Thread responsible for filtering and sending frames to the analysis plugin.

        All the heavy work will be done here. This thread is also responsible
        for putting frames in the preview queue, depending on the user option.

    """

    VP_GETTING_RAW_FRAME = 0x01
    VP_PUTTING_RAW_PREVIEW = 0x02
    VP_PROCESSING = 0x03
    VP_PUTTING_PROCESSED_PREVIEW = 0x04
    VP_DUMPING_BUFFER = 0x05

    def __init__(self, fs):
        super(VideoProcessingThread, self).__init__(fs)

    def dump_targets_buffer(self):
        targets = self._fs._engine.targets_buffer
        preview = self._fs._engine.preview_queue
        if self.buffer is None:
            self.buffer = targets
            for target in self.buffer:
                if target in ["pos", "timestamp"]:
                    continue
                colorspace, data = self.buffer[target]

                data = cv2.cvtColor(data, getattr(cv2, "COLOR_%s2RGB" % colorspace))
                img = QImage(data.tostring(), data.shape[1], data.shape[0], QImage.Format_RGB888)

                self.buffer[target] = ("qimage", img)
            self._fs._engine.targets_buffer = dict.fromkeys(targets)
        preview.put(self.buffer, False)
        self.buffer = None

    def do_work(self):
        engine = self._fs._engine
        raw_queue = engine.raw_queue
        preview_queue = engine.preview_queue
        targets_buffer = engine.targets_buffer

        # VP_GETTING_RAW_FRAME
        # At this state the worker is trying to get a
        # frame from the raw queue, it uses a no wait call that raises the
        # `Empty` exception if the queue has no frames. The worker will ignore
        # the exception and if a frame was succesfully acquired, it will change
        # the state to VP_PUTTIN_RAW_PREVIEW
        if self.state == VideoProcessingThread.VP_GETTING_RAW_FRAME:
            try:
                self.frame = raw_queue.get(False)
                if valid_frame(self.frame):
                    targets_buffer["pos"] = self.frame[2]
                    targets_buffer["timestamp"] = self.frame[3]
                    try:
                        self.frame = engine.filter_rack["Raw"].apply_filters(self.frame)
                        self.state = VideoProcessingThread.VP_PROCESSING
                    except:
                        self._fs.stop()
                        messages.post("UI_error_message", ("Flow error on filter rack [VideoProcessing]"
                            "There is an error in the filter rack flow, the application will be paused."), self)
                        LOG.debug("", exc_info=True)
            except Empty:
                pass

        if self.state == VideoProcessingThread.VP_PROCESSING:
            analysis_plugin = engine.analysis_plugin
            if analysis_plugin is None:
                # There is no analysis plugin loaded so ignore it
                self.state = VideoProcessingThread.VP_DUMPING_BUFFER
            else:
                try:
                    colorspace, data, pos, timestamp = self.frame
                    colorspace, data = analysis_plugin.process_frame(self.frame)
                    if "processed" in targets_buffer:
                        targets_buffer["processed"] = (colorspace, np.copy(data))
                    self.state = VideoProcessingThread.VP_DUMPING_BUFFER
                except FilterPageFlowError as e:
                    self._fs.stop()
                    messages.post("UI_error_message", ("Flow error on filter rack;"
                        "There is an error in the filter rack flow, the application will be paused."), self)
                    LOG.error("", exc_info=True)
                except Exception as e:
                    self._fs.stop()
                    messages.post("UI_error_message", "Unknown Error;"+
                        "%(1)s: %(2)s" % {"1": str(type(e)), "2": str(e.message)}, self)
                    LOG.debug("Erro", exc_info=True)

        if self.state == VideoProcessingThread.VP_DUMPING_BUFFER:
            try:
                self.dump_targets_buffer()
                self.state = VideoProcessingThread.VP_GETTING_RAW_FRAME
                return True
            except:
                pass


    def work_started(self):
        self.state = VideoProcessingThread.VP_GETTING_RAW_FRAME
        self.frame = None
        self.buffer = None

class FrameStream(object):
    """This class responsible for managing the flow of frames.

    It reads the frames, pass them through the filter rack and sends them to
    the analysis module. It holds the queues containing the frames.

    The reading is done in one thread and the processing in another, both sepa-
    rated from the main thread.

    """
    # The current state of the FS can be described by these constants
    STATE_IDLE = 0x0
    STATE_STARTED = 0x2
    STATE_WAITING_TO_STOP = 0x3
    STATE_WAITING_TO_START = 0x4

    _INSTANCE = None

    def __init__(self, engine):
        self._engine = engine
        # Create the Raw Frames Queue, where the frames got from the Video Source
        # will be put
        # The thread responsible for reading the frames.
        self._input_thread = VideoInputThread(self)
        # The thread responsible for pumping the frame into the filter rack
        # and analysis plugin
        self._processor_thread = VideoProcessingThread(self)
        # The state of the frame stream
        self.state = FrameStream.STATE_IDLE
        # Is the FS active (reading and processing frames)?
        self.active = False
        # Mutex used to access the FrameStream states from the WorkerThreads
        self.mutex = QMutex()
        # This member will hold the number of workers that are active, or "not idle"
        # this is necessary because to stop or start the frame stream, both wor-
        # kers need to stop or start, but they do this in the different moments.
        # This member, associated with the mutex, can safely control the workers
        # states.
        self.active_workers = 0
        # Number of worker threads
        self.worker_count   = 2
        self.frozen_workers = 0
        # Wait condition used to wake the workers from an idle state
        self.startCondition = QWaitCondition()
        # Sometimes will be useful to stream only a single frame (i.e. when the
        # user changes the position of the video cursor and it needs to read a
        # frame to update the view). This member signals that the current work
        # is supposed to be done only one time
        self.single_shot = False
        self.state = FrameStream.STATE_WAITING_TO_STOP
        # If True, the frame stream will seek the video source to 0 when it
        # reaches the last frame
        self.loop = True
        # When the workers must be stopped to do just one operation, this flag
        # is set to true
        self.frozen = False
        # The condition to unfreeze the workers
        self.freeze_condition = QWaitCondition()
        # Start the worker threads so the run() method will be called
        messages.register(self)
        self._processor_thread.start()
        self._input_thread.start()

    def _worker_freezed(self):
        self.frozen_workers += 1

    def _worker_unfreezed(self):
        self.frozen_workers -= 1

    def _worker_deactived(self):
        self.active_workers -= 1

        if self.state == FrameStream.STATE_WAITING_TO_STOP and self.active_workers == 0:
            if self.single_shot:
                self.single_shot = False
            else:
                messages.post("FS_stream_stopped", None, self)
                self.active = False
            self.state = FrameStream.STATE_IDLE

        # If a thread deactivated when active is True, something went wrong
        # so stop the other worker too
        if self.state == FrameStream.STATE_STARTED or self.state == FrameStream.STATE_WAITING_TO_START:
            if self.active_workers == 0:
                self.state = FrameStream.STATE_IDLE
                messages.post("FS_stream_stopped", None, self)
                self.active = False
            else:
                self.state = FrameStream.STATE_WAITING_TO_STOP
                self.active = False

    def _worker_activated(self):
        self.active_workers += 1

        if self.state == FrameStream.STATE_WAITING_TO_START and self.active_workers == self.worker_count:
            self.state = FrameStream.STATE_STARTED
            messages.post("FS_stream_started", None, self)

    def message_received(self, mtype, mdata, sender):
        pass

    def freeze(self):
        raise NotImplementedError()

    def unfreeze(self):
        raise NotImplementedError()

    def start(self, single_shot = False):
        """Start the frame stream.

        This methods starts the Video Input and Video Processing Threads.

        Args:
          single_shot (bool): Default is False. If True, do only one complete
            work step, resulting in only one frame being processed.
        """
        self.single_shot = single_shot
        # If IDLE just wake the threads and set active to true if it is not
        if self.state == FrameStream.STATE_IDLE:
            if self.single_shot:
                self.state = FrameStream.STATE_WAITING_TO_STOP
            else:
                self.state = FrameStream.STATE_WAITING_TO_START
                self.active = True
            self.startCondition.wakeAll()
        # If started or starting just ignore
        elif self.state == FrameStream.STATE_STARTED or self.state == FrameStream.STATE_WAITING_TO_START:
            pass
        # If waiting to stop, wait until it becomes IDLE
        elif self.state == FrameStream.STATE_WAITING_TO_STOP:
            while not self.state == FrameStream.STATE_IDLE:
                pass

            if self.single_shot:
                self.state = FrameStream.STATE_WAITING_TO_STOP
            else:
                self.state = FrameStream.STATE_WAITING_TO_START
                self.active = True
            self.startCondition.wakeAll()

    def stop(self):
        """Stop the frame stream.

        """
        # If IDLE just ignore
        if self.state == FrameStream.STATE_IDLE or self.state == FrameStream.STATE_WAITING_TO_STOP:
            pass
        # If it is waiting to start, wait until starts or go to idle
        elif self.state == FrameStream.STATE_WAITING_TO_START:
            # Make sure to wait just if it is not stopping
            while self.state != FrameStream.STATE_IDLE and self.state != FrameStream.STATE_WAITING_TO_STOP:
                # If started, tell to stop
                if self.state == FrameStream.STATE_STARTED:
                    self.state = FrameStream.STATE_WAITING_TO_STOP
                    self.active = False
                    break

        # If started change state
        elif self.state == FrameStream.STATE_STARTED:
            self.state = FrameStream.STATE_WAITING_TO_STOP
            self.active = False

    def seek(self, pos):
        """Change the position of the current frame, if possible.

        If the video source is seekable, this methods will seek to the given
        position, signaling the application about it.

        Args:
          pos (int): The new position.
        """
        # If the thread is waiting to start, wait it to start or stop
        if self.state == FrameStream.STATE_WAITING_TO_START:
            while not self.state == FrameStream.STATE_STARTED or not self.state == FrameStream.STATE_IDLE:
                pass

        # If the workers are running, freeze them and wait to clear the queues
        if self.state == FrameStream.STATE_STARTED:
            self.frozen = True
            while self.frozen_workers < self.worker_count:
                pass

        self._engine.raw_queue.clear()
        self._engine.preview_queue.clear()

        try:
            # Reset workers states
            self._input_thread.work_started()
            self._processor_thread.work_started()
            # Seek the Video Source
            new_pos = self._engine.input_plugin.seek(pos)
            messages.post("FS_stream_sought", ";".join([str(new_pos)]))
            p = self._engine.analysis_plugin
            if p is not None:
                try:
                    p.on_media_sought(new_pos)
                except:
                    LOG.error("", exc_info=True)

        except Exception as e:
            LOG.error("Seeking raised an error", exc_info=True)
        finally:
            if self.frozen:
                self.frozen = False
                self.freeze_condition.wakeAll()

        if self.state == FrameStream.STATE_IDLE:
            self.single_shot = True
            self.start()

