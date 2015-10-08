from PyQt4 import QtCore, QtGui


class QLabel_Color(QtGui.QLabel):
	def __init__(self, parent = None):
		super(QtGui.QWidget, self).__init__(parent)


	def mouseDoubleClickEvent(self, event):
		if event.buttons() & QtCore.Qt.LeftButton == QtCore.Qt.LeftButton:
			r = self.parent().findChild(QtGui.QSlider, 'sldr_Red').value()
			g = self.parent().findChild(QtGui.QSlider,'sldr_Green').value()
			b = self.parent().findChild(QtGui.QSlider,'sldr_Blue').value()

			color = QtGui.QColorDialog.getColor(QtGui.QColor(r, g, b))

			if color.isValid():
				self.parent().findChild(QtGui.QSlider, 'sldr_Red').setValue(color.red())
				self.parent().findChild(QtGui.QSlider, 'sldr_Green').setValue(color.green())
				self.parent().findChild(QtGui.QSlider, 'sldr_Blue').setValue(color.blue())