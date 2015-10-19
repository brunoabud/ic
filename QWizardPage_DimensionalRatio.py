#coding: utf-8
from PyQt4 import QtGui, QtCore
from MovAnalysis import Mov_track
import QGraphicsView_LineMarker
import unicodedata
import QDialog_Filters
import math
from MovAnalysis import Analysis

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
		self.movTrack = Mov_track.Mov_track()
		self.preview_timer = QtCore.QTimer()
		self.preview_timer.timeout.connect(self.updatePreview)

		self.has_wiz_add_me = False									#Neste ponto os componentes provavelmente não foram inseridos
																	#na classe de UI. E a página, apesar de ter sido criada, ainda não
																	#foi adicionada ao Wizard.
		
	def updatePreview(self):
		ret, img = self.movTrack.getNextFrame()
		if not ret:
			return
		qimg = self.wiz_ui.gv_lineMarker.cv2ImgToQImage(img)
		self.wiz_ui.gv_lineMarker.updatePreviewImage(qimg)
				
	def isComplete(self):
		if not self.has_wiz_add_me:
			return False

		if self.wiz_ui.lbl_lineLength.text() == '0':
			return False

		if not is_number(self.wiz_ui.le_realLength.text()):
			return False

		return True

	def initializePage(self):
		if not self.has_wiz_add_me:
			if self.wizard() is not None:
				self.wiz_ui = self.wizard().ui
				self.has_wiz_add_me = True
				self.connectSignals()
			else:
				return

		if not self.wiz_ui.rb_fromFile.isChecked():
			ret = self.movTrack.startFromCamera()
			if not ret:
				QtGui.QMessageBox.critical(self, u"Erro ao inicializar a captura da câmera", u"Houve um erro"+
				 u"ao tentar inicializar a captura pela câmera. Verifique se sua câmera está conectada e funcionando corretamente.")
				self.wizard().back()
			else:
				if not self.wiz_ui.pb_holdFrame.isChecked():
					self.preview_timer.start(65)
					self.wiz_ui.pb_holdFrame.setVisible(True)
					self.wiz_ui.tckbar_frame.setVisible(False)
		else:
			ret = self.movTrack.startFromFile(str(self.wiz_ui.ledit_videoPath.text()))
			if not ret:
				QtGui.QMessageBox.critical(self, u"Erro ao carregar arquivo", u"Houve um problema ao tentar carregar o arquivo de vídeo."+
				u" Verifique se o arquivo realmente é um arquivo de vídeo e se o mesmo não está corrompido. O problema também pode ter sido causado"+
				u"pela ausência ou má instalação do FFmpeg.")
				self.wizard().back()
			else:
				self.wiz_ui.pb_holdFrame.setVisible(False)
				self.wiz_ui.tckbar_frame.setVisible(True)

				self.updatePreview()
				self.wiz_ui.tckbar_frame.setValue(self.movTrack.getFramePos())
				self.wiz_ui.tckbar_frame.setMaximum(self.movTrack.getTotalFrames())

	def pb_filters_clicked(self, checked):
		dialog = QDialog_Filters.QDialog_Filters(self)
		dialog.getFilters()

	def connectSignals(self):
		self.wiz_ui.pb_holdFrame.toggled.connect(self.pb_holdFrame_toggled)
		self.wiz_ui.tckbar_frame.valueChanged.connect(self.tckbar_frame_valueChanged)
		self.wiz_ui.tckbar_frame.setTracking(False)
		self.wiz_ui.sldr_Red.valueChanged.connect(self.lineColorChanged)
		self.wiz_ui.sldr_Green.valueChanged.connect(self.lineColorChanged)
		self.wiz_ui.sldr_Blue.valueChanged.connect(self.lineColorChanged)
		self.wiz_ui.le_realLength.textChanged.connect(self.le_realLength_textChanged)
		self.wiz_ui.pb_filters.clicked.connect(self.pb_filters_clicked)
		self.wiz_ui.gv_lineMarker.lineChanged.connect(self.gv_lineMarker_lineChanged)
		palette = self.wiz_ui.le_realLength.palette()
		palette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))

		self.wiz_ui.le_realLength.setPalette(palette)
		pix = QtGui.QPixmap(32, 32)
		pix.fill(QtGui.QColor(0, 0, 0))
		self.wiz_ui.lblColor.setPixmap(pix)

		self.wiz_ui.lblColor.setAlignment(QtCore.Qt.AlignHCenter)

	def gv_lineMarker_lineChanged(self, value):
		self.wiz_ui.lbl_lineLength.setText(str(  math.ceil(value)  ))
		self.completeChanged.emit()

	def le_realLength_textChanged(self, text):
		if is_number(text):
			palette = self.wiz_ui.le_realLength.palette()
			palette.setColor(QtGui.QPalette.Base, QtGui.QColor(0, 255, 0))
			self.wiz_ui.le_realLength.setPalette(palette)
		else:
			palette = self.wiz_ui.le_realLength.palette()
			palette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 0, 0))
			self.wiz_ui.le_realLength.setPalette(palette)
		self.completeChanged.emit()

	def chooseLineColor(self, checked):
		color = QtGui.QColorDialog.getColor(QtGui.QColor(self.wiz_ui.sldr_R.value(), self.wiz_ui.sldr_G.value(), self.wiz_ui.sldr_B.value()), self,
		u"Selecione a cor da linha")

		if color.isValid():
			self.wiz_ui.gv_lineMarker.setLineColor(color.red(), color.green(), color.blue())
			self.wiz_ui.sldr_R.setValue(color.red())
			self.wiz_ui.sldr_G.setValue(color.green())
			self.wiz_ui.sldr_B.setValue(color.blue())

	def lineColorChanged(self, value):
		self.wiz_ui.gv_lineMarker.setLineColor(self.wiz_ui.sldr_Red.value(), self.wiz_ui.sldr_Green.value(), self.wiz_ui.sldr_Blue.value())
		pix = QtGui.QPixmap(32, 32)
		pix.fill(QtGui.QColor(self.wiz_ui.sldr_Red.value(), self.wiz_ui.sldr_Green.value(), self.wiz_ui.sldr_Blue.value()))
		self.wiz_ui.lblColor.setPixmap(pix)

	def tckbar_frame_valueChanged(self, value):
		self.movTrack.setFramePos(value)
		self.updatePreview()

	def pb_holdFrame_toggled(self, checked):
		if checked:
			self.preview_timer.stop()
		else:
			self.preview_timer.start(65)

	def validatePage(self):
		self.analysis = Analysis.Analysis(self.movTrack)
		self.analysis.analyze()
		self.movTrack.stop()
		print 'analisado' 
		return True

	def cleanupPage(self):
		self.movTrack.stop()
		self.wiz_ui.gv_lineMarker.resetView()

	def __del__(self):
		pass