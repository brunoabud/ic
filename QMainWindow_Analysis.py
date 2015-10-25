#coding: utf-8
from PyQt4 import QtCore, QtGui
from Ui_QMainWindow_Analysis import Ui_QMainWindow_Analysis 
from QWizard_NewAnalysis import QWizard_NewAnalysis

#Importa o módulo de Análise
#Ao importar este módulo, a inicialização da análise é feita automaticamente
import Analysis

class QMainWindow_Analysis(QtGui.QMainWindow):
	def __init__(self, parent = None):
		super(QtGui.QMainWindow, self).__init__(parent)

		#Inicializa a a interface gráfica da janela
		self.ui = Ui_QMainWindow_Analysis()
		self.ui.setupUi(self)

		#Chama a função que conecta os signals dos componentes da janela
		self.connectSignals()

	def connectSignals(self):
		self.ui.actn_newAnalysis.triggered.connect(self.actn_newAnalysis_triggered)
		self.ui.actn_exit.triggered.connect(self.actn_exit_triggered)
		self.ui.btn_previewPlayPause.clicked.connect(self.btn_previewPlayPause_clicked)
		self.ui.scrlbar_previewTime.valueChanged.connect(self.scrlbar_previewTime_valueChanged)
		self.ui.cb_acceleration.currentIndexChanged.connect(self.cb_acceleration_currentIndexChanged)
		self.ui.cb_velocity.currentIndexChanged.connect(self.cb_velocity_currentIndexChanged)
		self.ui.cb_position.currentIndexChanged.connect(self.cb_position_currentIndexChanged)


	def actn_exit_triggered(self, checked):
		if Analysis.initialized == True:
			buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel | QtGui.QMessageBox.No
			response = QtGui.QMessageBox.warning(self, u"Sair da análise", u"Você deseja salvara as alterações feitas nesta análise antes de sair?",
				buttons, QtGui.QMessageBox.Cancel)
			if response == QtGui.QMessageBox.No:
				self.close()
			elif response == QtGui.QMessageBox.Yes:
				saved = self.saveAnalysis()
				if saved:
					self.close()
		else:
			self.close()

	def saveAnalysis(self):
		return True

	def actn_newAnalysis_triggered(self, checked):	
		response = QWizard_NewAnalysis().exec_()
		if response == QtGui.QDialog.Accepted:
			#Iniciar análise
			Analysis.analyze(850, 150)
			self.ui.tbwg_Analysis.setEnabled(True)

			positions_count = Analysis.positions.shape[1]

			x_list = [x * (1.0/Analysis.fps) for x in range(Analysis.start_frame, Analysis.start_frame + positions_count)]

			y_list = [Analysis.positions[0][i] * Analysis.realPxRatio for i in range(0, positions_count)]

			self.ui.wdgt_plots.canvas.ax.plot(x_list, y_list, '.')
			self.ui.wdgt_plots.canvas.draw()

	def cb_position_currentIndexChanged(self, index):
		pass

	def cb_velocity_currentIndexChanged(self, index):
		pass

	def cb_acceleration_currentIndexChanged(self, index):
		pass

	def btn_previewPlayPause_clicked(self, checked):
		pass

	def scrlbar_previewTime_valueChanged(self, value):
		pass

	def updatePreviewImage(self):
		pass

