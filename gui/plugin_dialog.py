import sys, os

from PyQt4.QtGui import QListWidget, QListWidgetItem, QWidget, QLabel
from PyQt4.QtGui import QGridLayout, QFont, QDialog, QDialogButtonBox
from PyQt4.QtCore import QSize
from PyQt4 import uic

from application import get_app, Application
from gui import tr

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
    def select_type(plugin_type = Application.PLUGIN_TYPE_ANY):
        app = get_app()
        plugins = app.list_plugins(plugin_type)
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
