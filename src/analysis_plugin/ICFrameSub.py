#coding: utf-8
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from PyQt4.QtGui import QWidget, QGridLayout, QSlider, QLabel
from matplotlib.figure import Figure
from PyQt4.QtCore import Qt, QTimer
import numpy as np
import math
import cv2

from media import FPSHint, LengthHint



def impar(value):
    return value | 0x01

class ICFrameSub(object):
    def __init__(self):
        self.params = {}
        self.tab_graficos = QWidget()
        self.tab_graficos.setLayout(QGridLayout())

    def inicializar_grafico(self):
        #Cria duas subplots (uma para x outra para y)
        self.xplt = self.mplcanvas.figure.add_subplot(2, 1, 1)
        self.yplt = self.mplcanvas.figure.add_subplot(2, 1, 2)
        self.xl,   = self.xplt.plot([], [])
        self.yl,   = self.yplt.plot([], [])

        self.xl.set_marker('o')
        self.yl.set_marker('o')
        self.xl.set_fillstyle('full')
        self.yl.set_fillstyle('full')
        self.xl.set_linestyle('')
        self.yl.set_linestyle('')
        self.xl.set_markersize(3.0)
        self.yl.set_markersize(2.5)

        self.mplcanvas.draw()

    def atualizar_grafico(self, x, y, framepos, fps):
        try:
            tempo = 1.0 / fps * framepos
            self.tempo[framepos] = tempo
            self.x[framepos]     = x
            self.y[framepos]     = y
            self.xl.set_data(self.tempo, self.x)
            self.yl.set_data(self.tempo, self.y)


        except Exception as e:
            print e
        finally:
            self.mplcanvas.draw()
    def init_plugin(self, *args, **kwargs):
        gui            = kwargs["gui_proxy"]

        self.thresh    = gui.int_parameter(13, (3, 99), "Valor do threshold", adjust_func = impar)
        self.thresh_c  = gui.int_parameter(8 , (0, 99), "Constante de treshold")
        self.blur01    = gui.int_parameter(3 , (3, 99), "Primeiro blur", adjust_func = impar)
        self.blur02    = gui.int_parameter(3 , (3, 99), "Segundo blur", adjust_func = impar)
        self.dkernel   = gui.int_parameter(5 , (3, 99), "Tamanho do kernel de dilatacao", adjust_func = impar)
        self.skernel   = gui.int_parameter(4 , (3, 99), "Quantidade de passos da dilatacao")
        self.skip      = gui.int_parameter(1 , (0,  5), "Quantidade de frames a serem pulados")
        self.mplcanvas = FigureCanvas(Figure(figsize=(6, 5), dpi=100))
        self.gui       = gui
        self.gui.add_main_tab(self.tab_graficos, "Analise")
        self.tab_graficos.layout().addWidget(self.mplcanvas, 0, 0)
        self.inicializar_grafico()
        self.inicializar_processamento()
        return True

    def release(self):
        pass

    def inicializar_processamento(self):
        self.preview    = None
        self.previous   = None
        self.skipped    = 0

    def on_media_opened(self, media_state, length_hint, fps_hint):
        self.width, self.height = media_state.size
        self.tempo = np.empty((media_state.length,))
        self.x     = np.empty((media_state.length,))
        self.y     = np.empty((media_state.length,))

        self.tempo.fill(np.nan)
        self.x.fill(np.nan)
        self.y.fill(np.nan)
        if self.xplt.axis() != [0, self.width, 0, self.height]:
            self.xplt.axis([0, 1.0 / media_state.fps * media_state.length, 0, media_state.size[0]])
            self.yplt.axis([0, 1.0 / media_state.fps * media_state.length, 0, media_state.size[1]])


    def on_media_closed(self, media_state):
        self.xplt.clear()
        self.yplt.clear()
        self.mplcanvas.figure.clear()
        self.mplcanvas.draw()

    def on_media_sought(self, media_state):
        pass
    
    def process_frame(self, media_state, frame):
        if self.previous is None:
            self.previous = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.previous = cv2.blur(self.previous, (self.blur01.value,)*2)
            return np.zeros(frame.shape)
        if self.skipped < self.skip.value and self.preview is not None:
            self.skipped += 1
            return self.preview
        #Reset the skipped
        self.skipped = 0

    	cinza 		    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    	cinza 		    = cv2.blur(cinza, (self.blur01.value,)*2)

    	diferenca       = cv2.absdiff(cinza, self.previous)
    	diferenca 		= cv2.blur(diferenca, (self.blur02.value,)*2)

    	binario 		= cv2.adaptiveThreshold(diferenca, 255,
    		              cv2.ADAPTIVE_THRESH_MEAN_C,
                          cv2.THRESH_BINARY_INV, self.thresh.value,
                          self.thresh_c.value)

    	kernel          = np.ones((self.skernel.value,)*2, np.uint8)
    	binario         = cv2.dilate(binario, kernel, iterations=self.dkernel.value)

        self.previous = cinza

    	_, contorno, h  = cv2.findContours(binario, cv2.RETR_EXTERNAL,
    					  cv2.CHAIN_APPROX_SIMPLE)
        if contorno:
            try:
                M = cv2.moments(contorno[0])
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
                cv2.circle(frame, (x,y), 8, (255,0,0),3)
                self.atualizar_grafico(x, y, media_state.pos, media_state.fps)
            except:
                pass
                #self.atualizar_grafico(np.nan, np.nan, media_state.pos, media_state.fps)
        else:
            self.atualizar_grafico(np.nan, np.nan, media_state.pos, media_state.fps)


        self.preview = frame
        return frame

def main():
    return ICFrameSub()
