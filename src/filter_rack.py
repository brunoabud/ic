from PyQt4.QtCore import (QObject, pyqtSlot, pyqtSignal)

import plugin
import log
import messages
import main

class ICFilter(object):
    def __init__(self, plugin, fid):
        self.plugin = plugin
        self.fid = fid
        self._ignore = False

    def get_ignore(self):
        return self._ignore

    def set_ignore(self, value):
        self._ignore = value
        messages.post_message('filter_ignore', {'fid': self.fid, 'ignore': value}, self)

    ignore = property(get_ignore, set_ignore)

class ICFilterRack(QObject):
    def __init__(self):
        super(ICFilterRack, self).__init__()
        self._rack = []

    def __iter__(self):
        return iter(self._rack)

    def __len__(self):
        return len(self._rack)

    def is_last(self, fid):
        #The reason to use self.get_filter is to raise an exception if an invalid
        #value is provided
        return self.get_filter_pos(fid) == len(self._rack) - 1

    def is_first(self, fid):
        return self.get_filter_pos(fid) == 0

    def is_ignored(self, fid):
        return self._rack[self.get_filter_pos(fid)].ignore


    def get_filter(self, fid):
        try:
            return [f.plugin for f in self._rack if f.fid == fid][0]
        except:
            raise ValueError("There is no filter with id {}".format(fid))

    def get_filter_at(self, pos):
        try:
            return self._rack[pos]
        except:
            raise ValueError("There is no filter at {}".format(pos))

    def get_filter_pos(self, fid):
        for (i, f) in enumerate(self._rack):
            if f.fid == fid:
                return i
        raise ValueError("There is no filter with id {}".format(fid))

    def get_next_fid(self):
        fid = 0
        used_fids = [f.fid for f in self._rack]
        while fid in used_fids:
            fid += 1
        return fid

    def load(self, plugin_name):
        try:
            p = plugin.load_plugin(main.settings['filter_dir'], plugin_name)
            f = ICFilter(p, self.get_next_fid())
            self._rack.append(f)
            messages.post_message('filter_loaded', {'plugin_name': plugin_name, 'fid': f.fid}, self)

            return f.fid
        except:
            log.dump_traceback()
            return None

    def remove(self, fid):
        try:
            pos = self.get_filter_pos(fid)
            self._rack[pos].plugin.release()
            del self._rack[pos]
            messages.post_message('filter_removed', {'fid': fid}, self)
        except:
            raise ValueError("there is no filter with id {}".format(fid))


    def move_up(self, fid):
        pos = self.get_filter_pos(fid)
        self._rack[pos], self._rack[pos - 1] = self._rack[pos - 1], self._rack[pos]
        messages.post_message('filter_up', {'fid': self._rack[pos-1].fid, 'pos': pos - 1}, self)
        messages.post_message('filter_down', {'fid': self._rack[pos].fid, 'pos': pos}, self)
        return pos - 1


    def move_down(self, fid):
        pos = self.get_filter_pos(fid)
        self._rack[pos], self._rack[pos + 1] = self._rack[pos + 1], self._rack[pos]
        messages.post_message('filter_up', {'fid': self._rack[pos].fid, 'pos': pos }, self)
        messages.post_message('filter_down', {'fid': self._rack[pos+1].fid, 'pos': pos+1}, self)
        return pos + 1

    def set_ignore(self, fid, ignore = False):
        self._rack[self.get_filter_pos(fid)].ignore = ignore


    def release(self):
        for f in self._rack:
            try:
                f.plugin.release()
            except:
                Log.dump_traceback()
        self._rack[:] = []
