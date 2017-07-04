# coding: utf-8
# Copyright (C) 2016 Bruno Abude Cardoso
#
# Imagem Cinemática is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Imagem Cinemática is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QIcon, QPixmap, QImage, QApplication
import cv2

from application import get_app
from ic.queue import Empty
from ic import engine
from ic import messages

# Create the logger object for this module
LOG = logging.getLogger(__name__)

class Playback(object):
    """Class that controls the Playback GUI and manages the FrameStream states.

    """
    def __init__(self, main_window):
        self._main = main_window
        # Register this object to the messages system
        messages.register(self)

        # The timer responsible for getting frames from the preview queue
        # and showing them to the user
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        self.wait_to_seek = False

    def slider_moved(self, value):
        self._main.lbl_current.setText(self._format_pos(value))

    def start_seeking(self):
        self.wait_to_seek = True

    def seek(self):
        fs = engine.frame_stream
        fs.seek(self._main.scb_pos.sliderPosition())
        self.wait_to_seek = True
        self.preview_timer.start()

    def message_received(self, mtype, mdata, sender):
        if mtype == "ENGINE_source_opened":
            seekable, length = mdata.split(";")
            if length != "None":
                self.source_length = int(length)
            else:
                self.source_length = 0
            if seekable == "True":
                self._main.scb_pos.setEnabled(True)
            else:
                self._main.scb_pos.setEnabled(False)
            self._update_gui()
        elif mtype == "ENGINE_source_closed":
            self._reset_gui()
        elif mtype == "FS_stream_started":
            self._play()
        elif mtype == "FS_stream_stopped":
            self._pause()

    def _format_pos(self, pos):
        str_size = len(str(self.source_length))
        format_str = "{:0"+str(str_size)+"d}"
        return format_str.format(pos)

    def _reset_gui(self):
        mw = self._main

        mw.frm_playback.setEnabled(False)

        mw.lbl_current.setText(self._format_pos(0))
        mw.lbl_total.setText(self._format_pos(0))

        mw.scb_pos.setRange(0, 0)

        mw.pb_play.setChecked(False)
        mw.pb_play.setIcon(QIcon(":icon/play"))

        fs = engine.frame_stream
        fs.start(True)
        self.wait_to_seek = True
        self.preview_timer.start()

    def _update_gui(self, pos = 0):
        mw = self._main
        mw.frm_playback.setEnabled(True)
        mw.scb_pos.setRange(0, max(self.source_length - 1, 0))
        mw.lbl_total.setText(self._format_pos(mw.scb_pos.maximum()))


    def _play(self):
        self._main.pb_play.setChecked(True)
        self._main.pb_play.setIcon(QIcon(":icon/pause"))
        self.preview_timer.start()

    def _pause(self):
        self._main.pb_play.setChecked(False)
        self._main.pb_play.setIcon(QIcon(":icon/play"))

    def _set_pos(self, pos):
        mw = self._main
        mw.scb_pos.setValue(pos)
        mw.lbl_current.setText(self._format_pos(pos))

    def update_preview(self):
        interval = 20
        try:
            mw = self._main
            fs = engine.frame_stream
            preview_queue = engine.preview_queue
            # Don't get frames from the queue if the user is moving the time
            # scroll bar
            if not mw.scb_pos.isSliderDown():
                targets_buffer = preview_queue.get(False)
                pos = targets_buffer["pos"]
                timestamp = targets_buffer["timestamp"]

                self._set_pos(pos)

                for target in targets_buffer:
                    for canvas in [c for c in self._main._canvas_list if c._target == target]:
                        f = targets_buffer[target]
                        canvas.update_preview(f)
                        QApplication.instance().processEvents()

                self.wait_to_seek = False
        except Empty:
            interval = 0
        except:
            LOG.debug("", exc_info=True)

        if self._main.pb_play.isChecked() or self.wait_to_seek:
            self.preview_timer.start(interval)

    def pb_play_clicked(self, checked):
        app = get_app()
        fs = engine.frame_stream

        if checked:
            fs.start()
            self._play()
        else:
            fs.stop()
            self._pause()
