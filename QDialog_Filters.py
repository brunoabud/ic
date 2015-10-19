#coding: utf-8

from PyQt4 import QtGui, QtCore
import Ui_QDialog_Filters

class QDialog_Filters(QtGui.QDialog):
	def __init__(self, parent = None):
		super(QtGui.QDialog, self).__init__(parent)
		self.ui = Ui_QDialog_Filters.Ui_QDialog_Filters()
		self.ui.setupUi(self)
		self.d = {}

		self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).clicked.connect(self.accept)
		self.ui.buttonBox.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.reject)

		self.ui.buttonBox.addButton(u"Valores Padrões", QtGui.QDialogButtonBox.ResetRole).clicked.connect(self.defaultValues)


	
	def defaultValues(self):

		self.ui.sldr_preBlur.setValue(3)

		self.ui.sldr_postBlur.setValue(3)

		self.ui.sldr_preThreshold.setValue(13 )
		self.ui.sldr_threshC.setValue(8)

		self.ui.sldr_frameSkip.setValue(0)

		self.ui.sldr_dilateKernelSize.setValue(4)


	def loadFilterValues(self):
		with open('filter_values.txt', 'r') as f:
			for line in f:
				(key, value) = line.split()
				self.d[key] = int(value)

		self.ui.sldr_preBlur.setValue(self.d['preBlur'])
		self.ui.sldr_postBlur.setValue(self.d['postBlur'])
		self.ui.sldr_preThreshold.setValue(self.d['preThreshold'])
		self.ui.sldr_threshC.setValue(self.d['threshC'])
		self.ui.sldr_frameSkip.setValue(self.d['frameSkip'])
		self.ui.sldr_dilateKernelSize.setValue(self.d['dilateKernelSize'])

	def saveFilterValues(self):
		self.d['preBlur'] = self.ui.sldr_preBlur.value()
		self.d['postBlur'] = self.ui.sldr_postBlur.value()
		self.d['preThreshold'] =self.ui.sldr_preThreshold.value()
		self.d['threshC'] = self.ui.sldr_threshC.value()
		self.d['frameSkip'] = self.ui.sldr_frameSkip.value()
		self.d['dilateKernelSize'] = self.ui.sldr_dilateKernelSize.value()

		with open('filter_values.txt', 'w') as f:
			for pair in self.d.items():
				(key, value) = pair
				f.write(str(key) + ' ' + str(value) + '\n')

	def getFilters(self):
		self.loadFilterValues()

		self.exec_()

		if self.result() == QtGui.QDialog.Accepted:
			self.saveFilterValues()
			return self.d
		else:
			return None

