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

from PyQt4.QtGui import QScrollArea, QDial, QSlider, QScrollBar, QBoxLayout
from PyQt4.QtGui import QWidget, QLabel
from PyQt4.QtCore import Qt

from gui import tr
from ic import settings

LOG = logging.getLogger(__name__)

class GUIInterface(object):
    """Provide utlity and methods to manipulate the main application GUI.

    """
    def __init__(self, main_window):
        self._main = main_window
        # Cache all the windows created by the plugin (to safely remove later)
        self.windows = []


    def main_window(self):
        return self._main

    def show_window(self, widget):
        if widget not in self.windows:
            self.windows.append(widget)
            #widget.setParent(self._main)
            widget.show()

    def close_window(self, widget):
        if widget in self.windows:
            self.windows.remove(widget)
            widget.setParent(None)
            widget.deleteLater()

    def release(self, error=0):
        for i in [i for i in self.windows]:
            self.close_window(i)
