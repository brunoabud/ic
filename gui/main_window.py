#coding: latin-1
import sys
import os
from os.path import join as pjoin
import logging
log = logging.getLogger(__name__)

from PyQt4.QtGui import QMainWindow, QMessageBox, QDialog, QTextCursor, QFrame
from PyQt4.QtGui import QActionGroup, QLabel, QIcon, QInputDialog

from PyQt4.QtCore import QString, QTimer, pyqtSlot
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
        elif action is self.actn_post_analysis:
            app.user_options["preview_source"] = app.OPT_PREVIEW_POST_ANALYSIS
        elif action is self.actn_filter_page:
            app.user_options["preview_source"] = app.OPT_PREVIEW_FILTER_PAGE

    def prompt_input_plugin(self, checked):
        ret, selected = PluginDialog.select_type(engine.PLUGIN_TYPE_VIDEO_INPUT)
        app = get_app()

        if ret:
            try:
                pid, plugin = engine.load_plugin(selected)
                engine.init_input_plugin(pid)
                vs = engine.get_component("video_source")
                fr = engine.get_component("filter_rack")
                color_space = vs.color_space
                page = fr.get_page("Raw")
                page.in_color  = color_space
                page.out_color = color_space
                self.update_filter_uis()
            except:
                log.exception("")
                QMessageBox.warning(None, tr("MainWindow", "Plugin Load Error"),
                tr("MainWindow", "Got an error when trying to load the input plugin"))

        return

    def update_filter_uis(self):
        layout = self.filter_rack_contents.layout()
        self.lbl_page_in.setStyleSheet("color: green;")
        self.lbl_page_out.setStyleSheet("color: green;")
        # Update buttons of the ui's
        for i in range(0, layout.count()):
            item = layout.itemAt(i)
            if isinstance(item.widget(), FilterUI):
                w = item.widget()
                w.update_buttons()
                w.filter_in.setStyleSheet("color: green;")
                w.filter_out.setStyleSheet("color: green;")

        try:
            # Get Flow Errors to correct the label colors
            page   = engine.get_component("filter_rack").get_page(get_app().user_options["filter_group"])
            self.lbl_page_in.setStyleSheet("color: green;")
            self.lbl_page_out.setStyleSheet("color: green;")
            self.lbl_page_in.setText(page.in_color)
            self.lbl_page_out.setText(page.out_color)

            errors = page.get_flow_errors()
            for err in errors:
                if err[0] is None:
                    self.lbl_page_in.setStyleSheet("color: red;")
                    i = layout.itemAt(err[1]+1)
                    if i is not None and i.widget() is not None:
                        i.widget().filter_in.setStyleSheet("color: red;")
                elif err[1] is None:
                    self.lbl_page_out.setStyleSheet("color: red;")
                    i = layout.itemAt(err[0]+1)
                    if i is not None and i.widget() is not None:
                        i.widget().filter_out.setStyleSheet("color: red;")
                else:
                    out_error = layout.itemAt(err[0]+1).widget()
                    in_error  = layout.itemAt(err[1]+1).widget()
                    out_error.filter_out.setStyleSheet("color: red;")
                    in_error.filter_in.setStyleSheet("color: red;")
        except:
            log.error("Error when checking for flow errors", exc_info=True)

    def add_filter_gui(self, pid, plugin):
        app = get_app()
        name = plugin.plugin_name
        info = [i[3] for i in engine.list_plugins() if i[1] == name][0]

        # Create the widget
        ui = FilterUI(pid, name, info["Title"], get_app().user_options["filter_group"])
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
                log.error("", exc_info=True)
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
                engine.get_component("filter_rack").get_page(get_app().user_options["filter_group"]).add(pid)
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
        self.playback = Playback()
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

        # Create an action group for the preview option
        self.actngroup_preview_source = QActionGroup(self.menu_preview_source)
        # Add all the preview source options
        self.actngroup_preview_source.addAction(self.actn_raw)
        self.actngroup_preview_source.addAction(self.actn_post_analysis)
        self.actngroup_preview_source.addAction(self.actn_filter_page)
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

        self.cb_filter_group.currentIndexChanged.connect(self.update_filter_page)



    def receive_message(self, mtype, mdata, sender_id):
        if mtype.startswith("filter_page"):
            if mtype == "filter_page_added":
                name   = mdata["name"]
                self.cb_filter_group.addItem(name)

                if self.cb_filter_group.count() == 1:
                    self.cb_filter_group.setCurrentIndex(0)

            elif mtype == "filter_page_deleted":
                name = mdata["name"]
                index = self.cb_filter_group.findText(name)
                self.cb_filter_group.removeItem(index)

        elif mtype.startswith("filter_rack") and mdata["page_name"] == get_app().user_options["filter_group"]:
            layout = self.filter_rack_contents.layout()
            if mtype == "filter_rack_up":
                pos    = mdata["old_pos"] + 1
                new    = mdata["new_pos"] + 1

                old_widget = layout.takeAt(new).widget()
                layout.insertWidget(pos, old_widget)
                self.update_filter_uis()

            elif mtype == "filter_rack_down":
                pos    = mdata["old_pos"] + 1
                new    = mdata["new_pos"] + 1

                old_widget = layout.takeAt(pos).widget()
                layout.insertWidget(new, old_widget)
                self.update_filter_uis()

            elif mtype == "filter_rack_removed":
                widget = layout.takeAt(mdata["pos"]+1).widget()
                widget.setParent(None)
                widget.deleteLater()

            elif mtype == "filter_rack_ignore":
                layout.itemAt(mdata["pos"] + 1).widget().pb_ignore.setChecked(mdata["ignore"])

    def update_filter_page(self, index):
        name     = str(self.cb_filter_group.itemText(index))
        fr       = engine.get_component("filter_rack")
        page     = fr.get_page(name)
        layout   = self.filter_rack_contents.layout()

        try:
            if get_app().user_options["filter_group"] is not None:
                cur_page = fr.get_page(get_app().user_options["filter_group"])
                length   = len(cur_page)
                # Clear the Layout
                while length > 0:
                    i = layout.takeAt(1).widget()
                    i.setParent(None)
                    i.deleteLater()
                    length -= 1
        except:
            log.error("Error when cleaning the Rack UI", exc_info=True)

        get_app().user_options["filter_group"] = name
        # Add the filters contained in the filter page
        for f in page:
            self.add_filter_gui(f.fid, engine.get_plugin(f.fid))

        self.update_filter_uis()
        self.lbl_page_in.setText(page.in_color)
        self.lbl_page_out.setText(page.out_color)

    def retranslateUi(self,):
        self.setWindowTitle(tr("MainWindow", "Imagem Cinemática", None))
        self.lbl_page_in.setToolTip(tr("MainWindow", "Input ColorSpace", None))
        self.lbl_page_in.setText(tr("MainWindow", "BGR", None))
        self.lbl_page_out.setToolTip(tr("MainWindow", "Output ColorSpace", None))
        self.lbl_page_out.setText(tr("MainWindow", "BGR", None))
        self.label.setText(tr("MainWindow", "Filter Page", None))
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
        self.actn_lang_en_US.setProperty("locale_str", tr("MainWindow", "default", None))
        self.actn_filter_page.setText(tr("MainWindow", "Filter Page", None))

    def closeEvent(self, event):
        msg = tr("MainWindow",
        "If you exit the application, all the work will be lost. Do you still wish to exit?")

        ret = QMessageBox.warning(None, tr("MainWindow", "Exit Application"),
        msg, QMessageBox.Yes | QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
