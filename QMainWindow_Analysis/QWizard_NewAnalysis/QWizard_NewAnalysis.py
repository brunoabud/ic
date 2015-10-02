#coding: utf-8
from PyQt4 import QtCore, QtGui
from Ui_QWizard_NewAnalysis import Ui_QWizard_NewAnalysis

class QWizard_NewAnalysis(QtGui.QWizard):
	def __init__(self, parent = None):
		super(QtGui.QWizard, self).__init__(parent)
		
		#Cria a classe que inicializa os componentes da interface gráfica
		self.ui = Ui_QWizard_NewAnalysis()
		self.ui.setupUi(self)