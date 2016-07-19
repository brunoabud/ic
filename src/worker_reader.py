import traceback

from PyQt4.QtCore import pyqtSlot
from enum import Enum

from worker import ICWorker
from media import FrameError, MediaClosedError, NotSeekableError, CursorPosition
import main
from analysis import PreviewOption
from queue import Full

class ReaderState(Enum):
    GettingRaw = 1
    PuttingRaw = 2
    PuttingPreview = 3

class ICWorker_VIMOReader(ICWorker):
    def __init__(self):
        super(ICWorker_VIMOReader, self).__init__('reader')

    @pyqtSlot()
    def _start_work(self):
        self.state = ReaderState.GettingRaw
        self._raw = None

    def receive_message(self, message_type, message_data, sender):
        if message_type == 'media_seek':
            self.push_command("seek", {'pos': message_data['pos']})
        else:
            super(ICWorker_VIMOReader, self).receive_message(message_type, message_data, sender)

    def process_command(self, command, kwargs):
        if command == "seek":
            pos = kwargs['pos']
            main.rawqueue.clear()
            main.previewqueue.clear()
            self._start_work()
            main.processor._start_work()
            main.ic.media.seek(pos)
        else:
            super(ICWorker_VIMOReader, self).process_command(command, kwargs)

    @pyqtSlot()
    def _do_work(self):
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
            print "DEU FRAME"
        except MediaClosedError:
            print  "can\'t read from a closed media"
            raise
        except EOFError as e:
            print "EOFOU READER"
            if media.state.seekable and media.loop:
                media.seek(CursorPosition.Begin)
                self.state = ReaderState.GettingRaw
            else:
                raise
        except Exception as e:
            print 'deu outra'
            traceback.print_exc()
            raise
