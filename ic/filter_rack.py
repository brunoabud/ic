
from gui.application import get_app

class FilterElement(object):
    def __init__(self, fid):
        self.fid = fid
        self.ignore = False

class FilterRack(object):
    """Manages a list of Filter Plugins id's that will be applied to the frames.

    This class contains a list of Filter Plugin ids that can have their positions
    changed and can be removed or ignored.
    This list is used at the filtering stage when each filter will be applied
    to a frame sequentially.

    """

    def __init__(self):
        self.flist = []
        app = get_app()

        self.m_id = app.register_message_listener(self)

    def receive_message(self, mtype, mdata, sender):
        if mtype == "plugin_unloaded":
            if mdata["id"] in self.id_list():
                self.remove(mdata["id"])


    def id_list(self):
        return [f.fid for f in self.flist]

    def add(self, fid):
        if fid not in self.id_list():
            self.flist.append(FilterElement(fid))
            get_app().post_message("filter_rack_added", {"id": fid, "pos": len(self.flist) - 1}, self.m_id)
        else:
            raise ValueError("Filter ID already in the list")

    def remove(self, fid):
        pos = self.filter_pos(fid)
        del self.flist[pos]
        get_app().post_message("filter_rack_removed", {"id": fid, "pos": pos}, self.m_id)

    def __iter__(self):
        return iter(self.flist)

    def filter_pos(self, fid):
        for (i, f) in enumerate(self.flist):
            if f.fid == fid:
                return i
        raise ValueError("Filter ID not in the list")

    def up(self, fid):
        pos = self.filter_pos(fid)
        if pos > 0:
            self.flist[pos - 1], self.flist[pos] = self.flist[pos], self.flist[pos - 1]
            get_app().post_message("filter_rack_up", {"id": fid, "old_pos": pos, "new_pos": pos-1}, self.m_id)
            return pos - 1
        else:
            raise IndexError("Cannot up filter at the beggining of the list")

    def down(self, fid):
        pos = self.filter_pos(fid)
        if pos < len(self.flist) - 1:
            self.flist[pos + 1], self.flist[pos] = self.flist[pos], self.flist[pos + 1]
            get_app().post_message("filter_rack_down", {"id": fid, "old_pos": pos, "new_pos": pos+1}, self.m_id)
            return pos + 1
        else:
            raise IndexError("Cannot down filter at end of the list")

    def ignore(self, fid, ignore = True):
        pos = self.filter_pos(fid)
        self.flist[pos].ignore = ignore
        get_app().post_message("filter_rack_ignore", {"id": fid, "ignore": ignore, "pos": pos}, self.m_id)

    def is_last(self, fid):
        return self.filter_pos(fid) == len(self.flist) - 1

    def is_first(self, fid):
        return self.filter_pos(fid) == 0

    def is_ignored(self, fid):
        pos = self.filter_pos(fid)
        return self.flist[pos].ignore
