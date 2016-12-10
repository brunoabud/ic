# coding: latin-1
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
import numpy as np

from ic.queue import Queue
from gui.application import get_app, Application
from ic.filter_rack import FilterRack
from ic.queue import Empty, Full
from ic import get_engine
from ic.video_source import SourceClosedError
from filter_rack import FilterPageFlowError


LOG = logging.getLogger(__name__)


class Frame(object):
    """Class that represents a frame.

    Members:
      pos: Frame position.
      fps: FPS at the moment that the frame was read.
      size: The dimensions of the frame.
      data: A numpy ndarray containing the frame data.
      color_space: A string represeting the color space of the frame.
      length: The length of the media that contains the frame.
    """
    def __init__(self, pos, fps, size, color_space, length, data):
        self.pos = pos
        self.fps = fps
        self.size = size
        self.color_space = color_space
        self.length = length
        self.data = data

    def copy(self):
        """Returns a new Frame object containing the same data."""
        f = Frame(self.pos,
            self.fps, self.size,
            self.color_space,
            self.length, None
            )
        f.data = np.copy(self.data)
        return f

class FSWorkerThread(QThread):
    """Base class for FrameStream worker threads.

    """
    # The worker threads are modeled as Finite State Machines.
    # At each iteration of the main loop, it will try to process a state and the
    # next one, until it fails or reachs the last state. So, instead of doing
    # long and locking operations, its splitted into smaller non-locking operations.
    # If a state fails, the next iteration will try to process that state again.
    # The thread can also be aborted on intermediary states, not only on the last
    # one.
    STATE_IDLE              = 0x00
    _SLEEP_TIME = 20

    def __init__(self, fs):
        super(FSWorkerThread, self).__init__()
        self.fs = fs
        # The flag used to tell the main loop to exit as soon as possible, lea-
        # ding to the end of the thread
        self.abort_flag = False
        self.state = FSWorkerThread.STATE_IDLE
        self.error_flag = False
        self.work_done = False
        self.old_state = self.state

    def run(self):
        # Tell the FS that the thread is becoming active
        self.fs._worker_activated()
        while not self.abort_flag:
            # Lock the mutex
            self.fs.mutex.lock()
            # Check for the freezing condition
            if self.fs.frozen:
                self.fs._worker_freezed()
                self.fs.freeze_condition.wait(self.fs.mutex)
                self.fs._worker_unfreezed()

            if not self.fs.active or self.error_flag or self.fs.single_shot:
                if self.fs.single_shot and not self.work_done:
                    pass
                else:
                    self.error_flag = False
                    # Tell the FS that this thread is not active
                    self.fs._worker_deactived()
                    # Wait to be woken up
                    self.fs.startCondition.wait(self.fs.mutex)
                    # Check if it is a single shot work
                    if self.fs.single_shot:
                        self.work_done = False
                    # Check if it woke up just to die :(
                    if self.abort_flag:
                        self.fs.mutex.unlock()
                        break
                    # Tell the FS that this thread is active
                    self.fs._worker_activated()
                    # Reset the worker states
                    self.work_started()

            # Unlock the mutex
            self.fs.mutex.unlock()
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
        self.plugin = None

    def do_work(self):
        if self.state == VideoInputThread.VI_GETTING_RAW_FRAME:
            try:
                app = get_app()
                vs  = get_engine().get_component("video_source")

                self.source_state = vs.source_state()
                self.raw_frame = vs.next()

                if self.raw_frame is not None:
                    self.frame = Frame(self.source_state["pos"],
                                       self.source_state["fps"],
                                       self.source_state["size"],
                                       self.source_state["color_space"],
                                       self.source_state["length"],
                                       self.raw_frame
                        )
                    try:
                        fr = get_engine().get_component("filter_rack")
                        raw_page = fr.get_page("Raw")
                        self.frame = raw_page.apply_filters(self.frame)
                    except:
                        self.fs.stop()
                        get_app().post_message("error_frame_stream", {
                                               "type": FilterPageFlowError,
                                               "description": ""
                                               }, self.fs.m_id)
                    self.state = VideoInputThread.VI_PUTTING_FRAME
            except EOFError:
                if self.fs.loop:
                    vs.seek(0)
                else:
                    self.error_flag = True
            except SourceClosedError:
                self.error_flag = True
            except:
                raise

        if self.state == VideoInputThread.VI_PUTTING_FRAME:
            try:
                self.fs.raw_queue.put(self.frame, False)
                self.raw_frame = None
                self.source_state = None
                self.frame = None
                self.state = VideoInputThread.VI_GETTING_RAW_FRAME
                # Signal end of the work
                return True
            except:
                pass

    def work_started(self):
        self.state = VideoInputThread.VI_GETTING_RAW_FRAME
        self.raw_frame = None
        self.frame_state = None
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

    def __init__(self, fs):
        super(VideoProcessingThread, self).__init__(fs)

    def do_work(self):
        # VP_GETTING_RAW_FRAME
        # At this state the worker is trying to get a
        # frame from the raw queue, it uses a no wait call that raises the
        # `Empty` exception if the queue has no frames. The worker will ignore
        # the exception and if a frame was succesfully acquired, it will change
        # the state to VP_PUTTIN_RAW_PREVIEW
        if self.state == VideoProcessingThread.VP_GETTING_RAW_FRAME:
            try:
                self.raw_frame = self.fs.raw_queue.get(False)
                if self.raw_frame.data is not None:
                    self.state = VideoProcessingThread.VP_PUTTING_RAW_PREVIEW
            except Empty:
                pass

        if self.state == VideoProcessingThread.VP_PUTTING_RAW_PREVIEW:
            try:
                if get_app().user_options["preview_source"] == Application.OPT_PREVIEW_RAW:
                    self.fs.preview_queue.put(self.raw_frame, False)
                    self.state = VideoProcessingThread.VP_PROCESSING
                else:
                    self.state = VideoProcessingThread.VP_PROCESSING
            except:
                pass

        if self.state == VideoProcessingThread.VP_PROCESSING:
            try:
                plugin = get_engine().get_plugin(get_engine().get_analysis_plugin()["plugin_id"]).instance
            except:
                # There is no analysis plugin loaded so ignore it
                self.state = VideoProcessingThread.VP_GETTING_RAW_FRAME
                return True
            try:
                self.processed_frame = plugin.process_frame(self.raw_frame)
                if get_app().user_options["preview_source"] == Application.OPT_PREVIEW_POST_ANALYSIS:
                    self.state = VideoProcessingThread.VP_PUTTING_PROCESSED_PREVIEW
                else:
                    self.state = VideoProcessingThread.VP_GETTING_RAW_FRAME
                    return True
            except FilterPageFlowError as e:
                self.fs.stop()
                get_app().post_message("error_frame_stream", {
                                       "type": FilterPageFlowError,
                                       "description": ""
                                       }, self.fs.m_id)
            except Exception as e:
                self.fs.stop()
                get_app().post_message("error_frame_stream", {
                                       "type": type(e),
                                       "description": e.message
                                       }, self.fs.m_id)

        if self.state == VideoProcessingThread.VP_PUTTING_PROCESSED_PREVIEW:
            try:
                self.fs.preview_queue.put(self.processed_frame, False)
                self.state = VideoProcessingThread.VP_GETTING_RAW_FRAME
                return True
            except:
                pass

    def work_started(self):
        self.state = VideoProcessingThread.VP_GETTING_RAW_FRAME
        self.raw_frame = None
        self.frame_state = None
        self.filtered_frame = None

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

    def __init__(self, raw_queue_len, preview_queue_len):
        assert FrameStream._INSTANCE is None
        FrameStream._INSTANCE = self

        # Create the Raw Frames Queue, where the frames got from the Video Source
        # will be put
        self.raw_queue     = Queue(raw_queue_len)
        # The Preview Queue, where the frames ready to be viewed by the
        # user will be put. These frames can come from many places, it will
        # depend on the value of app.user_option["preview_source"]
        self.preview_queue = Queue(preview_queue_len)
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
        self._input_thread.start()
        self._processor_thread.start()
        self.m_id = get_app().register_message_listener(self)

    def _worker_freezed(self):
        self.frozen_workers += 1

    def _worker_unfreezed(self):
        self.frozen_workers -= 1

    def _worker_deactived(self):
        app = get_app()
        self.active_workers -= 1

        if self.state == FrameStream.STATE_WAITING_TO_STOP and self.active_workers == 0:
            if self.single_shot:
                self.single_shot = False
            else:
                app.post_message("frame_stream_stopped", {}, self.m_id)
                self.active = False
            self.state = FrameStream.STATE_IDLE

        # If a thread deactivated when active is True, something went wrong
        # so stop the other worker too
        if self.state == FrameStream.STATE_STARTED or self.state == FrameStream.STATE_WAITING_TO_START:
            if self.active_workers == 0:
                self.state = FrameStream.STATE_IDLE
                app.post_message("frame_stream_stopped", {}, self.m_id)
                self.active = False
            else:
                self.state = FrameStream.STATE_WAITING_TO_STOP
                self.active = False

    def _worker_activated(self):
        app = get_app()
        self.active_workers += 1

        if self.state == FrameStream.STATE_WAITING_TO_START and self.active_workers == self.worker_count:
            self.state = FrameStream.STATE_STARTED
            app.post_message("frame_stream_started", {}, self.m_id)

    def receive_message(self, mtype, mdata, sender):
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
        vs = get_engine().get_component("video_source")
        app = get_app()

        # If the thread is waiting to start, wait it to start or stop
        if self.state == FrameStream.STATE_WAITING_TO_START:
            while not self.state == FrameStream.STATE_STARTED or not self.state == FrameStream.STATE_IDLE:
                pass

        # If the workers are running, freeze them and wait to clear the queues
        if self.state == FrameStream.STATE_STARTED:
            self.frozen = True
            while self.frozen_workers < self.worker_count:
                pass

        self.preview_queue._clear()
        self.raw_queue._clear()

        try:
            # Reset workers states
            self._input_thread.work_started()
            self._processor_thread.work_started()
            # Seek the Video Source
            vs.seek(pos)
            app.post_message("frame_stream_sought", {"pos": pos}, self.m_id)

        except Exception as e:
            LOG.error("Seeking raised an error", exc_info=True)
        finally:
            if self.frozen:
                self.frozen = False
                self.freeze_condition.wakeAll()

        if self.state == FrameStream.STATE_IDLE:
            self.single_shot = True
            self.start()

    def _tell(self):
        pass
