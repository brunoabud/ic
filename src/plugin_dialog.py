import sys, os

from PyQt4.QtGui import QListWidget, QListWidgetItem, QWidget, QLabel
from PyQt4.QtGui import QGridLayout, QFont, QDialog, QDialogButtonBox
from PyQt4.QtCore import QSize
from PyQt4 import uic

import main
import plugin


class ICListPlugin(QListWidget):
    def __init__(self, parent = None):
        super(ICListPlugin, self).__init__(parent)

    def populate(self, plugin_infos):
        for info in plugin_infos:
            uipath = str(main.settings['ui_dir'])
            uipath = os.path.join(uipath+'/ICPluginWidgetListItem.ui')
            widget = uic.loadUi(uipath)
            widget.title.setText(info['Title'])
            widget.author.setText(info['Author'])
            widget.description.setText(info['Description'])
            widget.version.setText(info['Version'])
            widget.setObjectName(info['name'])
            widget.adjustSize()
            item = QListWidgetItem('', self)
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)

class ICPluginDialog(QDialog):
    @staticmethod
    def select_from_dir(path, plugin_type = plugin.PluginType.Any):
        names = plugin.list_plugins(path, plugin_type)
        dialog = ICPluginDialog()
        dialog.list_plugins.populate([plugin.get_plugin_info(path, n) for n in names])
        return (dialog.exec_() == 1, dialog.selected)

    def __init__(self):
        super(ICPluginDialog, self).__init__()
        uipath = str(main.settings['ui_dir'])
        uipath = os.path.join(uipath+'/ICPluginDialog.ui')
        uic.loadUi(uipath, self)
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
