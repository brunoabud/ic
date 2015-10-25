from PyQt4 import QtCore, QtGui


class QLabel_Color(QtGui.QLabel):

	colorChanged = QtCore.pyqtSignal(QtGui.QColor)

	def __init__(self, parent = None):
		super(QtGui.QWidget, self).__init__(parent)
		self.setColor(QtGui.QColor(0, 0, 0))

	def setColor(self, color):
		self.color = color
		pix = QtGui.QPixmap(32, 32)
		pix.fill(self.color)
		self.setPixmap(pix)

		self.colorChanged.emit(self.color)
		
	def getColor(self):
		return self.color

	def mouseDoubleClickEvent(self, event):
		if event.buttons() & QtCore.Qt.LeftButton == QtCore.Qt.LeftButton:

			color = QtGui.QColorDialog.getColor(self.color, self,
		u"Selecione a cor da linha")

			if color.isValid():
				self.setColor(color)