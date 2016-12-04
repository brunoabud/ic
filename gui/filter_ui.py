import os
import sys
import logging
log = logging.getLogger(__name__)

from PyQt4.QtGui import QApplication, QFrame, QWidget, QSlider, QLabel
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt4.QtGui import QAbstractSlider
from PyQt4 import uic

from gui.application import get_app
from gui import tr
from ic import engine


class FilterUI(QFrame):
    def __init__(self, fid, name, title, page_name, parent = None):
        super(FilterUI, self).__init__(parent)
        app = get_app()
        app.load_ui("", "ICFilterUI.ui", self)

        self.parameters = {}
        self.lbl_fid.setNum(fid)
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

        page = engine.get_component("filter_rack").get_page(page_name)
        filter_ = page.get_filter(fid)

        self.filter_in.setText(filter_.in_color)
        self.filter_out.setText(filter_.out_color)


    def update_buttons(self):
        page = engine.get_component("filter_rack").get_page(self.page_name)
        self.pb_up.setEnabled(not page.is_first(self.fid))
        self.pb_down.setEnabled(not page.is_last(self.fid))
        self.pb_ignore.setChecked(page.is_ignored(self.fid))

    def add_parameter(self, name, parameter_data, parameter_change):
        layout = self.frm_parameters.layout()
        qtitle = QLabel(parameter_data[3]); qslider = QSlider(Qt.Horizontal);
        qmin = QLabel(str(parameter_data[0])); qmax = QLabel(str(parameter_data[1]))
        qvalue = QLabel(str(parameter_data[2]));
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
        plugin = engine.get_plugin(self.fid)
        for name in plugin.instance.parameters:
            self.add_parameter(name, plugin.instance.parameters[name], plugin.instance.parameter_change)

    def pb_up_clicked(self):
        engine.get_component("filter_rack").get_page(self.page_name).up(self.fid)

    def pb_down_clicked(self):
        engine.get_component("filter_rack").get_page(self.page_name).down(self.fid)

    def pb_remove_clicked(self):
        engine.get_component("filter_rack").get_page(self.page_name).remove(self.fid)
        engine.unload_plugin(self.fid)
    def pb_ignore_clicked(self, checked):
        engine.get_component("filter_rack").get_page(self.page_name).ignore(self.fid, checked)
