# -*- coding: latin-1 -*-

from PyQt4 import QtCore, QtGui
from matplotlib.patches import Rectangle
import cv2
import math


class QGraphicsView_LineMarker(QtGui.QGraphicsView):

	lineChanged = QtCore.pyqtSignal(float)

	def __init__(self, parent):
		super(QtGui.QGraphicsView, self).__init__(parent)
		self.createScene()

	def createScene(self):
		#Variáveis de Controle
		self.zoom = 1.0												#Zoom da visualização
		self.drawing = False										#Usuário está desenhando a linha?
		self.zooming = False										#Usuário está desenhando a caixa de zoom?

		scene = QtGui.QGraphicsScene()								#Cria uma cena para o objeto QGraphicsView

		pixmap = QtGui.QPixmap()									#Cria uma pixmap que irá conter a visualização do vídeo

		self.zoom_p0 = QtCore.QPoint(0, 0)							#Ponto 0(esquerda superior) da caixa de zoom
		self.zoom_p1 = QtCore.QPoint(0, 0)							#Ponto 1(direita inferior)  da caixa de zoom

		self.line_p0 = QtCore.QPoint(0, 0)							#Ponto 0(esquerda superior) da linha
		self.line_p1 = QtCore.QPoint(0, 0)							#Ponto 1(direita inferior)  da linha

		self.pixmap_preview = scene.addPixmap(pixmap)				#Adiciona a pixmap na cena

		self.zoomRect = scene.addRect(0, 0, 0, 0)					#Adiciona o retângulo que iŕa desenhar a caixa de zoom na cena
		self.line = scene.addLine(0, 0, 0, 0)						#Adiciona a linha que irá ser desenhada pelo usuário na cena

		self.line_pen = QtGui.QPen()								#Cria uma pen para ser utilizada no desenho da linha
		self.line_pen.setWidthF(0.5)								#Muda a largura da linha para 0.5
		self.line.setPen(self.line_pen)								#Define a pen da linha

		self.line.setVisible(False)									#Esconde a linha
		self.zoomRect.setVisible(False)								#Esconde o retângulo		
		
		self.setScene(scene)										#Muda a cena para a que foi criada
		self.default_scene = scene
		self.mouse_delta = 0.0										#Variavel usada para calcular o movimento da roda do mouse

		self.resetView()
	#Evento do scroll do Mouse
	def wheelEvent(self, event):
		#O delta da maioria dos mouses é 15 oitavos de grau. Porém existem mouses mais sensíveis com valores menores do que 15 oitavos.
		#Para evitar problemas com cálculos, estipula-se como padrão os 15 oitavos de grau. Portanto, se um delta menor que 15 for fornecido,
		#ele será acumulado na variável mouse_delta até atingir o valor 15. (via OpenCV Doc.)
		self.mouse_delta += event.delta()

		if math.fabs(self.mouse_delta) >= 15.0:
			delta = 15.0 * math.floor(self.mouse_delta / 15.0)		#Encontra o menor múltiplo de 15 contido no acumulador

			self.zoom += (delta / 8.0) / 100.0						#Um valor razoável para a variação de zoom é 0.018 
																	#para cada 15 oitavos de grau. [(15.0 / 8.0) / 100.0 = +- 0.018]
			self.mouse_delta -= delta 								#Subtrai o delta do acumulador

		#Para evitar comportamentos estranhos, o zoom deve sempre ser maior que 0
		if self.zoom <= 0.0:
			self.zoom = 0.018

		self.resetMatrix()											#Limpa a matriz de transformação
		self.scale(self.zoom, self.zoom)							#Aplica o zoom na matriz

		self.show()													#Força a atualização da tela

	def mousePressEvent(self, event):
		if event.button() == QtCore.Qt.RightButton and not self.drawing:
			self.zooming = True

			self.zoom_p0 = self.mapToScene(QtCore.QPoint(event.x(), event.y()))
			

		if event.button() == QtCore.Qt.LeftButton and not self.zooming:
			self.drawing = True

			self.line_p0 = self.mapToScene(QtCore.QPoint(event.x(), event.y()))

		if event.button() == QtCore.Qt.MidButton:
			self.fitInView(self.pixmap_preview, QtCore.Qt.KeepAspectRatio)
			self.getZoomFromMatrix()
			self.update()


	#Calcula qual é o zoom aplicado na matriz transformação atual
	def getZoomFromMatrix(self):
		point = QtCore.QPointF(1.0, 0.0)				
		zommed_point = self.matrix().map(point)
		self.zoom = zommed_point.x()

	def mouseReleaseEvent(self, event):
		if event.button() == QtCore.Qt.RightButton and self.zooming:
			self.fitInView(self.zoomRect.rect(), 
				QtCore.Qt.KeepAspectRatio)							#Esta função centraliza o retângulo fornecido na tela
																	#e altera a matriz de transformação a fim de mudar o zoom
																	#para ajustar o retângulo o mais justo possível na visualização

			#Para manter a variável de controle de zoom atualizada deve-se, através da matriz transformação, calcular qual foi
			#o zoom aplicado pela função fitInView. Para fazer tal, basta criar um ponto com um valor x de 1 e aplicar a transformação.
			#A nova posição x do ponto será então o valor do zoom.

			#Obtem o zoom atual e atualiza a variavel self.zoom
			self.getZoomFromMatrix()

			self.zoomRect.setVisible(False)							#Esconde o retângulo
			self.zooming = False

		if event.button() == QtCore.Qt.LeftButton and self.drawing:
			self.drawing = False
			self.lineChanged.emit(self.getLineLength())

	def mouseMoveEvent(self, event):		
		if self.zooming == True:
			self.zoom_p1.setX(event.x())
			self.zoom_p1.setY(event.y())

			p0 = QtCore.QPointF(self.zoom_p0)						#Transforma as coordenadas de viewport para coordenadas de Cena.
			p1 = self.mapToScene(self.zoom_p1)						#as coordenadas são bem diferentes pois o objeto QGraphicsView aplica 
																	#varías transformações para centralizar, escalar, rotacionar etc a 
																	#cena na visualização.
																	
			if p0.x() > p1.x():										#Certifica-se de que as coordenadas do ponto 1 são maiores
				x = p0.x()											#que as coordenadas do ponto 0
				p0.setX(p1.x())
				p1.setX(x)

			if p0.y() > p1.y():
				y = p0.y()
				p0.setY(p1.y())
				p1.setY(y)	

			self.zoomRect.setRect(p0.x(), p0.y(), p1.x() - p0.x(),
			 p1.y() - p0.y())										#Altera as dimensões do retângulo

			self.zoomRect.setVisible(True)							#Certifica-se de que o retângulo está visível

		if self.drawing == True:
			self.line_p1.setX(event.x())
			self.line_p1.setY(event.y())

			p0 = self.line_p0										#Transforma as coordenadas de viewport para coordenadas de Cena.
			p1 = self.mapToScene(self.line_p1)						#as coordenadas são bem diferentes pois o objeto QGraphicsView aplica 
																	#varías transformações para centralizar, escalar, rotacionar etc a 
																	#cena na visualização.

			self.line.setLine(QtCore.QLineF(p0, p1))				#Altera as dimensões da linha
			self.line.setVisible(True)								#Certifica-se de que a linha está visível


	def updatePreviewImage(self, image):
		self.pixmap_preview.setPixmap(QtGui.QPixmap.fromImage(image))
		self.setSceneRect(0, 0, image.width(), image.height())		


	def cv2ImgToQImage(self, array):
		img = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
		qimg = QtGui.QImage(img.data, img.shape[1], img.shape[0], QtGui.QImage.Format_RGB888)
		return qimg

	#Overload da função keyPressEvent apenas para desabilitar o scroll pelas teclas cima, baixo, direita e esquerda.
	def keyPressEvent(self, event):
		pass

	def setLineColor(self, r, g, b):
		self.line_pen.setColor(QtGui.QColor(int(r), int(g), int(b)))
		self.line.setPen(self.line_pen)

	def resetView(self):
		self.zoom = 1.0		
		self.resetMatrix()											#Limpa a matriz de transformação
		self.scale(self.zoom, self.zoom)							#Aplica o zoom na matriz

		self.zoomRect.setRect(0, 0, 0, 0)
		self.line.setLine(0, 0, 0, 0)
		self.pixmap_preview.setPixmap(QtGui.QPixmap())

	def getLineLength(self):
		return self.line.line().length()


