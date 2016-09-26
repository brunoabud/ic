#coding: latin-1
import sys
import os
from os.path import join as pjoin
import logging
log = logging.getLogger(__name__)


from PyQt4.QtGui import QMainWindow, QMessageBox, QDialog, QTextCursor, QFrame
from PyQt4.QtGui import QActionGroup, QLabel, QIcon, QInputDialog

from PyQt4.QtCore import QString, QTimer
from PyQt4 import uic
import cv2

from application import get_app, Application
from gui import tr
from gui.plugin_dialog import PluginDialog
from gui.playback import Playback
from gui.filter_ui import FilterUI
from ic import engine

class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        app = get_app()

        #Register this class to the messages system
        self.m_id = app.register_message_listener(self)

    def actn_load_input_plugin_triggered(self, checked):
        pass

    def actngroup_language_triggered(self, action):
        try:
            locale_str = str(action.property("locale_str").toString())
            get_app().set_language(locale_str)
        except:
            log.exception("")
            QMessageBox.warning(None, tr("MainWindow", "Language Error"),

            tr("MainWindow",
            "Could not set the language to '%1', missing language file."
            ).arg(locale_str))

    def actngroup_preview_source_triggered(self, action):
        app = get_app()
        if action is self.actn_raw:
            app.user_options["preview_source"] = app.OPT_PREVIEW_RAW
        elif action is self.actn_post_filter:
            app.user_options["preview_source"] = app.OPT_PREVIEW_POST_FILTER
        elif action is self.actn_post_analysis:
            app.user_options["preview_source"] = app.OPT_PREVIEW_POST_ANALYSIS

    def prompt_input_plugin(self, checked):
        ret, selected = PluginDialog.select_type(engine.PLUGIN_TYPE_VIDEO_INPUT)
        app = get_app()

        if ret:
            try:
                pid, plugin = engine.load_plugin(selected)
                engine.init_input_plugin(pid)
            except:
                log.exception("")
                QMessageBox.warning(None, tr("MainWindow", "Plugin Load Error"),
                tr("MainWindow", "Got an error when trying to load the input plugin"))

        return

    def update_filter_uis(self):
        layout = self.filter_rack_contents.layout()
        # Update buttons of the ui's
        for i in range(0, layout.count()):
            item = layout.itemAt(i)
            if isinstance(item.widget(), FilterUI):
                item.widget().update_buttons()

    def add_filter_gui(self, pid, plugin):
        app = get_app()
        name = plugin.plugin_name
        info = [i[3] for i in engine.list_plugins() if i[1] == name][0]

        # Create the widget
        ui = FilterUI(pid, name, info["Title"])
        layout = self.filter_rack_contents.layout()
        layout.insertWidget(layout.count() - 2, ui)

        self.update_filter_uis()

    def prompt_analysis_plugin(self, checked):
        ret, selected = PluginDialog.select_type(engine.PLUGIN_TYPE_ANALYSIS)
        if ret:
            try:
                pid, plugin = engine.load_plugin(selected)
                engine.init_analysis_plugin(pid)
            except:
                log.exception("")
                QMessageBox.warning(None, tr("MainWindow", "Plugin Load Error"),
                tr("MainWindow", "Got an error when trying to load the analysis plugin"))

        return


    def prompt_filter_plugin(self, checked):
        ret, selected = PluginDialog.select_type(engine.PLUGIN_TYPE_FILTER)
        app = get_app()
        vs = engine.get_component("video_source")
        fs = engine.get_component("frame_stream")
        if ret:
            try:
                pid, plugin = engine.load_plugin(selected)
                engine.get_component("filter_rack").add(pid)
                # Create the GUI
                self.add_filter_gui(pid, plugin)
            except:
                log.exception("")
                QMessageBox.warning(None, tr("MainWindow", "Plugin Load Error"),
                tr("MainWindow", "Got an error when trying to load the filter plugin"))

        return


    def set_loop(self, loop):
        engine.get_component("frame_stream").loop = loop

    def setupUi(self):
        # Create the Playback object that will take care of the preview and
        # playback gui
        self.playback = Playback(self)

        # Create an action group for the language selection menu
        self.actngroup_language = QActionGroup(self.menu_lang)
        # Add all the language change actions
        self.actngroup_language.addAction(self.actn_lang_en_US)
        self.actngroup_language.addAction(self.actn_lang_pt_BR)
        # Connect the action to the handler
        self.actngroup_language.triggered.connect(self.actngroup_language_triggered)

        # Create an action group for the preview option
        self.actngroup_preview_source = QActionGroup(self.menu_preview_source)
        # Add all the preview source options
        self.actngroup_preview_source.addAction(self.actn_raw)
        self.actngroup_preview_source.addAction(self.actn_post_filter)
        self.actngroup_preview_source.addAction(self.actn_post_analysis)
        # Connect the action to the handler
        self.actngroup_preview_source.triggered.connect(self.actngroup_preview_source_triggered)

        # Connect the exit action to the close method
        self.actn_exit.triggered.connect(self.close)

        # The action that will let the user show the input plugin to be loaded
        self.actn_load_input_plugin.triggered.connect(self.prompt_input_plugin)

        self.pb_add_filter.clicked.connect(self.actn_add_filter.trigger)
        self.actn_add_filter.triggered.connect(self.prompt_filter_plugin)


        self.actn_load_analysis_plugin.triggered.connect(self.prompt_analysis_plugin)

        self.pb_loop.clicked.connect(self.set_loop)

    def receive_message(self, mtype, mdata, sender_id):
        layout = self.filter_rack_contents.layout()
        if mtype == "filter_rack_up":
            pos    = mdata["old_pos"]
            new    = mdata["new_pos"]

            old_widget = layout.takeAt(new).widget()
            layout.insertWidget(pos, old_widget)
            self.update_filter_uis()

        elif mtype == "filter_rack_down":
            pos    = mdata["old_pos"]
            new    = mdata["new_pos"]

            old_widget = layout.takeAt(pos).widget()
            layout.insertWidget(new, old_widget)
            self.update_filter_uis()
        elif mtype == "filter_rack_removed":
            widget = layout.takeAt(mdata["pos"]).widget()
            widget.setParent(None)
            widget.deleteLater()
        elif mtype == "filter_rack_ignore":
            layout.itemAt(mdata["pos"]).widget().pb_ignore.setChecked(mdata["ignore"])

    def retranslateUi(self):
        self.setWindowTitle(tr("MainWindow", "Imagem Cinemática"))
        self.toolstab.setTabText(self.toolstab.indexOf(self.tab_filterrack), tr("MainWindow", "Filter Rack", None))
        self.maintab.setTabText(self.maintab.indexOf(self.tab_preview), tr("MainWindow", "Preview", None))
        self.menu_preview.setTitle(tr("MainWindow", "Preview", None))
        self.menu_preview_source.setTitle(tr("MainWindow", "Preview source", None))
        self.menu_video.setTitle(tr("MainWindow", "Video", None))
        self.menu_analysis.setTitle(tr("MainWindow", "Analysis", None))
        self.menu_console.setTitle(tr("MainWindow", "Console", None))
        self.toolbar.setWindowTitle(tr("MainWindow", "Toolbar", None))
        self.actn_raw.setText(tr("MainWindow", "Raw", None))
        self.actn_post_filter.setText(tr("MainWindow", "Post-Filter", None))
        self.actn_post_analysis.setText(tr("MainWindow", "Post-Analysis", None))
        self.actn_load_input_plugin.setText(tr("MainWindow", "Load Input Plugin", None))
        self.actn_new_analysis.setText(tr("MainWindow", "New Analysis", None))
        self.actn_new_analysis.setToolTip(tr("MainWindow", "Create a new Analysis", None))
        self.actn_new_analysis.setShortcut(tr("MainWindow", "Ctrl+N", None))
        self.actn_exit.setText(tr("MainWindow", "Exit", None))
        self.actn_exit.setToolTip(tr("MainWindow", "Exit from application", None))
        self.actn_add_filter.setText(tr("MainWindow", "Add Filter", None))
        self.actn_load_analysis_plugin.setText(tr("MainWindow", "Load Analysis Plugin", None))
        self.actn_show_console.setText(tr("MainWindow", "Show console", None))

    def closeEvent(self, event):
        msg = tr("MainWindow",
        "If you exit the application, all the work will be lost. Do you still wish to exit?")

        ret = QMessageBox.warning(None, tr("MainWindow", "Exit Application"),
        msg, QMessageBox.Yes | QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
