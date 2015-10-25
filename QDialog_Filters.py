#coding: utf-8

from PyQt4 import QtGui, QtCore
import Ui_QDialog_Filters

class QDialog_Filters(QtGui.QDialog):
	def __init__(self, parent = None):
		super(QtGui.QDialog, self).__init__(parent)
		self.ui = Ui_QDialog_Filters.Ui_QDialog_Filters()
		self.ui.setupUi(self)
		self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).clicked.connect(self.accept)
		self.ui.buttonBox.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.reject)

	def isComplete(self):
		return True

