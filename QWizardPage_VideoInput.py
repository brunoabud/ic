#coding: utf-8
from PyQt4 import QtGui, QtCore
import os

class QWizardPage_VideoInput(QtGui.QWizardPage):
	def __init__(self, parent = None):
		super(QtGui.QWizardPage, self).__init__(parent)

		self.has_wiz_add_me = False									#Neste ponto os componentes provavelmente não foram inseridos
																	#na classe de UI. E a página, apesar de ter sido criada, ainda não
																	#foi adicionada ao Wizard.

	def initializePage(self):
		if not self.has_wiz_add_me:
			if self.wizard() is not None:
				self.wiz_ui = self.wizard().ui
				self.has_wiz_add_me = True
				self.connectSignals()
			else:
				return
				
	def isComplete(self):
		if not self.has_wiz_add_me:
			return False

		if not self.wiz_ui.rb_fromFile.isChecked():
			return True
		else:
			file_path = self.wiz_ui.ledit_videoPath.text()
			if os.path.isfile(file_path):
				return True
			else:
				return False

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


