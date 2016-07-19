
from PyQt4.QtGui import QWidget

import log
import main
import messages
import filter_ui
import plugin

class ICTab_FilterRack(QWidget):
    def __init__(self, parent = None):
        super(ICTab_FilterRack, self).__init__(parent)
        messages.add_message_listener(self)
        self._filters = []

    def get_layout(self):
        return main.mainwindow.filterrack_contents.layout()

    def update_all_guis(self):
        for (fid, gui) in self._filters:
            gui.update_buttons()


    def add_filter_gui(self, fid, gui):
        layout = self.get_layout()
        layout.insertWidget(layout.count() - 2, gui)
        self._filters.append((fid, gui))
        self.update_all_guis()

    def get_filter_pos(self, fid):
        return [n for (n, i) in enumerate(self._filters) if i[0] == fid][0]

    def remove_filter_gui(self, fid):
        layout = self.get_layout()
        pos = self.get_filter_pos(fid)
        item = layout.itemAt(pos)
        layout.removeItem(item)
        self._filters[pos][1].setParent(None)
        self._filters[pos][1].deleteLater()
        del self._filters[pos]
        self.update_all_guis()

    def get_filter_gui(self, fid):
        [i for (n, i) in enumerate(self._filters) if i[0] == fid][0]

    def get_filter_at(self, pos):
        return self._filters[pos]

    def swap_filter_gui(self, fid1, fid2):
        layout     = self.get_layout()
        pos1       = self.get_filter_pos(fid1)
        pos2       = self.get_filter_pos(fid2)
        pos1, pos2 = min(pos1, pos2), max(pos1, pos2)
        i1         = layout.itemAt(pos1)
        i2         = layout.itemAt(pos2)

        i = layout.itemAt(pos2)
        layout.removeItem(i)

        layout.insertWidget(pos1, i.widget())
        i = layout.itemAt(pos1+1)
        layout.removeItem(i)
        layout.insertWidget(pos2, i.widget())

        self._filters[pos1], self._filters[pos2] = self._filters[pos2], self._filters[pos1]
        self.update_all_guis()

    def receive_message(self, message_type, message_data, sender):
        try:
            if message_type == 'filter_loaded':
                fid         = message_data['fid']
                plugin_name = message_data['plugin_name']
                info = plugin.get_plugin_info(main.settings['filter_dir'], plugin_name)
                gui = filter_ui.ICFilterUI(fid, plugin_name, info['Title'])
                self.add_filter_gui(fid, gui)
            elif message_type == 'filter_removed':
                self.remove_filter_gui(message_data['fid'])
            elif message_type == 'filter_up':
                pos = main.ic.filter_rack.get_filter_pos(message_data['fid'])
                if pos != self.get_filter_pos(message_data['fid']):
                    self.swap_filter_gui(self.get_filter_at(pos)[0], self.get_filter_at(pos+1)[0])
            elif message_type == 'filter_down':
                pos = main.ic.filter_rack.get_filter_pos(message_data['fid'])
                if pos != self.get_filter_pos(message_data['fid']):
                    self.swap_filter_gui(self.get_filter_at(pos)[0], self.get_filter_at(pos-1)[0])
            elif message_type == 'filter_ignore':
                self.update_all_guis()
        except:
            log.dumptraceback()
