#coding: utf-8
from PyQt4 import QtGui, QtCore
import os

class QWizardPage_VideoInput(QtGui.QWizardPage):
	def __init__(self, parent = None):
		super(QtGui.QWizardPage, self).__init__(parent)

		#Inicializa a interface gráfica da classe QWizard Pai
		#Apesar da página ter sido criada agora, ela ainda não foi adiciona ao QWizard portanto
		#não é possível obter uma referência para a UI ainda.
		self.wiz_ui = None

	def initializePage(self):
		#Verifica se a referência para a interface gráfica do QWizard já foi criada
		if self.wiz_ui is None:
			if self.wizard() is not None:
				self.wiz_ui = self.wizard().ui
				self.connectSignals()
			else:
				return False		

	def isComplete(self):
		if self.wiz_ui is None:
			return False

		#Verifica se a opção arquivo está escolhida
		#****A a opção camera ainda não está implementada!!!!
		if not self.wiz_ui.rb_fromFile.isChecked():
			return False
		else:
			file_path = self.wiz_ui.ledit_videoPath.text()
			if os.path.isfile(file_path):
				return True
			else:
				return False

		return True


	def connectSignals(self):
		self.wiz_ui.rb_fromFile.toggled.connect(self.rb_fromFile_toggled)
		self.wiz_ui.pb_searchFile.clicked.connect(self.pb_searchFile_clicked)
		self.wiz_ui.ledit_videoPath.textChanged.connect(self.ledit_videoPath_textChanged)

	def pb_searchFile_clicked(self, checked):
		file_path = QtGui.QFileDialog.getOpenFileName(self, u"Selecione o arquivo de vídeo", '', u"Arquivos de Vídeo (*.mov *.avi *.mpg *.mpeg *.wmv *.mkv *.3gp)")
		self.wiz_ui.ledit_videoPath.setText(file_path)
		self.completeChanged.emit()


	def connectSignals(self):
		self.wiz_ui.rb_fromFile.toggled.connect(self.rb_fromFile_toggled)
		self.wiz_ui.pb_searchFile.clicked.connect(self.pb_searchFile_clicked)
		self.wiz_ui.ledit_videoPath.textChanged.connect(self.ledit_videoPath_textChanged)

	def rb_fromFile_toggled(self, checked):
		self.completeChanged.emit()

	def ledit_videoPath_textChanged(self, text):
		self.completeChanged.emit()