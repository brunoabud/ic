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
import sys, os
import logging

from PyQt4.QtGui import QListWidget, QListWidgetItem, QWidget, QLabel
from PyQt4.QtGui import QGridLayout, QFont, QDialog, QDialogButtonBox, QStandardItem, QStandardItemModel
from PyQt4.QtCore import QSize, Qt, QString, QStringList
from PyQt4 import uic

from gui import tr, load_ui
from ic import engine
from ic import plugin

LOG = logging.getLogger(__name__)
VersionRole = 32
AuthorRole = 33
ColorSpaceRole = 34
TypeRole = 35
PackageRole = 36

class PluginDialog(QDialog):
    @staticmethod
    def select_type(plugin_type=None):
        plugins = plugin.list_all(plugin_type)
        dialog = PluginDialog(plugins)
        ret = dialog.exec_()
        if ret == 1:
            selected = dialog.list_plugins.currentIndex()
            selected = str(dialog.list_plugins.model().data(selected, PackageRole).toPyObject())
            return (True, selected)
        else:
            return (False, None)
        return (dialog.exec_() == 1, dialog)


    def __init__(self, packages):
        super(PluginDialog, self).__init__()
        load_ui("PluginDialog.ui", self)

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.list_plugins.doubleClicked.connect(self._double_clicked)

        model = QStandardItemModel()
        for p in packages:
            item = QStandardItem(p.__name__)
            item.setData(QString(p.__name__), PackageRole)
            item.setData(QString(p.INFO["title"]), Qt.DisplayRole)
            item.setData(QString(p.INFO["description"]), Qt.ToolTipRole)
            item.setData(QStringList([p.COLORSPACE[i] for i in ["in", "out"] if i in p.COLORSPACE]), ColorSpaceRole)
            item.setData(QString(p.INFO["version"]), VersionRole)
            item.setData(QStringList(p.INFO["author"]), AuthorRole)
            item.setData(QString(p.TYPE), TypeRole)
            model.appendRow(item)

        self.list_plugins.setModel(model)
        selection = self.list_plugins.selectionModel()
        selection.currentChanged.connect(self._current_changed)

    def _double_clicked(self, index):
        self.accept()

    def _current_changed(self, current, previous):
        title, desc, color, version, author, ptype = [current.data(role).toPyObject() for role in [Qt.DisplayRole,
            Qt.ToolTipRole, ColorSpaceRole, VersionRole, AuthorRole, TypeRole]]
        self.lbl_title.setText(title)
        self.lbl_description.setText(desc)
        if ptype == "filter":
            self.lbl_output.setVisible(True)
            self.lbl_output_caption.setVisible(True)
            self.lbl_input.setVisible(True)
            self.lbl_input_caption.setVisible(True)
            self.lbl_input.setText(color[0])
            self.lbl_output.setText(color[1])
        elif ptype == "input":
            self.lbl_input.setVisible(False)
            self.lbl_input_caption.setVisible(False)
            self.lbl_output.setVisible(True)
            self.lbl_output_caption.setVisible(True)
            self.lbl_output.setText(color[0])
        elif ptype == "analysis":
            self.lbl_output.setVisible(False)
            self.lbl_output_caption.setVisible(False)
            self.lbl_input.setVisible(True)
            self.lbl_input_caption.setVisible(True)
            self.lbl_input.setText(color[0])

        self.lbl_version.setText(version)
        self.lbl_author.setText(author.join(u"\n"))

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

    def itemDoubleClicked(self, item):
        pass
