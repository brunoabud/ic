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

from PyQt4.QtGui import QApplication, QFrame, QWidget, QSlider, QLabel
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt4.QtGui import QAbstractSlider
from PyQt4 import uic

from gui.application import get_app
from gui import tr
from ic import engine
from ic.engine import get_engine

LOG = logging.getLogger(__name__)

class FilterUI(QFrame):
    """This class is used by the Main Window to generate gui for loaded filters.
    """
    # QT StyleSheet values used to decorate the "filter in" and "filter out"
    # colorspace labels. They are reinitialized when the ui file is loaded.
    COLORSPACE_OK = ""
    COLORSPACE_ERROR = ""

    def __init__(self, fid, name, title, page_name, parent = None):
        super(FilterUI, self).__init__(parent)
        app = get_app()
        app.load_ui("", "ICFilterUI.ui", self)
        FilterUI.COLORSPACE_OK = self.filter_in.styleSheet()
        FilterUI.COLORSPACE_ERROR = self.filter_out.styleSheet()
        self.parameters = {}
        self.lbl_fid.setText("%02d" % fid)
        self.title.setText(title)
        self.title.setToolTip(title)
        self.pb_up.setEnabled(False)
        self.pb_down.setEnabled(False)
        self.name = name
        self.fid = fid
        self.frm_parameters.setVisible(False)
        self.populate_parameters()
        self.pb_up.clicked.connect(self.pb_up_clicked)
        self.pb_down.clicked.connect(self.pb_down_clicked)
        self.pb_remove.clicked.connect(self.pb_remove_clicked)
        self.pb_ignore.clicked.connect(self.pb_ignore_clicked)
        self.page_name = page_name
        page = get_engine().get_component("filter_rack").get_page(page_name)
        filter_ = page.get_filter(fid)
        self.filter_in.setText(filter_.in_color)
        self.filter_out.setText(filter_.out_color)

    def update_buttons(self):
        """Update the GUI buttons.

        This method updates the up, down and ignore buttons, also it makes
        the colorspace labels gray if the filter is ignored.
        """
        page = get_engine().get_component("filter_rack").get_page(self.page_name)
        self.pb_up.setEnabled(not page.is_first(self.fid))
        self.pb_down.setEnabled(not page.is_last(self.fid))
        self.pb_ignore.setChecked(page.is_ignored(self.fid))
        if page.is_ignored(self.fid):
            self.filter_in.setStyleSheet("QLabel{\nbackground-color:qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(113, 113, 113, 255), stop:1 rgba(86, 86, 86, 255)) ;\nborder:rgb(115, 115, 115);\ncolor:rgb(50, 50, 50);\n}")
            self.filter_out.setStyleSheet("QLabel{\nbackground-color:qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(113, 113, 113, 255), stop:1 rgba(86, 86, 86, 255)) ;\nborder:rgb(115, 115, 115);\ncolor:rgb(50, 50, 50);\n}")

    def _add_parameter(self, name, parameter_data, parameter_change):
        """Add a new parameter controller to the gui.

        Add a new Slider that will change a filter parameter when the user
        interacts with the widget.

        Args:
          name (str): The name of the parameter.
          parameter_data(str): The parameter's data given by the plugin: min,
            max, default and title values.
          parameter_change (function): Function that will be called to correct
            the value returned by the widget.
        """
        layout = self.frm_parameters.layout()
        qtitle = QLabel(parameter_data[3])
        qslider = QSlider(Qt.Horizontal)
        qmin = QLabel(str(parameter_data[0]))
        qmax = QLabel(str(parameter_data[1]))
        qvalue = QLabel(str(parameter_data[2]))
        qslider.setRange(parameter_data[0], parameter_data[1])
        qslider.setValue(parameter_data[2])
        qtitle.setAlignment(Qt.AlignHCenter)
        qvalue.setAlignment(Qt.AlignHCenter)
        pos = layout.rowCount()
        layout.addWidget(qtitle, pos, 0, 1, 3)
        layout.addWidget(qmin, pos + 1, 0, 1, 1)
        layout.addWidget(qslider, pos + 1, 1, 1, 1)
        layout.addWidget(qmax, pos + 1, 2, 1, 1)
        layout.addWidget(qvalue, pos + 2, 0, 1, 3)

        def value_changed(value):
            v = parameter_change(name, value)
            qvalue.setNum(v)

        qslider.valueChanged.connect(value_changed)
        qslider.setTracking(True)

        self.parameters[name] = qslider

    def populate_parameters(self):
        """Create a parameter ui for each one of the filter's parameters.
        """
        plugin = get_engine().get_plugin(self.fid)
        for name in plugin.instance.parameters:
            self._add_parameter(name, plugin.instance.parameters[name], plugin.instance.parameter_change)
        if not plugin.instance.parameters:
            self.pb_parameters.setEnabled(False)
            self.pb_parameters.setVisible(False)

    def pb_up_clicked(self):
        get_engine().get_component("filter_rack").get_page(self.page_name).up(self.fid)

    def pb_down_clicked(self):
        get_engine().get_component("filter_rack").get_page(self.page_name).down(self.fid)

    def pb_remove_clicked(self):
        get_engine().get_component("filter_rack").get_page(self.page_name).remove(self.fid)
        get_engine().unload_plugin(self.fid)

    def pb_ignore_clicked(self, checked):
        get_engine().get_component("filter_rack").get_page(self.page_name).ignore(self.fid, checked)
        if checked:
            self.title.setStyleSheet("color: red;")
        else:
            self.title.setStyleSheet("")
