
from PyQt4.QtCore import pyqtSlot
from enum import Enum

from worker import ICWorker
import main
from queue import Full, Empty
from analysis import PreviewOption

class ProcessorState(Enum):
    """Currente state of the Processor.

    The processor is considered a Finite State Machine."""
    GettingRaw = 1
    Filtering = 2
    PuttingFiltered = 3
    Processing = 4
    PuttingProcessed = 5


class ICWorker_Processor(ICWorker):
    def __init__(self):
        super(ICWorker_Processor, self).__init__('processor')

    @pyqtSlot()
    def _start_work(self):
        self.state = ProcessorState.GettingRaw
        self._frame = None

    @pyqtSlot()
    def _do_work(self):
        try:
            ic = main.ic
            rawqueue = main.rawqueue
            previewqueue = main.previewqueue
            if self.state is ProcessorState.GettingRaw:
                self._mediastate, self._frame = rawqueue.get(timeout = 0.05)
                self.state = ProcessorState.Filtering

            if self.state is ProcessorState.Filtering:
                for f in ic.filter_rack:
                    if f.ignore: continue
                    try:
                        self._frame = f.plugin.applyFilter(self._frame)
                    except:
                        print "Plugin '{:03d}' raised an exception and will be ignored".format(f.fid)
                self.state = ProcessorState.PuttingFiltered

            if self.state is ProcessorState.PuttingFiltered:
                if ic.preview is PreviewOption.PostFiltering:
                    previewqueue.put((self._mediastate, self._frame), False)
                    self.state = ProcessorState.Processing
                else:
                    self.state = ProcessorState.Processing

            if self.state is ProcessorState.Processing:
                if ic.VAMO is None:
                    self.state = ProcessorState.GettingRaw
                else:
                    self._frame = ic.VAMO.process_frame(self._mediastate, self._frame)
                    self.state = ProcessorState.PuttingProcessed

            if self.state is ProcessorState.PuttingProcessed:
                if ic.preview is PreviewOption.PostProcessing:
                    previewqueue.put((self._mediastate, self._frame), False)
                    self.state = ProcessorState.GettingRaw
                    return True
                else:
                    self.state = ProcessorState.GettingRaw
                    return True

        except (Full, Empty) as e:
            pass
        except Exception as e:
            print "A"
            import traceback
            traceback.print_exc()
            raise
