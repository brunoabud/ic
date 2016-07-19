#encoding: utf-8
import sys
import os
from os.path import join as pjoin

from PyQt4.QtGui import QMainWindow, QMessageBox, QDialog, QTextCursor, QFrame
from PyQt4.QtGui import QActionGroup, QLabel, QIcon
from PyQt4.QtCore import QString, QTimer
from PyQt4 import uic

from plugin_dialog import ICPluginDialog
from gui_interface import ICGUI_Interface
from filter_ui import ICFilterUI
from analysis import PreviewOption
import main
import messages
import plugin
import log


#Callbacks for the Filter GUI Buttons
class LogListener(object):
    def __init__(self, out):
        self.out = out
    def write(self, text):
        try:
            self.out.insertPlainText(QString(str(text).replace('\\n', '\n')))
            self.out.moveCursor(QTextCursor.End)
        except:
            pass


class ICMainWindow(QMainWindow):
    def load_input_plugin(self, name):
        try:
            ret = main.ic.open_VIMO(ICGUI_Interface(self), name)
        except:
            log.dump_traceback()

    def load_analysis_plugin(self, name):
        try:
            ret = main.ic.open_VAMO(ICGUI_Interface(self), name)
        except:
            Log.dump_traceback()

    def receive_message(self, message_type, message_data, sender):
        if message_type == 'input_plugin_loaded':
            self.actn_close_input_plugin.setEnabled(True)
        elif message_type == 'input_plugin_closed':
            self.actn_close_input_plugin.setEnabled(False)
        elif message_type == 'analysis_plugin_loaded':
            self.actn_close_analysis_plugin.setEnabled(True)
        elif message_type == 'analysis_plugin_closed':
            self.actn_close_analysis_plugin.setEnabled(False)

    def actn_load_input_plugin_triggered(self, checked):
        ret, selected = ICPluginDialog.select_from_dir(main.settings['video_dir'])
        if ret:
            self.load_input_plugin(selected)

    def actn_close_input_plugin_triggered(self, checked):
        try:
            Main.ic.closeVIMO()
        except:
            Log.dump_traceback()

    def actn_load_analysis_plugin_triggered(self, checked):
        ret, selected = ICPluginDialog.select_from_dir(main.settings['analysis_dir'])
        if ret:
            self.load_analysis_plugin(selected)

    def actn_close_analysis_plugin_triggered(self, checked):
        try:
            main.ic.close_VAMO()
        except:
            log.dump_traceback()

    def agp_preview_source_triggered(self, action):
        if action is self.actn_raw:
            main.ic.preview = PreviewOption.Raw
        elif action is self.actn_post_filter:
            main.ic.preview = PreviewOption.PostFiltering
        elif action is self.actn_post_analysis:
            main.ic.preview = PreviewOption.PostProcessing

    def actn_add_filter_triggered(self, checked):
        ret, selected = ICPluginDialog.select_from_dir(main.settings['filter_dir'])
        if ret:
            main.ic.filter_rack.load(selected)

    def __init__(self, parent = None):
        super(ICMainWindow, self).__init__(parent)
        uic.loadUi(pjoin(main.settings['ui_dir'], 'ICMainWindow.ui'), self)
        self.log = LogListener(self.txt_console)
        log.add_output(self.log)

        messages.add_message_listener(self)

        self.agp_preview_source = QActionGroup(self.menu_preview_source)
        self.agp_preview_source.addAction(self.actn_raw)
        self.agp_preview_source.addAction(self.actn_post_filter)
        self.agp_preview_source.addAction(self.actn_post_analysis)
        self.agp_preview_source.triggered.connect(self.agp_preview_source_triggered)

        self.actn_load_input_plugin.triggered.connect(self.actn_load_input_plugin_triggered)
        self.actn_close_input_plugin.triggered.connect(self.actn_close_input_plugin_triggered)
        self.actn_load_analysis_plugin.triggered.connect(self.actn_load_analysis_plugin_triggered)
        self.actn_close_analysis_plugin.triggered.connect(self.actn_close_analysis_plugin_triggered)

        self.pb_add_filter.clicked.connect(self.actn_add_filter.trigger)
        self.actn_add_filter.triggered.connect(self.actn_add_filter_triggered)
        self.load_input_plugin('ICFile')

    def closeEvent(self, event):
        main.ic.release()
