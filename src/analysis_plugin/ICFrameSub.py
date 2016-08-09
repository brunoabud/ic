#coding: utf-8
import math
from collections import deque
import os
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from PyQt4.QtGui import QWidget, QGridLayout
from PyQt4 import uic
from matplotlib.figure import Figure
import numpy as np
import cv2

from media import FPSHint, LengthHint


def impar(value):
    return value | 0x01


class Processador(object):
    def __init__(self, gui_proxy):
        self.thresh    = gui_proxy.int_parameter(13, (3, 99),
        "Threshold block size", adjust_func = impar)
        self.thresh_c  = gui_proxy.int_parameter(8 , (1, 10),
        "Threshold constant")
        self.blur01    = gui_proxy.int_parameter(3 , (3, 99),
        "Pre-blur", adjust_func = impar)
        self.blur02    = gui_proxy.int_parameter(3 , (3, 99),
        "Post-blur", adjust_func = impar)
        self.dkernel   = gui_proxy.int_parameter(5 , (3, 99),
        "Dilatation kernel", adjust_func = impar)
        self.skernel   = gui_proxy.int_parameter(4 , (3, 99),
        "Dilatation iterations")
        self.skip      = gui_proxy.int_parameter(1 , (0,  5),
        "Max frames to be skipped")
        self.queue = deque()

    def add_frame(self, media_state, frame):
        self.queue.append((media_state, frame))

    def frame_sub(self, f1, f2):
        g1              = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
        g1              = cv2.blur(g1, (self.blur01.value,)*2)
        g2              = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
        g1              = cv2.blur(g2, (self.blur01.value,)*2)

    	diferenca       = cv2.absdiff(g1, g2)
    	diferenca 		= cv2.blur(diferenca, (self.blur02.value,)*2)

    	binario 		= cv2.adaptiveThreshold(diferenca, 255,
    		              cv2.ADAPTIVE_THRESH_MEAN_C,
                          cv2.THRESH_BINARY_INV, self.thresh.value,
                          self.thresh_c.value)

    	kernel          = np.ones((self.skernel.value,)*2, np.uint8)
    	binario         = cv2.dilate(binario, kernel, iterations=self.dkernel.value)

    	_, contorno, h  = cv2.findContours(binario, cv2.RETR_EXTERNAL,
    					  cv2.CHAIN_APPROX_SIMPLE)
        if contorno:
            try:
                M = cv2.moments(contorno[0])
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
                return (x, y)
            except:
                return (None, None)
        else:
            return (None, None)

    def process_frame(self):
        if self.queue.empty() or self.queue.qsize() < self.skip.value + 2:
            return (None, None, None, None, None)
        try:
            state1, frame1 = self.queue.popleft()
            for i in range(0, self.skip.value + 1):
                state2, frame2 = self.queue[i]
                x, y = self.frame_sub(frame1, frame2)
                if x is not None and y is not None:
                    return (x, y, frame1, state1, state2)
            return (None, None, frame1, state1, None)
        except:
            return (None, None, frame1, state1, None)

    def clear(self):
        self.queue.queue.clear()


class ICFrameSub(object):
    def __init__(self):
        pass

    def init_plugin(self, *args, **kwargs):
        gui              = kwargs["gui_proxy"]
        return True

    def release(self):
        pass

    def on_media_opened(self, media_state, length_hint, fps_hint):
        pass

    def on_media_closed(self, media_state):
        pass

    def on_media_sought(self, media_state):
        pass

    def process_frame(self, media_state, frame):
        return (media_state, frame)



def main():
    return ICFrameSub()
