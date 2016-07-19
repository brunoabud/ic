import cv2, numpy as np

from PyQt4.QtCore import (QObject, pyqtSlot, pyqtSignal)

class ICBlurFilter(object):
    def __init__(self):
        self.parameters = {}
        self.parameters['kernelsize'] = {'title': 'Kernel Size', 'value':3, 'min':3, 'max':99,
        'paramSlot': self._kernelsize_onSliderMoved, 'lblSlot': None}

    def _kernelsize_onSliderMoved(self, value):
        value = value | 1
        self.parameters['kernelsize']['value'] = value
        self.parameters['kernelsize']['lblSlot'](value)

    def applyFilter(self, frame):
        kernelsize = int(self.parameters['kernelsize']['value'])
        return cv2.blur(frame, (kernelsize, kernelsize))

    def release(self):
        pass
def main():
    return ICBlurFilter()
