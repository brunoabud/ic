from os.path import join as pjoin
import sys

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QThread

import main
import queue
import messages
import resources
import analysis
import main_window
from analysis_worker import AnalysisWorker

from console import Console

main.app_path     = sys.path[0]
main.app          = QApplication(sys.argv)
main.settings     = {
                'raw_length'        : 1                                 ,
                'preview_length'    : 1                                 ,
                'filter_dir'        : pjoin(main.app_path, 'filter_plugin')  ,
                'video_dir'         : pjoin(main.app_path, 'video_plugin')   ,
                'analysis_dir'      : pjoin(main.app_path, 'analysis_plugin'),
                'ui_dir'            : pjoin(main.app_path, 'ui')             ,
                'log_dir'           : pjoin(main.app_path, 'log')            ,
                'thread_exittimeout': 500                               ,
                }
main.previewqueue = queue.ICQueue(main.settings['preview_length'])
main.rawqueue     = queue.ICQueue(main.settings['raw_length'])

messages.init_message_system()

ret = -1
try:
    main.ic            = analysis.ICAnalysis()
    main.worker        = AnalysisWorker()
    main.consolewindow = Console()
    main.mainwindow    = main_window.ICMainWindow()

    main.consolewindow.show()
    main.mainwindow.frm_playback.init()
    main.mainwindow.showMaximized()

    ret = main.app.exec_()
except:
    import traceback
    traceback.print_exc()
finally:
    resources.qCleanupResources()
    sys.exit(ret)
