from PyQt4 import QtGui, QtCore

class ResizablePixmapLabel(QtGui.QLabel):
    def __init__(self, *args, **kwargs):
        super(ResizablePixmapLabel, self).__init__(*args, **kwargs)
        self._pixmap = QtGui.QPixmap()
        self.setMinimumSize(1, 1)

    def setPixmap(self, pix):
        if pix is None:
            self._pixmap = QtGui.QPixmap(640, 480)
            self._pixmap.fill(QtGui.QColor(0, 0, 0, 0))
        else:
            self._pixmap = pix
        self._fitPixmap()

    def ratio(self):
        if self._pixmap.isNull(): return 0
        return self._pixmap.height() / float(self._pixmap.width())

    def sizeHint(self):
        if self._pixmap.isNull(): return QtCore.QSize(0, 0)
        w = self.width();
        return QtCore.QSize(w, self.ratio() * w);

    def _fitPixmap(self):
        if not self._pixmap.isNull():
            super(ResizablePixmapLabel, self).setPixmap(self._pixmap.scaled(self.size(),
                                 QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
    def resizeEvent(self, event):
        self._fitPixmap()
