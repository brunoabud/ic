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

import sys
import os
from os.path import join as pjoin
import logging

from PyQt4.QtGui import QMainWindow, QMessageBox, QDialog, QTextCursor, QFrame
from PyQt4.QtGui import QActionGroup, QLabel, QIcon, QInputDialog, QPixmap
from PyQt4.QtGui import QMessageBox

from PyQt4.QtCore import QString, QTimer, pyqtSlot, Qt
from PyQt4 import uic
import cv2

from application import get_app, Application
from gui import tr
from gui.gui_interface import GUIInterface
from gui.plugin_dialog import PluginDialog
from gui.playback import Playback
from gui.filter_rack_window import FilterRackWindow
from ic import settings
from ic import engine
from ic import messages
from gui.view_canvas import ViewCanvas

LOG = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi(os.path.join(settings.get("app_path"), "res", "ui", "main_window.ui"), self)
        messages.register(self)
        self.setupUi()

        self._canvas_list = []

    def actn_load_input_plugin_triggered(self, checked):
        pass

    def actngroup_language_triggered(self, action):
        pass

    def prompt_input_plugin(self, checked):
        ret, selected = PluginDialog.select_type("input")
        if ret:
            try:
                plugin = engine.load_input_plugin(selected, GUIInterface(self))
            except:
                LOG.error("", exc_info=True)
                QMessageBox.warning(None, tr("MainWindow", "Plugin Load Error"),
                tr("MainWindow", "Got an error when trying to load the input plugin"))

        return

    def actn_new_canvas_triggered(self, checked):
        canvas = ViewCanvas(self, "filter_page:Raw;")
        canvas.show()
        self._canvas_list.append(canvas)

    def update_filter_uis(self):
        return

    def add_filter_gui(self, plugin):
        return

    def prompt_analysis_plugin(self, checked):
        ret, selected = PluginDialog.select_type("analysis")
        if ret:
            try:
                plugin = engine.load_analysis_plugin(selected, GUIInterface(self))
            except:
                LOG.error("", exc_info=True)
                QMessageBox.warning(None, tr("MainWindow", "Plugin Load Error"),
                tr("MainWindow", "Got an error when trying to load the input plugin"))

    def prompt_filter_plugin(self, checked):
        return

    def set_loop(self, loop):
        engine.frame_stream.loop = loop

    def setupUi(self):
        self.filter_rack_window = FilterRackWindow(self)
        self.filter_rack_window.show()

        # Create the Playback object that will take care of the preview and
        # playback gui
        self.playback = Playback(self)
        self.pb_play.clicked.connect(self.playback.pb_play_clicked)
        self.scb_pos.sliderPressed.connect(self.playback.start_seeking)
        self.scb_pos.sliderReleased.connect(self.playback.seek)
        self.scb_pos.sliderMoved.connect(self.playback.slider_moved)

        # Create an action group for the language selection menu
        self.actngroup_language = QActionGroup(self.menu_lang)
        # Add all the language change actions
        self.actngroup_language.addAction(self.actn_lang_en_US)
        self.actngroup_language.addAction(self.actn_lang_pt_BR)
        # Connect the action to the handler
        self.actngroup_language.triggered.connect(self.actngroup_language_triggered)

        # Connect the exit action to the close method
        self.actn_exit.triggered.connect(self.close)

        # The action that will let the user show the input plugin to be loaded
        self.actn_load_input_plugin.triggered.connect(self.prompt_input_plugin)

        self.actn_load_analysis_plugin.triggered.connect(self.prompt_analysis_plugin)

        self.pb_loop.clicked.connect(self.set_loop)

        self.actn_new_canvas.triggered.connect(self.actn_new_canvas_triggered)


    def message_received(self, mtype, mdata, sender):
        if mtype == "UI_error_message":
            title, message = mdata.split(";")
            QMessageBox.critical(None, title, message)

    def closeEvent(self, event):
        msg = tr("MainWindow",
        "If you exit the application, all the work will be lost. Do you still wish to exit?")

        ret = QMessageBox.warning(None, tr("MainWindow", "Exit Application"),
        msg, QMessageBox.Yes | QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            for canvas in [c for c in self._canvas_list]:
                canvas.close()
            self.filter_rack_window.close()
            engine.unload_input_plugin()
            engine.unload_analysis_plugin()
            event.accept()
        else:
            event.ignore()
