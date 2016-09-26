import traceback as tb
import logging
log = logging.getLogger(__name__)

from PyQt4.QtCore import QThread, pyqtSlot, pyqtSignal, QMutex, QWaitCondition

from ic.queue import Queue
from gui.application import get_app, Application
from ic.filter_rack import FilterRack
from ic.queue import Empty, Full
from ic import engine
from ic.video_source import SourceClosedError

class FSWorkerThread(QThread):
    """Base class for FrameStream worker threads.

    """
    #The worker threads are modeled as Finite State Machines.
    #At each iteration of the main loop, it will try to process a state and the
    #next one, until it fails or reachs the last state. So, instead of doing
    #long and locking operations, it splits it in smaller non-locking operations.
    #If a state fails, the next iteration will try to process that state again.
    #The thread can also be aborted on intermediary states, not only on the last
    #one.

    # Doing nothing
    STATE_IDLE              = 0x00

    _SLEEP_TIME = 20

    def __init__(self, fs):
        super(QThread, self).__init__()
        # The frame stream instance
        self.fs = fs
        # The flag used to tell the main loop to exit as soon as possible, lea-
        # ding to the end of the thread
        self.abort_flag = False

        self.state = FSWorkerThread.STATE_IDLE
        self.error_flag = False
        self.work_done = False

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
                log.error("Error when doing work", exc_info=True)
                self.error_flag = True

            # Give her a break, poor girl
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
    # Trying to put the frame in the raw queue
    VI_PUTTING_FRAME     = 0x02

    def __init__(self, fs):
        super(VideoInputThread, self).__init__(fs)
        self.plugin = None

    def do_work(self):
        if self.state == VideoInputThread.VI_GETTING_RAW_FRAME:
            try:
                app = get_app()
                vs  = engine.get_component("video_source")

                self.frame_state = {"pos": vs.tell(), "fps": vs.get_fps()}
                self.raw_frame = vs.next()

                if self.raw_frame is not None:
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
                self.fs.raw_queue.put((self.frame_state, self.raw_frame), False)
                self.raw_frame = None
                self.frame_state = None
                self.state = VideoInputThread.VI_GETTING_RAW_FRAME
                # Signal end of the work
                return True
            except:
                pass

    def work_started(self):
        self.state = VideoInputThread.VI_GETTING_RAW_FRAME
        self.raw_frame = None
        self.frame_state = None

class VideoProcessingThread(FSWorkerThread):
    """Thread responsible for filtering and sending frames to the analysis plugin.

        All the heavy work will be done here. This thread is also responsible
        for putting frames in the preview queue, depending on the user option.

    """

    VP_GETTING_RAW_FRAME         = 0x01
    VP_PUTTING_RAW_PREVIEW       = 0x02
    VP_FILTERING                 = 0x03
    VP_PUTTING_FILTERED_PREVIEW  = 0x04
    VP_PROCESSING                = 0x05
    VP_PUTTING_PROCESSED_PREVIEW = 0x06

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
                self.frame_state, self.raw_frame = self.fs.raw_queue.get(False)
                if self.raw_frame is not None:
                    self.state = VideoProcessingThread.VP_PUTTING_RAW_PREVIEW
            except Empty:
                pass

        if self.state == VideoProcessingThread.VP_PUTTING_RAW_PREVIEW:
            try:
                if get_app().user_options["preview_source"] == Application.OPT_PREVIEW_RAW:
                    self.fs.preview_queue.put((self.frame_state, self.raw_frame), False)
                    self.state = VideoProcessingThread.VP_FILTERING
                else:
                    self.state = VideoProcessingThread.VP_FILTERING
            except:
                pass

        if self.state == VideoProcessingThread.VP_FILTERING:
            self.filtered_frame = self.raw_frame
            for filter_element in engine.get_component("filter_rack"):
                if filter_element.ignore:
                    continue
                try:
                    app = get_app()
                    plugin = app.get_plugin(filter_element.fid)
                    self.filtered_frame = plugin.instance.apply_filter(self.filtered_frame)
                except:
                    engine.get_component("filter_rack").set_ignore(filter_element.fid, True)
            self.state = VideoProcessingThread.VP_PUTTING_FILTERED_PREVIEW

        if self.state == VideoProcessingThread.VP_PUTTING_FILTERED_PREVIEW:
            if get_app().user_options["preview_source"] == Application.OPT_PREVIEW_POST_FILTER:
                try:
                    self.fs.preview_queue.put((self.frame_state, self.filtered_frame), False)
                    self.state = VideoProcessingThread.VP_GETTING_RAW_FRAME
                    return True
                except:
                    pass
            else:
                self.state = VideoProcessingThread.VP_GETTING_RAW_FRAME
                return True

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

    :singleton
    """

    # The current state of the FS can be described by these constants
    STATE_IDLE                = 0x0
    STATE_STARTED             = 0x2
    STATE_WAITING_TO_STOP     = 0x3
    STATE_WAITING_TO_START    = 0x4

    _INSTANCE = None

    def __init__(self, raw_queue_len, preview_queue_len):
        assert FrameStream._INSTANCE is None
        FrameStream._INSTANCE = self

        # Create the Raw Frames Queue, where the frames got from the Video Source
        # will be put
        self.raw_queue     = Queue(raw_queue_len)

        # Create the Preview Queue, where the frames ready to be viewed by the
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
        pass

    def unfreeze(self):
        pass

    def start(self, single_shot = False):
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
        vs = engine.get_component("video_source")
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
            app = get_app()
            input_plugin = engine.get_input_plugin()
            if input_plugin is not None:
                pid = input_plugin["plugin_id"]
                p = engine.get_plugin(pid)
        except Exception as e:
            print "Seeking raised an error"
            print e.message
        finally:
            self.frozen = False
            self.freeze_condition.wakeAll()

        if self.state == FrameStream.STATE_IDLE:
            self.single_shot = True
            self.start()

    def _tell(self):
        pass
