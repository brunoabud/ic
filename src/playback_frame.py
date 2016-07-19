#encoding: utf-8
import os
import itertools

from PyQt4.QtGui import QStringListModel, QApplication, QPushButton, QFrame
from PyQt4.QtGui import QWidget, QDialog, QMainWindow, QMessageBox, QIcon
from PyQt4.QtCore import QObject, Qt, pyqtSlot, SIGNAL, SLOT, QTimer
from PyQt4.QtGui import QAbstractSlider
from PyQt4 import uic
from enum import Enum

from media import CursorPosition
from time_util import TicCounter
import main
import messages
import log
from queue import Full,  Empty


class FormatMode(Enum):
    Time = 1
    FramePos = 2


class ICPlaybackFrame(QFrame):
    def formatpos(self, pos, fps = None):
        if self.format is FormatMode.FramePos:
            return str(pos)
        elif self.format is FormatMode.Time:
            try:
                if fps is None:
                    fps = main.ic.media.state.fps
                ms_total  = int(1000.0 / fps * pos)
                ms        = ms_total % 1000
                s         = ms_total / 1000  % 60
                m         = ms_total / 60000 % 60
                return "{:02d}:{:02d}:{:03d}".format(m, s, ms)
            except:
                return "00:00:000"

    def translate_pos(self, pos):
        if pos is CursorPosition.Begin:
            return 0
        elif pos is CursorPosition.End:
            return main.mainwindow.scb_pos.maximum()
        elif pos is CursorPosition.EOF:
            return main.mainwindow.scb_pos.maximum()
        else:
            return pos

    def receive_message(self, message_type, message_data, sender):
        if message_type == 'media_opened':
            try:
                state = main.ic.media.state
                main.mainwindow.scb_pos.setRange(0, state.length - 1)
                main.mainwindow.scb_pos.setValue(self.translate_pos(state.pos))
                self.setEnabled(True)
            except:
                Log.dumptraceback()
        elif message_type == 'media_closed':
            main.mainwindow.scb_pos.setRange(0, 0)
            main.mainwindow.pb_play.setChecked(False)
            self.setEnabled(False)
        elif message_type == 'worker_stopped':
            main.mainwindow.pb_play.setChecked(False)
            self.previewtimer.stop()
        elif message_type == 'media_seeked':
            self.waiting_seek = False
            if not main.mainwindow.pb_play.isChecked():
                messages.post_message('start_worker', {'single_shot' : True, 'id': 'reader'}, self)
                messages.post_message('start_worker', {'single_shot' : True, 'id': 'processor'}, self)
                self.previewtimer.start(0)
                self.single_shot = True

    def scb_pos_valueChanged(self, value):
        main.mainwindow.lbl_current.setText(self.formatpos(value))

    def scb_pos_sliderMoved(self):
        main.mainwindow.lbl_current.setText(self.formatpos(main.mainwindow.scb_pos.sliderPosition()))

    def scb_pos_sliderReleased(self):
        pos = main.mainwindow.scb_pos.sliderPosition()
        messages.post_message("media_seek", {'pos' : pos}, self)
        self.waiting_seek = True

    def scb_pos_rangeChanged(self, min_, max_):
        main.mainwindow.lbl_total.setText(self.formatpos(max_))
        main.mainwindow.lbl_current.setText(self.formatpos(main.mainwindow.scb_pos.value()))

    def pb_play_clicked(self, checked):
        if checked:
            messages.post_message('start_worker', {'single_shot' : False, 'id': 'reader'}, self)
            messages.post_message('start_worker', {'single_shot' : False, 'id': 'processor'}, self)
            self.previewtimer.start()
        else:
            messages.post_message('stop_worker', {'id': 'reader'}, self)
            messages.post_message('stop_worker', {'id': 'processor'}, self)

    def preview_timeout(self):
        try:
            if not main.mainwindow.scb_pos.isSliderDown() and not self.waiting_seek:
                state, frame = main.previewqueue.get(False)
                main.mainwindow.scb_pos.setValue(state.pos)
                main.mainwindow.tab_preview.show_frame(frame)
                self.single_shot = False

            if main.mainwindow.pb_play.isChecked() or self.single_shot:
                self.previewtimer.start(0)
                self.single_shot = True
        except Empty:
            self.previewtimer.start(0)

        except:
            log.dump_traceback()

    def pb_loop_clicked(self, checked):
        main.ic.media.loop = checked

    def init(self):
        messages.add_message_listener(self)

        main.mainwindow.scb_pos.valueChanged.connect(self.scb_pos_valueChanged)
        main.mainwindow.scb_pos.sliderMoved.connect(self.scb_pos_sliderMoved)
        main.mainwindow.scb_pos.sliderReleased.connect(self.scb_pos_sliderReleased)
        main.mainwindow.scb_pos.rangeChanged.connect(self.scb_pos_rangeChanged)

        main.mainwindow.pb_play.clicked.connect(self.pb_play_clicked)
        main.mainwindow.pb_loop.clicked.connect(self.pb_loop_clicked)

    def __init__(self, parent = None):
        super(ICPlaybackFrame, self).__init__(parent)
        self.format = FormatMode.Time
        self.previewtimer = QTimer()
        self.previewtimer.timeout.connect(self.preview_timeout)
        self.previewtimer.setSingleShot(True)
        self.waiting_seek = False
        self.single_shot = False
