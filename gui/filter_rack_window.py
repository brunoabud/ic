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

from PyQt4 import uic
from PyQt4.QtGui import QMainWindow, QLabel, QSizePolicy, QInputDialog
from PyQt4.QtCore import QFile, QString, QTextStream
import logging

from ic import settings
from ic import messages
from gui import load_ui, tr
from gui.flow_widget import FlowWidget
from ic import engine
from gui.plugin_dialog import PluginDialog
from gui.filter_ui import FilterUI


LOG = logging.getLogger(__name__)

class FilterRackWindow(QMainWindow):
    def __init__(self, main_window):
        super(FilterRackWindow, self).__init__()
        load_ui("FilterRack.ui", self)
        self._main = main_window

        messages.register(self)
        self._set_page("Raw")

        self.setupUi()

    def _load_style(self, tag):
        qss_file = QFile(":/style/%s" % tag)
        if qss_file.open(QFile.ReadOnly | QFile.Text):
            contents = QTextStream(qss_file).readAll()
            qss_file.close()
            return contents
        else:
            raise IOError

    def _set_page(self, page):
        try:
            fr = engine.filter_rack
            p = fr[page]

            self.filters_flow.clear()
            for filter_plugin in p:
                self.filters_flow.add_item(FilterUI(filter_plugin, page))

            self._page = page
            self.setWindowTitle("Filter Rack [%s]" % page)
        except:
            LOG.error("Could not set page", exc_info=True)

    def setupUi(self):
        def create_label(s):
            lbl = QLabel(s)
            lbl.setStyleSheet(self._load_style("filter_ui_ok"))
            return lbl
        # The label used that represents the Input Colorspace of the Filter Page
        input_label = create_label("BGR")
        output_label = create_label("BGR")
        self.filters_flow.set_header(input_label)
        self.filters_flow.set_footer(output_label)

        self.input_label = input_label
        self.output_label = input_label

        self.actn_insert_filter.triggered.connect(self.actn_insert_filter_triggered)
        self.actn_select_filter_page.triggered.connect(self.actn_select_filter_page_triggered)

    def actn_select_filter_page_triggered(self, checked):
        pages = []
        current = -1
        i = 0
        for page in engine.filter_rack.pages:
            pages.append(page)
            if page == self._page:
                current = i
            i += 1

        item, ret= QInputDialog.getItem(None,
                tr("FilterRackWindow", "Filter Page"),
                tr("FilterRackWindow", "Select a Filter Page from the list"),
                pages,
                current,
                editable=False)
        if ret:
            self._set_page(str(item))


    def actn_insert_filter_triggered(self, checked):
        ret, selected = PluginDialog.select_type("filter")
        if ret:
            engine.load_filter_plugin(selected, self._page)

    def _update(self):
        input_style = self._load_style(["filter_ui_error", "filter_ui_ok"][engine.filter_rack[self._page].input_status])
        output_style = self._load_style(["filter_ui_error", "filter_ui_ok"][engine.filter_rack[self._page].output_status])
        self.input_label.setStyleSheet(input_style)
        self.output_label.setStyleSheet(output_style)

        for i in self.filters_flow:
            i.update_buttons()

    def message_received(self, message_type, message_data, sender):
        if message_type == "FR_page_removed":
            if message_data == self._page:
                self._set_page("Raw")
                self._update()
        elif message_type == "FR_filter_added":
            page, plugin_id = message_data.split(";")
            if page == self._page:
                self.filters_flow.add_item(FilterUI(engine.filter_rack[page].get_filter(int(plugin_id)), page))
                self._update()
        elif message_type == "FR_filter_removed":
            page, old_pos = message_data.split(";")
            if page == self._page:
                self.filters_flow.remove_item(int(old_pos))
                self._update()
        elif message_type == "FR_filter_swapped":
            page, pos1, pos2 = message_data.split(";")
            if page == self._page:
                self.filters_flow.swap_items(int(pos1), int(pos2))
                self._update()
        elif message_type == "FR_filter_ignore_changed":
            page, pos, ignore = message_data.split(";")
            if page == self._page:
                self._update()
        elif message_type == "ENGINE_source_opened":
            self._update()
