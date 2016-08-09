import sys
import logging

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QTimer, QCoreApplication


class Teste(object):
    def receive_message(self, mtype, mdata, sender_id):
        print mtype, mdata, sender_id

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s [%(levelname)s]: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    from gui import application
    from ic.video_source import VideoSource
    from ic.frame_stream import FrameStream

    app = application.Application(sys.argv)

    vs  = VideoSource()
    fs = FrameStream(1, 1)

    from gui.main_window import MainWindow

    app.import_resources()

    # Load ui objects
    mainWindow = app.load_ui("main_window", "mainWindow.ui", MainWindow())

    mainWindow.show()

    app.exec_()


    sys.exit()
