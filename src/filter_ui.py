import os, sys

from PyQt4.QtGui import QApplication, QFrame, QWidget, QSlider, QLabel
from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt4.QtGui import QAbstractSlider
from PyQt4 import uic

import main



class ICFilterUI(QFrame):
    def __init__(self, fid, name, title, parent = None):
        super(ICFilterUI, self).__init__(parent)
        uic.loadUi(os.path.join(main.settings['ui_dir'], 'ICFilterUI.ui'), self)
        self.parameters = {}
        self.lbl_fid.setNum(fid)
        self.title.setText(title)
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


    def update_buttons(self):
        self.pb_up.setEnabled(not main.ic.filter_rack.is_first(self.fid))
        self.pb_down.setEnabled(not main.ic.filter_rack.is_last(self.fid))
        self.pb_ignore.setChecked(main.ic.filter_rack.is_ignored(self.fid))

    def add_parameter(self, name, parameter):
        layout = self.frm_parameters.layout()
        qtitle = QLabel(parameter['title']); qslider = QSlider(Qt.Horizontal);
        qmin = QLabel(str(parameter['min'])); qmax = QLabel(str(parameter['max']))
        qvalue = QLabel(str(parameter['value'])); qslider.setRange(parameter['min'], parameter['max'])
        qslider.setValue(parameter['value'])
        qtitle.setAlignment(Qt.AlignHCenter)
        qvalue.setAlignment(Qt.AlignHCenter)
        pos = layout.rowCount()
        layout.addWidget(qtitle, pos, 0, 1, 3)
        layout.addWidget(qmin, pos + 1, 0, 1, 1)
        layout.addWidget(qslider, pos + 1, 1, 1, 1)
        layout.addWidget(qmax, pos + 1, 2, 1, 1)
        layout.addWidget(qvalue, pos + 2, 0, 1, 3)

        parameter['lblSlot'] = qvalue.setNum
        qslider.valueChanged.connect(parameter['paramSlot'])
        qslider.setTracking(True)
        self.parameters[name] = qslider

    def populate_parameters(self):
        plugin = main.ic.filter_rack.get_filter(self.fid)
        for parameter in plugin.parameters:
            self.add_parameter(parameter, plugin.parameters[parameter])

    def pb_up_clicked(self):
        main.ic.filter_rack.move_up(self.fid)

    def pb_down_clicked(self):
        main.ic.filter_rack.move_down(self.fid)

    def pb_remove_clicked(self):
        main.ic.filter_rack.remove(self.fid)

    def pb_ignore_clicked(self, checked):
        main.ic.filter_rack.set_ignore(self.fid, checked)
