#coding: latin-1
from PyQt4 import QtCore, QtGui
from Ui_QMainWindow_Analysis import Ui_QMainWindow_Analysis
from QWizard_NewAnalysis import QWizard_NewAnalysis

class QMainWindow_Analysis(QtGui.QMainWindow):
	def __init__(self, parent = None):
		super(QtGui.QMainWindow, self).__init__(parent)

		#Cria a classe que inicializa os componentes da interface gráfica
		self.ui = Ui_QMainWindow_Analysis()
		self.ui.setupUi(self)

		#Chama a função que iŕa conectar as actions da janela
		self.connectActions()

	#Opção Nova Análise do Menu
	def actn_newAnalysis_triggered(self, checked):
		wizard_newAnalysis = QWizard_NewAnalysis.QWizard_NewAnalysis(self)
		wizard_newAnalysis.show()

	def connectActions(self):
		self.ui.actn_newAnalysis.triggered.connect(self.actn_newAnalysis_triggered)
