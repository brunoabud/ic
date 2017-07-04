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
import os
import logging

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QMainWindow, QPixmap, QImage, QColor
import cv2

from ic import settings
from ic import engine
from gui import tr
from gui.vc_target_dialog import VCTargetDialog, TargetRole

LOG = logging.getLogger(__name__)

# Create a list of COLOR constants contained in the cv2 module
COLORS = [i for i in dir(cv2) if i.startswith("COLOR")]

class ViewCanvas(QMainWindow):
    """Window used to preview frames from any processing stage."""
    def __init__(self, main_window, preview_target="filter_page:Raw;"):
        super(ViewCanvas, self).__init__()
        self._main = main_window
        uic.loadUi(os.path.join(settings.get("resources_dir"), "ui", "ViewCanvas.ui"), self)
        if preview_target not in engine.targets_buffer:
            engine.targets_buffer[preview_target] = None
        self._target = preview_target
        self._setupUi()

    def _setupUi(self):
        self.actn_change_target.triggered.connect(self._change_target)

    def _change_target(self, checked):
        dialog = VCTargetDialog(self)
        if dialog.exec_():
            index = dialog.tv_targets.currentIndex()
            old_target = self._target
            self.setWindowTitle(u"Imagem Cinemática - Canvas [%s]" % str(dialog.tv_targets.model().data(index, Qt.DisplayRole).toPyObject()))
            self._target = str(dialog.le_identifier.text())
            if self._target not in engine.targets_buffer:
                engine.targets_buffer[self._target] = None
            if not [c for c in self._main._canvas_list if c._target == old_target]:
                del engine.targets_buffer[old_target]

    def update_preview(self, image):
        if image is not None:
            colorspace, data = image
            if colorspace == "qimage":
                self.lbl_frame.setPixmap(QPixmap.fromImage(data))
                return
        pix = QPixmap(40, 40)
        pix.fill(QColor(0, 0,0))
        self.lbl_frame.setPixmap(pix)

    def closeEvent(self, event):
        self._main._canvas_list.remove(self)
        if not [c for c in self._main._canvas_list if c._target == self._target]:
            del engine.targets_buffer[self._target]

        self.deleteLater()
        event.accept()
