import cv2, numpy as np

from PyQt4.QtCore import (QObject, pyqtSlot, pyqtSignal)

class ICThresholdFilter(object):
    def __init__(self):
        self.parameters = {}
        self.parameters['thresh_c'] = {'title': 'Threshold Constant', 'value':3, 'min':3, 'max':99,
        'paramSlot': self._thresh_c_onSliderMoved, 'lblSlot': None}
        self.parameters['thresh_sensi'] = {'title': 'Threshold Sensitivity', 'value':3, 'min':3, 'max':99,
        'paramSlot': self._thresh_sensi_onSliderMoved, 'lblSlot': None}

    def _thresh_sensi_onSliderMoved(self, value):
        value = value | 1
        self.parameters['thresh_sensi']['value'] = value
        self.parameters['thresh_sensi']['lblSlot'](value)

    def _thresh_c_onSliderMoved(self, value):
        self.parameters['thresh_c']['value'] = value
        self.parameters['thresh_c']['lblSlot'](value)

    def applyFilter(self, frame):
        thresh_sensi = self.parameters['thresh_sensi']['value']
        thresh_c = self.parameters['thresh_c']['value']
        b, g, r = cv2.split(frame)

        b = cv2.adaptiveThreshold(b, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, thresh_sensi, thresh_c)
        return cv2.merge([b, b, b])

    def release(self):
        pass
def main():
    return ICThresholdFilter()
