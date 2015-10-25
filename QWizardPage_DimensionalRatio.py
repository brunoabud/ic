#coding: utf-8

import QGraphicsView_LineMarker
import unicodedata
import QDialog_Filters
import math
from PyQt4 import QtCore, QtGui
import Analysis
import codecs
import cv2
import numpy as np

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        unicodedata.numeric(s)
        return True
        
    except (TypeError, ValueError):
        pass
 	return False


	

class QWizardPage_DimensionalRatio(QtGui.QWizardPage):
	def __init__(self, parent = None):
		super(QtGui.QWizardPage, self).__init__(parent)
		self.wiz_ui = None

	def createFilterSlider(self, filter_title, filter_name, min_value, max_value, value):
		slider = QtGui.QSlider(QtCore.Qt.Horizontal)
		slider.setObjectName(str(filter_name))
		lblTitle = QtGui.QLabel(filter_title)
		lblValue = QtGui.QLabel(str(value))
		slider.setMinimum(int(min_value))
		slider.setMaximum(int(max_value))
		slider.setValue(int(value))

		frame = QtGui.QWidget()
		layout = QtGui.QGridLayout()

		slider.valueChanged.connect(lblValue.setNum)

		layout.addWidget(lblTitle, 0, 0)
		layout.addWidget(lblValue, 0, 1)
		layout.addWidget(slider, 1, 0, 1, -1)

		frame.setLayout(layout)

		frame.setMaximumSize(99999, 75)
		return frame

	def initializePage(self):
		#Verifica se a referência para a interface gráfica do QWizard já foi criada
		if self.wiz_ui is None:
			if self.wizard() is not None:
				self.wiz_ui = self.wizard().ui
				self.connectSignals()

				Analysis.open_input_fromFile(str(self.wiz_ui.ledit_videoPath.text()))

				v_width, v_height = Analysis.getVideoDimensions()


				self.wiz_ui.spbox_posX.setMinimum(0)
				self.wiz_ui.spbox_posX.setMaximum(v_width)

				self.wiz_ui.spbox_posY.setMinimum(0)
				self.wiz_ui.spbox_posY.setMaximum(v_height)

				self.wiz_ui.spbox_rotAng.setMinimum(-180)
				self.wiz_ui.spbox_rotAng.setMaximum(180)

				self.updatePreview()
				self.wiz_ui.tckbar_frame.setMaximum(Analysis.get_cap_totalFrames())
				self.wiz_ui.tckbar_frame.setValue(Analysis.get_cap_framePos())

				import codecs
				self.wiz_ui.filter_sliders = []

				#Carrega os filtros
				with codecs.open('filter_values.txt', mode = 'r', encoding='utf-8') as f:
					for line in f:
						if line.startswith('#'):
							continue
						filter_args = line.split('\t')
						if (len(filter_args) != 6):
							continue
						Analysis.addFilterParams(filter_args[0], filter_args[1], filter_args[2], filter_args[3], filter_args[4], filter_args[5])
			else:
				return False	


	def pb_editFilters_clicked(self, checked):
		self.filter_dialog = QDialog_Filters.QDialog_Filters()
		

		self.filter_dialog.ui.wdgt_filters = QtGui.QWidget(self.filter_dialog)
		self.filter_dialog.ui.wdgt_filters.setObjectName('wdgt_filters')

		layout = QtGui.QGridLayout(self.filter_dialog.ui.wdgt_filters)

		r = 0
		c = 0
		self.filter_sliders = []

		for item in Analysis.filter_params.items():
			(filter_name, filter_params) = item

			frame_slider = self.createFilterSlider(filter_params['filter_title'], filter_name,
				filter_params['min_value'], filter_params['max_value'], filter_params['value'])
			
			self.filter_sliders.append(frame_slider.findChild(QtGui.QSlider, filter_name))

			layout.addWidget(frame_slider, r, c)
			c += 1
			if c >= 3:
				c = 0
				r += 1

		self.filter_dialog.ui.scrlA_filters.setWidget(self.filter_dialog.ui.wdgt_filters)
		self.filter_dialog.ui.buttonBox.addButton(u"Valores Padrões", QtGui.QDialogButtonBox.ResetRole).clicked.connect(self.defaultFilterValues)

		response = self.filter_dialog.exec_()
		if response == QtGui.QDialog.Accepted:
			for slider in self.filter_sliders:
				Analysis.changeFilterParams(str(slider.objectName()), 'value', int(slider.value()))

		del self.filter_sliders

	def defaultFilterValues(self):
		for slider in self.filter_sliders:
			filter_name = str(slider.objectName())

			slider.setValue(int(Analysis.getFilterParam(filter_name, 'default_value')))

	def pb_saveFilters_clicked(self, checked):
		response = QtGui.QMessageBox.question(self, u'Sobreescrever arquivo de filtros', u"Você gostaria de salvar os parâmetros de filtro?" +
			u" O arquivo atual será perdido e todos os comentários feitos nele também. Se você deseja "+
			u"alterar os valores sem perder os comentários, recomenda-se "+
			u" a alteração dos valores diretamente no arquivo.", QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)

		if response == QtGui.QMessageBox.Yes:
			with codecs.open('filter_values.txt', mode = 'w', encoding='utf-8') as f:
				for item in Analysis.filter_params.items():
					(filter_name, filter_params) = item
					f.write(filter_params['filter_title'] + '\t' + str(filter_name) + '\t' + str(filter_params['min_value']) + '\t' +
					str(filter_params['max_value']) + '\t' + str(filter_params['value']) + '\t' + str(filter_params['default_value']) + '\n')


	def isComplete(self):
		if not is_number(self.wiz_ui.le_realLength.text()):
			return False

		if self.wiz_ui.lbl_lineLength.text() == '0':
			return False

		if not self.isEnabled():
			return False

		return True

	def cleanUpPage(self):
		Analysis.closeInput()

	def connectSignals(self):
		self.wiz_ui.tckbar_frame.valueChanged.connect(self.tckbar_frame_valueChanged)
		self.wiz_ui.tckbar_frame.sliderReleased.connect(self.tckbar_frame_sliderReleased)
		self.wiz_ui.tckbar_frame.sliderMoved.connect(self.tckbar_frame_sliderMoved)

		self.wiz_ui.lbl_color.colorChanged.connect(self.lbl_color_colorChanged)

		self.wiz_ui.tckbar_frame.setTracking(False)

		self.wiz_ui.pb_editFilters.clicked.connect(self.pb_editFilters_clicked)
		self.wiz_ui.pb_saveFilters.clicked.connect(self.pb_saveFilters_clicked)

		self.wiz_ui.le_realLength.textChanged.connect(self.le_realLength_textChanged)
		self.wiz_ui.gv_lineMarker.lineChanged.connect(self.gv_lineMarker_lineChanged)

		palette = self.wiz_ui.le_realLength.palette()
		palette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))

		self.wiz_ui.spbox_posX.valueChanged.connect(self.updateCoordinates)
		self.wiz_ui.spbox_posY.valueChanged.connect(self.updateCoordinates)
		self.wiz_ui.spbox_rotAng.valueChanged.connect(self.updateCoordinates)
		self.wiz_ui.cb_showCoordsSystem.clicked.connect(self.updateCoordinates)

		self.wiz_ui.le_realLength.setPalette(palette)

	def gv_lineMarker_lineChanged(self, value):
		self.wiz_ui.lbl_lineLength.setText(str(  math.ceil(value)  ))
		if(self.wiz_ui.gv_lineMarker.getLineLength()) != 0 and is_number(self.wiz_ui.le_realLength.text()):
			Analysis.realPxRatio = (0.001 * float(self.wiz_ui.le_realLength.text())) / float(self.wiz_ui.gv_lineMarker.getLineLength())

		self.completeChanged.emit()

	def lbl_color_colorChanged(self, color):
		self.wiz_ui.gv_lineMarker.setLineColor(color.red(), color.green(), color.blue())

	def le_realLength_textChanged(self, text):
		if is_number(text):
			palette = self.wiz_ui.le_realLength.palette()
			palette.setColor(QtGui.QPalette.Base, QtGui.QColor(0, 255, 0))
			self.wiz_ui.le_realLength.setPalette(palette)

			if(self.wiz_ui.gv_lineMarker.getLineLength()) != 0 and is_number(self.wiz_ui.le_realLength.text()):
				Analysis.realPxRatio = (0.001 * float(self.wiz_ui.le_realLength.text())) / float(self.wiz_ui.gv_lineMarker.getLineLength())
		else:
			palette = self.wiz_ui.le_realLength.palette()
			palette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
			self.wiz_ui.le_realLength.setPalette(palette)
		self.completeChanged.emit()



	def tckbar_frame_valueChanged(self, value):
		self.wiz_ui.lbl_frame.setText(str(self.wiz_ui.tckbar_frame.value()) + '/' + str(self.wiz_ui.tckbar_frame.maximum()))
		Analysis.set_cap_framePos(self.wiz_ui.tckbar_frame.value())
		self.updatePreview()

	def tckbar_frame_sliderReleased(self):
		Analysis.set_cap_framePos(self.wiz_ui.tckbar_frame.value())
		self.updatePreview()

	def tckbar_frame_sliderMoved(self, value):
		self.wiz_ui.lbl_frame.setText(str(value) + '/' + str(self.wiz_ui.tckbar_frame.maximum()))

	def __del__(self):
		pass

	def updateCoordinates(self, ignoredParameter):
		Analysis.coordsSystemPos = (int(self.wiz_ui.spbox_posX.value()), int(self.wiz_ui.spbox_posY.value()))
		Analysis.coordsSystemAngle = int(self.wiz_ui.spbox_rotAng.value())
		
		self.updatePreview(False)

	def updatePreview(self, goto_next_frame = True):
		if not goto_next_frame:
			ret, img = Analysis.getCurrentFrame()
		else:
			ret, img = Analysis.getNextFrame()

		if not ret:
			return

		frame = np.copy(img)

		if self.wiz_ui.cb_showCoordsSystem.isChecked():
			#Posição e rotação da origem do sistema
			ox, oy = int(self.wiz_ui.spbox_posX.value()), int(self.wiz_ui.spbox_posY.value())
			rotAng = math.radians(int(self.wiz_ui.spbox_rotAng.value()))
			
			#Vetores unitários com a direção dos eixos x e y (positivo na direita e abaixo)
			line_length = 100	

			p1_x = int(ox)
			p1_y = int(oy)
			p2_x = ox + int(math.cos(rotAng) * line_length)
			p2_y = oy + int(math.sin(rotAng) * line_length)		

			cv2.line(frame, (p1_x, p1_y), (p2_x, p2_y), (0, 255, 0))

			font = cv2.FONT_HERSHEY_SIMPLEX
			cv2.putText(frame,'+x', (p2_x, p2_y), font, 0.4,(0,255,0),1)

			p2_x = ox + int(math.cos(rotAng + math.radians(90.0)) * line_length)
			p2_y = oy + int(math.sin(rotAng + math.radians(90.0)) * line_length)		

			cv2.line(frame, (p1_x, p1_y), (p2_x, p2_y), (0, 0, 255))

			cv2.putText(frame,'+y', (p2_x, p2_y), font, 0.4,(0,0, 255),1)

			cv2.circle(frame, (ox, oy), 1, (255, 0, 0), -1)

		qimg = self.wiz_ui.gv_lineMarker.cv2ImgToQImage(frame)
		self.wiz_ui.gv_lineMarker.updatePreviewImage(qimg)


		def validatePage(self):

			return True