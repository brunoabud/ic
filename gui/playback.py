import logging
log = logging.getLogger(__name__)


from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QIcon, QPixmap, QImage
import cv2

from application import get_app
from ic.video_source import get_vs
from ic.frame_stream import get_fs
from ic.queue import Empty


class Playback(object):
    """Class that controls the Playback GUI and manages the FrameStream states.

    """
    # Format modes of the labels that display the current position of the
    # Video Source.
    FORMAT_FRAME_POS  = 0x0                 # Integer representing the pos
    FORMAT_FRAME_TIME = 0x1                 # mm:ss:ms

    def __init__(self, main_window):
        # A reference to the QMainWindow widget
        self.main_window = main_window
        # Register this object to the messages system
        self.m_id = get_app().register_message_listener(self)

        # The timer responsible for getting frames from the preview queue
        # and showing them to the user
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)

        main_window.pb_play.clicked.connect(self.pb_play_clicked)
        main_window.scb_pos.sliderPressed.connect(self.start_seeking)
        main_window.scb_pos.sliderReleased.connect(self.seek)
        main_window.scb_pos.sliderMoved.connect(self.slider_moved)

        self.wait_to_seek = False

    def slider_moved(self, value):
        self.main_window.lbl_current.setText(self._format_pos(value))

    def start_seeking(self):
        self.wait_to_seek = True

    def seek(self):
        fs = get_fs()
        fs.seek(self.main_window.scb_pos.sliderPosition())
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
            self.wait_to_seek = False

    def _format_pos(self, pos, fps = None):
        vs = get_vs()
        length = vs.get_length()
        str_size = len(str(length))
        format_str = "{:0"+str(str_size)+"d}"
        return format_str.format(pos)

    def _reset_gui(self):
        mw = self.main_window

        mw.frm_playback.setEnabled(False)

        mw.lbl_current.setText(self._format_pos(0))
        mw.lbl_total.setText(self._format_pos(0))

        mw.scb_pos.setRange(0, 0)

        mw.pb_play.setChecked(False)
        mw.pb_play.setIcon(QIcon(":icon/pause"))

    def _update_gui(self, pos = 0):
        mw = self.main_window
        vs = get_vs()

        mw.frm_playback.setEnabled(True)
        mw.scb_pos.setRange(0, vs.get_length() - 1)
        mw.lbl_total.setText(self._format_pos(mw.scb_pos.maximum(), vs.get_fps()))


    def _play(self):
        self.main_window.pb_play.setChecked(True)
        self.main_window.pb_play.setIcon(QIcon(":icon/pause"))
        self.preview_timer.start()

    def _pause(self):
        self.main_window.pb_play.setChecked(False)
        self.main_window.pb_play.setIcon(QIcon(":icon/play"))

    def _set_pos(self, pos):
        mw = self.main_window
        mw.scb_pos.setValue(pos)
        mw.lbl_current.setText(self._format_pos(pos, get_vs().get_fps()))

    def update_preview(self):
        try:
            mw = self.main_window
            fs = get_fs()
            preview_queue = fs.preview_queue

            # Dont pull frames if the user is seeking
            if not mw.scb_pos.isSliderDown():
                if not self.wait_to_seek:
                    state, frame = preview_queue.get(False)
                    self._set_pos(state["pos"])

                    # Convert and show the frame
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Create a QImage with the frame data
                    img = QImage(rgb.tostring(), rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
                    # Create and show the Pixmap
                    pixmap = QPixmap(img)
                    self.main_window.lbl_preview.setPixmap(pixmap)
        except Empty:
            pass

        if self.main_window.pb_play.isChecked():
            self.preview_timer.start(0)

    def pb_play_clicked(self, checked):
        app = get_app()
        fs = get_fs()

        if checked:
            fs.start()
            self._play()
        else:
            fs.stop()
            self._pause()
