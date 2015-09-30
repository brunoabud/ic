#Bibliotecas utilizadas
from PyQt4 import QtGui, QtCore
import numpy as np
import cv2
import sys
import datetime
#Arquivos de interface grafica
import main_window 					#Janela Principal
#Modulo com as funcoes de processamento de video e deteccao de movimento
import Mov_track

class Events_main_window():
	def __init__(self, mainwindow_ui, mov_track):
		self.mainWindow = mainwindow_ui
		self.movTrack = mov_track
		#Conecta os eventos com as suas respectivas funcoes.
		self.connect_Events()

	#RadioButton rb_fromFile toggled(bool checked) Signal
	def rb_fromFile_toggled(self, checked):
		if checked == True:
			self.mainWindow.ledit_videoPath.setEnabled(True)			#Habilita a LineEdit com o caminho do arquivo de video
			self.mainWindow.btn_videoPath.setEnabled(True)				#Habilita o botao para procurar o arquivo de video

	#RadioButton rb_rb_fromCamera toggled(bool checked) Signal
	def rb_fromCamera_toggled(self, checked):
		if checked == True:
			self.mainWindow.ledit_videoPath.setEnabled(False)			#Desabilita a LineEdit com o caminho do arquivo de video
			self.mainWindow.btn_videoPath.setEnabled(False)				#Desabilita o botao para procurar o arquivo de video

	def btn_videoPath_clicked(self, checked):
		#Cria o dialogo de procura de arquivo
		selected = QtGui.QFileDialog.getOpenFileName(caption = "Selecione o video a ser analisado", filter = "Video Files(*.mov)")
		if not selected.isEmpty():
			self.mainWindow.ledit_videoPath.setText(selected)

	def btn_preview_clicked(self, checked):
		#Desabilita a caixa para impedir que o usuario clique mais de uma vez nos botoes
		self.mainWindow.gb_VideoInput.setEnabled(False)

		if self.mainWindow.rb_fromCamera.isChecked() == True:
			#Iniciar a pre-visualizacao da camera
			success = self.movTrack.startFromCamera()

			if success:
				#Habilita a caixa dos controles de visualizacao
				self.mainWindow.groupbox_previewControl.setEnabled(True)
				#Desabilita o scroll de tempo
				self.mainWindow.scrlbar_previewTime.setEnabled(False)
				#Desabilita o botao de pause
				self.mainWindow.btn_previewPlayPause.setEnabled(True)
				#Desabilita as abas de visualizacao e de analise
				self.mainWindow.tbwidget_views.setTabEnabled(1, False)
				self.mainWindow.tbwidget_views.setTabEnabled(2, False)
				self.mainWindow.tbwidget_views.setEnabled(True)
				self.mainWindow.gb_filtering.setEnabled(True)
				#Cria o timer que sera responsavel por atualizar a pre-visualizacao
				self.preview_Timer.start(25)
			else:
				#Se nao foi possivel iniciar a captura, reabilita a caixa para que o usuario possa tentar denovo.
				self.mainWindow.gb_VideoInput.setEnabled(True)
		else:
			success = self.movTrack.startFromFile(str(self.mainWindow.ledit_videoPath.text()))

			if not success:
				#Iniciar a pre-visualizacao do arquivo
				self.mainWindow.gb_VideoInput.setEnabled(True)
			else:
				#Habilita a caixa dos controles de visualizacao
				self.mainWindow.groupbox_previewControl.setEnabled(True)
				#Desabilita o scroll de tempo
				self.mainWindow.scrlbar_previewTime.setEnabled(True)
				#Desabilita o botao de pause
				self.mainWindow.btn_previewPlayPause.setEnabled(True)
				#Redimensiona a trackbar de tempo
				self.mainWindow.scrlbar_previewTime.setMaximum(self.movTrack.getTotalFrames())
				self.mainWindow.scrlbar_previewTime.setValue(0)
				#Desabilita as abas de visualizacao e de analise
				self.mainWindow.tbwidget_views.setTabEnabled(1, False)
				self.mainWindow.tbwidget_views.setTabEnabled(2, False)
				self.mainWindow.tbwidget_views.setEnabled(True)
				self.mainWindow.gb_filtering.setEnabled(True)
				#Cria o timer que sera responsavel por atualizar a pre-visualizaca
				self.preview_Timer.start(25)
			
	def btn_previewPlayPause_toggled(self, checked):
		if checked:
			#Usuario clicou no botao pausar
			self.mainWindow.btn_previewPlayPause.setText("Resumir")
			self.preview_Timer.stop()
		else:
			self.mainWindow.btn_previewPlayPause.setText("Pausar")
			self.preview_Timer.start(25)

	def scrlbar_previewTime_sliderPressed(self):
		self.preview_Timer.stop()

	def scrlbar_previewTime_sliderReleased(self):
		self.movTrack.setFramePos(self.mainWindow.scrlbar_previewTime.value())
		self.updatePreview()
		if not self.mainWindow.btn_previewPlayPause.isChecked():
			self.preview_Timer.start(25)
	def lstview_filters_clicked(self, item):
		self.mainWindow.scrlbar_filterValue.setValue(self.movTrack.getConfig(str(item.data().toString())))
	def scrlbar_filterValue_valueChanged(self, value):
		item = self.mainWindow.lstview_filters.currentIndex()
		self.movTrack.setConfig(str(item.data().toString()), value)
	#Funcao que ira conectar todos os slots que serao utilizados.
	def connect_Events(self):
		self.mainWindow.rb_fromFile.toggled.connect(self.rb_fromFile_toggled)
		self.mainWindow.rb_fromCamera.toggled.connect(self.rb_fromCamera_toggled)
		self.mainWindow.btn_videoPath.clicked.connect(self.btn_videoPath_clicked)
		self.mainWindow.btn_preview.clicked.connect(self.btn_preview_clicked)
		self.preview_Timer = QtCore.QTimer()
		self.preview_Timer.timeout.connect(self.updatePreview)
		self.mainWindow.btn_previewPlayPause.toggled.connect(self.btn_previewPlayPause_toggled)
		self.mainWindow.btn_previewPlayPause.setText("Pausar")
		self.mainWindow.scrlbar_previewTime.sliderPressed.connect(self.scrlbar_previewTime_sliderPressed)
		self.mainWindow.scrlbar_previewTime.sliderReleased.connect(self.scrlbar_previewTime_sliderReleased)
		self.mainWindow.lstview_filters.clicked.connect(self.lstview_filters_clicked)
		self.mainWindow.scrlbar_filterValue.valueChanged.connect(self.scrlbar_filterValue_valueChanged)

		model = QtGui.QStandardItemModel(self.mainWindow.lstview_filters)

		filters = ['blur_value', 'threshold_value','threshold_value_c', 'dilate_kernel', 'frame_skip']
		for filter_ in filters:
			item = QtGui.QStandardItem(filter_)
			model.appendRow(item)
		self.mainWindow.lstview_filters.setModel(model)

	def stopProcessing(self):
		self.movTrack.stop()

	def updatePreview(self):
		ret, frame = self.movTrack.processNextFrame()
		if ret:
			#Calcula o tamanho minimo do frame para que ele seja exibido corretamente na label
			geo = self.mainWindow.lbl_previewImage.geometry()
			width_lbl = geo.width()							
			height_lbl = geo.height()									
			ratio_lbl = float(width_lbl)/float(height_lbl)				#Proporcao da label

			width_size = frame.shape
			width_frame = width_size[1]									#Largura = numero de colunas
			height_frame = width_size[0]								#Altura = numero de linhas
			ratio_frame = float(width_frame)/float(height_frame)		#Proporcao do frame

			width_res = width_frame
			height_res = height_frame


			#Para se ter certeza de que tudo sera exibido corretamente, a menor dimensao da label deve ser
			#igual a maior dimensao do frame.
			#Eventualmente atualizo estas rotinas para que o frame se ajuste com a maior dimensao possivel dentro da label
			#Este codigo e somente para se ter certeza que o tamanho e possivel de ser exibido na label, mas na maioria das vezes
			#vai "sobrar" espaco util.

			if ratio_lbl > 1:
				#Menor dimensao e altura.
				min_dim_lbl = height_lbl
				dim_lbl_type = 'height'
			else:
				#Menor dimensao e largura.
				min_dim_lbl = width_lbl
				dim_lbl_type = 'width'	

			if ratio_frame > 1:
				#Maior dimensao e largura
				max_frame_dim = 'width'
			else:
				#Maior dimensao e altura
				max_frame_dim = 'height'

			width_res, height_res = self.recalculateSize(min_dim_lbl, max_frame_dim, ratio_frame)


			resized = cv2.resize(frame, (int(width_res), int(height_res)))
			cvRGBImg = cv2.cvtColor(resized, cv2.cv.CV_BGR2RGB)
			qimg = QtGui.QImage(cvRGBImg.data,cvRGBImg.shape[1], cvRGBImg.shape[0], QtGui.QImage.Format_RGB888)
			qpm = QtGui.QPixmap.fromImage(qimg)
			self.mainWindow.lbl_previewImage.setPixmap(qpm)
			#Atualiza a trackbar de frames se ela estiver ativa
			if self.mainWindow.scrlbar_previewTime.isEnabled():
				self.mainWindow.scrlbar_previewTime.setValue(self.movTrack.getFramePos())
			#Atualiza a label de tempo
			frames_pos = str(self.movTrack.getFramePos()) + '|' + str(int(self.movTrack.getTotalFrames()))

			self.mainWindow.lbl_previewTime.setText(frames_pos)
	def recalculateSize(self, size, size_type = 'width', width_over_height = 1.0):
		if 'width' in size_type:
			return size, size / width_over_height
		elif 'height' in size_type:
			return size, size * width_over_height
		else:
			return -1, -1
