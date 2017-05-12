# coding: latin-1
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
from PyQt4.QtGui import QIcon, QPixmap, QImage
import cv2

from application import get_app
from ic.queue import Empty
from ic.engine import get_engine

# Create the logger object for this module
LOG = logging.getLogger(__name__)
# Create a list of COLOR constants contained in the cv2 module
COLORS = [i for i in dir(cv2) if i.startswith("COLOR")]


class Playback(object):
    """Class that controls the Playback GUI and manages the FrameStream states.

    """
    # Format modes of the labels that display the current position of the
    # Video Source.
    FORMAT_FRAME_POS  = 0x0                 # Integer representing the frame pos
    FORMAT_FRAME_TIME = 0x1                 # 02i:02i:03i % min:sec:ms

    def __init__(self):
        # Register this object to the messages system
        self.m_id = get_app().register_message_listener(self)

        # The timer responsible for getting frames from the preview queue
        # and showing them to the user
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        self.wait_to_seek = False

    def slider_moved(self, value):
        get_app().get_ui("main_window").lbl_current.setText(self._format_pos(value))

    def start_seeking(self):
        self.wait_to_seek = True

    def seek(self):
        fs = get_engine().get_component("frame_stream")
        fs.seek(get_app().get_ui("main_window").scb_pos.sliderPosition())
        self.wait_to_seek = True
        self.preview_timer.start()

    def receive_message(self, mtype, mdata, sender):
        if mtype == "video_source_opened":
            self._update_gui()
        elif mtype == "video_source_closed":
            self._reset_gui()
        elif mtype == "frame_stream_started":
            self._play()
        elif mtype == "frame_stream_stopped":
            self._pause()
        elif mtype == "frame_stream_sought":
            pass

    def _format_pos(self, pos, fps = None):
        vs = get_engine().get_component("video_source")
        length = vs.get_length()
        str_size = len(str(length))
        format_str = "{:0"+str(str_size)+"d}"
        return format_str.format(pos)

    def _reset_gui(self):
        mw = get_app().get_ui("main_window")

        mw.frm_playback.setEnabled(False)

        mw.lbl_current.setText(self._format_pos(0))
        mw.lbl_total.setText(self._format_pos(0))

        mw.scb_pos.setRange(0, 0)

        mw.pb_play.setChecked(False)
        mw.pb_play.setIcon(QIcon(":icon/play"))

        fs = get_engine().get_component("frame_stream")
        fs.start(True)
        self.wait_to_seek = True
        self.preview_timer.start()

    def _update_gui(self, pos = 0):
        mw = get_app().get_ui("main_window")
        vs = get_engine().get_component("video_source")

        mw.frm_playback.setEnabled(True)
        mw.scb_pos.setRange(0, vs.get_length() - 1)
        mw.lbl_total.setText(self._format_pos(mw.scb_pos.maximum(), vs.get_fps()))


    def _play(self):
        get_app().get_ui("main_window").pb_play.setChecked(True)
        get_app().get_ui("main_window").pb_play.setIcon(QIcon(":icon/pause"))
        self.preview_timer.start()

    def _pause(self):
        get_app().get_ui("main_window").pb_play.setChecked(False)
        get_app().get_ui("main_window").pb_play.setIcon(QIcon(":icon/play"))

    def _set_pos(self, pos):
        mw = get_app().get_ui("main_window")
        mw.scb_pos.setValue(pos)
        mw.lbl_current.setText(self._format_pos(pos, get_engine().get_component("video_source").get_fps()))

    def update_preview(self):
        interval = 0
        try:
            mw = get_app().get_ui("main_window")
            fs = get_engine().get_component("frame_stream")
            preview_queue = fs.preview_queue

            # Don't get frames from the queueif the user is moving the time
            # scroll bar
            if not mw.scb_pos.isSliderDown():
                frame = preview_queue.get(False)
                self._set_pos(frame.pos)
                # If the current tab isn't the preview, don't bother converting
                # the frames.
                if mw.maintab.currentIndex() == mw.maintab.indexOf(mw.tab_preview):
                    # Generate COLOR CONVERTION CONSTANT to RGB based on the
                    # frame color space
                    color = "COLOR_" + frame.color_space + "2RGB"
                    # Check if it is valid
                    if not color in COLORS and frame.color_space != "RGB":
                        log.error("Can't convert {} to RGB".format(frame.color_space))
                    else:
                        rgb = None
                        # Convert the frame if it isn't at RGB format yet
                        if frame.color_space == "RGB":
                            rgb = frame.data
                        else:
                            rgb = cv2.cvtColor(frame.data, getattr(cv2, color))
                        # Create a QImage with the frame data
                        img = QImage(rgb.tostring(), rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
                        # Create and show the Pixmap
                        pixmap = QPixmap(img)
                        get_app().get_ui("main_window").lbl_preview.setPixmap(pixmap)
                        self.wait_to_seek = False
        except Empty:
            interval = 0

        if get_app().get_ui("main_window").pb_play.isChecked() or self.wait_to_seek:
            self.preview_timer.start(interval)

    def pb_play_clicked(self, checked):
        app = get_app()
        fs = get_engine().get_component("frame_stream")

        if checked:
            fs.start()
            self._play()
        else:
            fs.stop()
            self._pause()
