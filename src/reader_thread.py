import traceback

from PyQt4.QtCore import pyqtSlot, QThread, QMutex, QWaitCondition
from enum import Enum

from worker_thread import WorkerThread
from media import FrameError, MediaClosedError, NotSeekableError, CursorPosition
import main
from analysis import PreviewOption
from queue import Full
import messages

class ReaderState(Enum):
    GettingRaw = 1
    PuttingRaw = 2
    PuttingPreview = 3

class ReaderThread(WorkerThread):
    def __init__(self, notifier):
        super(ReaderThread, self).__init__(notifier)

    def process_command(self, command, kwargs):
        if command == "seek":
            pos = kwargs['pos']
            main.rawqueue.clear()
            main.previewqueue.clear()
            main.ic.media.seek(pos)
        else:
            super(ReaderThread, self).process_command(command, kwargs)

    def work_started(self):
        self.state = ReaderState.GettingRaw
        self._raw = None

    def do_work(self):
        rawqueue     = main.rawqueue
        previewqueue = main.previewqueue
        media        = main.ic.media

        try:
            if self.state is ReaderState.GettingRaw:
                self._mediastate, self._raw =  media.next()
                if self._raw is not None:
                    self.state = ReaderState.PuttingRaw

            if self.state is ReaderState.PuttingRaw:
                rawqueue.put((self._mediastate, self._raw), False)
                self.state = ReaderState.PuttingPreview

            if self.state is ReaderState.PuttingPreview:
                if main.ic.preview is PreviewOption.Raw:
                    previewqueue.put((self._mediastate, self._raw), False)
                    self.state = ReaderState.GettingRaw
                    return True
                else:
                    self.state = ReaderState.GettingRaw
                    return True

        except Full as e:
            pass
        except FrameError as e:
            self.state = ReaderState.GettingRaw
        except EOFError as e:
            if media.state.seekable and media.loop:
                media.seek(CursorPosition.Begin)
                self.state = ReaderState.GettingRaw
            else:
                raise
        except Exception as e:
            raise
