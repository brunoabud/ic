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
import sys, os

from PyQt4.QtGui import QListWidget, QListWidgetItem, QWidget, QLabel
from PyQt4.QtGui import QGridLayout, QFont, QDialog, QDialogButtonBox
from PyQt4.QtCore import QSize
from PyQt4 import uic

from application import get_app
from gui import tr
from ic import engine
from ic.engine import get_engine


class ListPlugin(QListWidget):
    def __init__(self, parent = None):
        super(ListPlugin, self).__init__(parent)

    def populate(self, plugin_infos):
        app = get_app()
        for ptype, pname, ppath, pinfo in plugin_infos:
            widget = app.load_ui("", "pluginDialogItem.ui")
            widget.title.setText(tr(pname, pinfo['Title']))
            widget.author.setText(tr(pname, pinfo['Author']))
            widget.description.setText(tr(pname, pinfo['Description']))
            widget.version.setText(pinfo['Version'])
            widget.setObjectName(pname)
            widget.adjustSize()
            item = QListWidgetItem('', self)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)

class PluginDialog(QDialog):
    @staticmethod
    def select_type(plugin_type = engine.PLUGIN_TYPE_ANY):
        app = get_app()
        plugins = get_engine().list_plugins(plugin_type)
        dialog = PluginDialog()
        dialog.list_plugins.populate(plugins)
        return (dialog.exec_() == 1, dialog.selected)

    def __init__(self):
        super(PluginDialog, self).__init__()
        app = get_app()

        app.load_ui("", "pluginDialog.ui", self)

        self.selected = None
        self.buttonbox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.list_plugins.currentItemChanged.connect(self.currentItemChanged)
        self.list_plugins.itemDoubleClicked.connect(self.itemDoubleClicked)

    def currentItemChanged(self, current, previous):
        widget = self.list_plugins.itemWidget(current)
        self.selected = str(widget.objectName())
        self.buttonbox.button(QDialogButtonBox.Ok).setEnabled(True)

    def itemDoubleClicked(self, item):
        widget = self.list_plugins.itemWidget(item)
        self.selected = str(widget.objectName())
        self.accept()
