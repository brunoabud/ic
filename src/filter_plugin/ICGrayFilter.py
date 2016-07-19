import cv2, numpy as np

from PyQt4.QtCore import (QObject, pyqtSlot, pyqtSignal)

class ICGrayFilter(object):
    def __init__(self):
        self.parameters = {}

    def applyFilter(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.merge([gray, gray, gray])

    def release(self):
        pass
def main():
    return ICGrayFilter()
