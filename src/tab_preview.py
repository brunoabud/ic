#encoding: utf-8
from PyQt4.QtGui import  QImage, QWidget, QPixmap, QGridLayout
from PyQt4.QtCore import Qt
import cv2

from resizable_pixmap_label import QLabel_ResizablePixmap
import main


class ICTab_Preview(QWidget):
    def __init__(self, parent = None):
        super(ICTab_Preview, self).__init__(parent)

    def _cv2ToPixmap(self, frame):
        height, width, bytesPerComponent = frame.shape
        bytesPerLine = 3 * width
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        QImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        return QPixmap.fromImage(QImg)

    def show_frame(self, img = None):
        """Convert and show a cv2 frame (numpy.ndaray) object."""
        if img is not None:
            frame = self._cv2ToPixmap(img)
            main.mainwindow.lbl_preview.setPixmap(frame)
            return True
        else:
            main.mainwindow.lbl_preview.clear()
            return False
