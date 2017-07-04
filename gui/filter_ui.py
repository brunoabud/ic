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

from PyQt4.QtGui import QApplication, QFrame, QWidget, QSlider, QLabel
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt4.QtGui import QAbstractSlider
from PyQt4 import uic

from gui import tr, load_ui
from ic import engine
from ic import messages
from ic import settings

LOG = logging.getLogger(__name__)

class FilterUI(QFrame):
    """This class is used by the Main Window to generate gui for loaded filters.
    """
    # QT StyleSheet values used to decorate the "filter in" and "filter out"
    # colorspace labels. They are reinitialized when the ui file is loaded.
    colorspace_style = {"ok": "", "error": ""}
    def __init__(self, plugin, page):
        super(FilterUI, self).__init__()
        load_ui("ICFilterUI.ui", self)
        FilterUI.colorspace_style["ok"] = self.filter_in.styleSheet()
        FilterUI.colorspace_style["error"] = self.filter_out.styleSheet()

        self.parameters = {}
        self.plugin = plugin
        self.lbl_fid.setText("%02d" % plugin.pid)

        package = plugin.package()
        self.title.setText(package.INFO["shortname"])
        self.title.setToolTip(package.INFO["shortname"])
        self.pb_up.setEnabled(False)
        self.pb_down.setEnabled(False)
        self.name = package.INFO["shortname"]
        self.frm_parameters.setVisible(False)
        self.populate_parameters()
        self.pb_up.clicked.connect(self.pb_up_clicked)
        self.pb_down.clicked.connect(self.pb_down_clicked)
        self.pb_remove.clicked.connect(self.pb_remove_clicked)
        self.pb_ignore.clicked.connect(self.pb_ignore_clicked)
        self.filter_in.setText(package.COLORSPACE["in"])
        self.filter_out.setText(package.COLORSPACE["out"])
        self.page = page

    def update_buttons(self):
        """Update the GUI buttons.

        This method updates the up, down and ignore buttons, also it makes
        the colorspace labels gray if the filter is ignored.
        """
        page = engine.filter_rack[self.page]

        self.pb_up.setEnabled(not page.is_first(self.plugin))
        self.pb_down.setEnabled(not page.is_last(self.plugin))
        self.pb_ignore.setChecked(page.is_ignored(self.plugin))
        if page.is_ignored(self.plugin):
            self.filter_in.setStyleSheet("QLabel{\nbackground-color:qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(113, 113, 113, 255), stop:1 rgba(86, 86, 86, 255)) ;\nborder:rgb(115, 115, 115);\ncolor:rgb(50, 50, 50);\n}")
            self.filter_out.setStyleSheet("QLabel{\nbackground-color:qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(113, 113, 113, 255), stop:1 rgba(86, 86, 86, 255)) ;\nborder:rgb(115, 115, 115);\ncolor:rgb(50, 50, 50);\n}")
        else:
            input_style = FilterUI.colorspace_style[["error", "ok"][self.plugin.input_status]]
            output_style = FilterUI.colorspace_style[["error", "ok"][self.plugin.output_status]]
            self.filter_in.setStyleSheet(input_style)
            self.filter_out.setStyleSheet(output_style)

    def _add_parameter(self, param):
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
        name, title, type_, min_, max_, step, default = param

        layout = self.frm_parameters.layout()
        qtitle = QLabel(title)
        qslider = QSlider(Qt.Horizontal)
        qmin = QLabel(str(min_))
        qmax = QLabel(str(max_))
        qvalue = QLabel(str(default))
        qslider.setRange(min_, max_)
        qslider.setValue(default)
        qslider.setSingleStep(step)
        qtitle.setAlignment(Qt.AlignHCenter)
        qvalue.setAlignment(Qt.AlignHCenter)
        pos = layout.rowCount()
        layout.addWidget(qtitle, pos, 0, 1, 3)
        layout.addWidget(qmin, pos + 1, 0, 1, 1)
        layout.addWidget(qslider, pos + 1, 1, 1, 1)
        layout.addWidget(qmax, pos + 1, 2, 1, 1)
        layout.addWidget(qvalue, pos + 2, 0, 1, 3)

        def value_changed(value):
            v = self.plugin.parameter_changed(name, value)
            if v is None:
                v = value
            qvalue.setNum(v)

        qslider.valueChanged.connect(value_changed)
        qslider.setTracking(True)

        self.parameters[name] = qslider

    def populate_parameters(self):
        """Create a parameter ui for each one of the filter's parameters.
        """
        for param in self.plugin.parameters:
            self._add_parameter(param)
        if not self.plugin.parameters:
            self.pb_parameters.setEnabled(False)
            self.pb_parameters.setVisible(False)

    def pb_up_clicked(self):
        engine.filter_rack[self.page].up(self.plugin)

    def pb_down_clicked(self):
        engine.filter_rack[self.page].down(self.plugin)

    def pb_remove_clicked(self):
        engine.filter_rack[self.page].remove(self.plugin)

    def pb_ignore_clicked(self, checked):
        engine.filter_rack[self.page].ignore(self.plugin, checked)
        if checked:
            #self.title.setStyleSheet("color: red;")
            pass
        else:
            self.title.setStyleSheet("")
