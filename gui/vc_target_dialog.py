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

from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtGui import QDialog, QStandardItem, QStandardItemModel, QActionGroup
from PyQt4.QtCore import QModelIndex

from gui import tr
from ic import engine
from ic import settings


TargetRole = 33
DisableBeforeRole = 34

class VCTargetDialog(QDialog):
    def __init__(self, parent=None):
        super(VCTargetDialog, self).__init__(parent)
        uic.loadUi(os.path.join(settings.get("resources_dir"), "ui", "VCTargetDialog.ui"), self)

        model = QStandardItemModel()
        self.rb_before.toggled.connect(self._toggled)

        raw_item = QStandardItem("From Input")
        raw_item.setData("filter_page:Raw;before", TargetRole)
        raw_item.setData(True, DisableBeforeRole)
        model.appendRow(raw_item)

        for page in engine.filter_rack.pages:
            page_item = QStandardItem("Filter Page [%s]" % page)
            page_item.setData("filter_page:%s;" % page, TargetRole)
            page_item.setData(False, DisableBeforeRole)
            for f in engine.filter_rack[page]:
                filter_item = QStandardItem("Filter ID %d - %s" % (f.pid, f.shortname))
                filter_item.setData("filter_id:%d;" % f.pid, TargetRole)
                filter_item.setData(False, DisableBeforeRole)
                page_item.appendRow(filter_item)
            model.appendRow(page_item)

        analysis_item = QStandardItem("After Analysis")
        analysis_item.setData("processed", TargetRole)
        analysis_item.setData(True, DisableBeforeRole)
        model.appendRow(analysis_item)

        self.tv_targets.setModel(model)
        self.tv_targets.activated.connect(self._activated)

        selection = self.tv_targets.selectionModel()
        selection.currentChanged.connect(self._current_changed)


    def _toggled(self, checked):
        t = str(self.le_identifier.text())
        if checked:
            if not t.endswith("before"):
                self.le_identifier.setText(t+"before")
        else:
            if t.endswith("before"):
                self.le_identifier.setText(t[:-6])

    def _activated(self, index):
        if self.tv_targets.model().data(index, DisableBeforeRole).toPyObject() == False:
            target = self.le_identifier.text() + "before" if self.rb_before.isChecked() else ''

    def _current_changed(self, current, previous):
        self.le_identifier.setText(self.tv_targets.model().data(current, TargetRole).toPyObject())
        disable = self.tv_targets.model().data(current, DisableBeforeRole).toPyObject()
        self.rb_before.setEnabled(not disable)
        self.rb_after.setEnabled(not disable)
        if not disable:
            self._toggled(self.rb_before.isChecked())

