#coding: utf-8
import sys
import os

from PyQt4.QtGui import QFileDialog, QMessageBox, QPushButton, QGridLayout, QWidget
from PyQt4.QtCore import QObject, pyqtSignal, Qt, pyqtSlot
from PyQt4 import QtGui, QtCore
from pymediainfo import MediaInfo
from cv2 import VideoCapture
import cv2

from errors import NoMediaOpenedError
from media import LengthHint, FPSHint
import log



class ICFile(object):
    def __init__(self):
        self.cap  = VideoCapture()
        self.pos  = None
        self.len  = None
        self.size = None
        self.fps  = None

    def close_file(self):
        if self.cap.isOpened():
            self.cap.release()
            self.pos  = None
            self.len  = None
            self.size = None
            self.fps  = None
        self.media.close()

    def open_file(self, path):
        try:
            self.close_file()
            if self.cap.open(path):
                info = [t for t in MediaInfo.parse(path).tracks if t.track_type == 'Video']
                if not info:
                    log.write("The file {} has no video tracks".format(path))
                    return False

                self.len  =  int(info[0].frame_count)
                self.size = (int(info[0].width), int(info[0].height))
                self.fps  =  int(float(info[0].frame_rate))
                self.pos  = 0
                #size, length, pos, fps, seekable, l_hint, f_hint, next_func, seek_func
                if self.media.open(self.size, self.len, self.pos, self.fps,
                                True, LengthHint.Fixed, FPSHint.Fixed,
                                self.next, self.seek):
                    return True
                else:

                    self.close_file()
                    return False
            else:
                log.write("OpenCV3 VideoCapture object could not open file {}".format(path))
        except:
            log.dump_traceback()
            self.cap.release()
            return False

    def seek(self, pos):
        if pos < 0 or pos > self.len - 1:
            raise IndexError()
        if self.cap.set(cv2.CAP_PROP_POS_FRAMES, pos):
            self.pos        = pos
            self.media.pos  = pos
            return True
        else:
            return False

    def next(self):
        if self.pos >= self.len:
            raise EOFError()
        ret, frame = self.cap.read()
        if ret:
            self.pos += 1
            self.media.pos = self.pos
            return frame


    def pb_open_clicked(self, checked):
        file_path = str(QFileDialog.getOpenFileName(None, "Select a video file"))
        if file_path:
            self.open_file(file_path)

    def init_plugin(self, *args, **kwargs):
        self.gui   = kwargs["gui_proxy"  ]
        self.media = kwargs["media_proxy"]

        layout       = QGridLayout()
        self.widget  = QWidget()
        self.pb_open = QPushButton()

        layout.addWidget(self.pb_open, 0, 0)
        self.pb_open.setText("Open Video File")

        self.widget.setLayout(layout)
        self.gui.add_tool_tab(self.widget, "ICFile")
        self.pb_open.clicked.connect(self.pb_open_clicked)
        return True

    def release(self):
        self.cap.isOpened() and self.cap.release()
        self.gui.remove_tool_tab(self.widget)
        self.widget.deleteLater()
        self.media.close()

def main():
    """Create and return a Video Input Model Object.
    """
    return ICFile()
