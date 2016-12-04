from os.path import join
from logging import getLogger
log = getLogger(__name__)
from xml.dom import minidom, Node

from gui.application import get_app
from ic import engine
import cv2

class InvalidColorSpace(Exception):
    pass

class WrongColorSpace(Exception):
    pass

class FilterPageFlowError(Exception):
    pass

class FilterElement(object):
    def __init__(self, fid):
        self.fid       = fid
        self.ignore    = False
        # Get plugin to extract the filter in and out parameters
        f   = engine.get_plugin(fid)
        doc = minidom.parse(join(f.root_path, "info.xml"))
        # Extract the slot info
        self.in_color  = str(doc.getElementsByTagName("in")[0].getAttribute("colorspace"))
        self.out_color = str(doc.getElementsByTagName("out")[0].getAttribute("colorspace"))

        # Do a lazy check to see if the colorspaces are contained in the cv2
        # color constants
        color_list = [c for c in dir(cv2) if c.startswith("COLOR")]

        if not [c for c in color_list if self.in_color in c]:
            raise InvalidColorSpace("Invalid colorspace '{}'".format(self.in_color))
        if not [c for c in color_list if self.out_color in c]:
            raise InvalidColorSpace("Invalid colorspace '{}'".format(self.out_color))

class FilterPage(object):
    """Manages a list of Filter Plugins id's that will be applied to the frames.

    This class contains a list of Filter Plugin ids that can have their positions
    changed and can be removed or ignored.
    This list is used at the filtering stage when each filter of a page will be
    applied to a frame sequentially.

    """
    def __init__(self, page_name, in_color, out_color):
        self.name      = page_name
        self.flist     = []
        self.in_color  = in_color
        self.out_color = out_color

        self.m_id = get_app().register_message_listener(self)

    def receive_message(self, mtype, mdata, sender):
        if mtype == "plugin_unloaded":
            if mdata["id"] in self.id_list():
                self.remove(mdata["id"])

    def id_list(self):
        return [f.fid for f in self.flist]

    def add(self, fid):
        if fid not in self.id_list():
            self.flist.append(FilterElement(fid))
            get_app().post_message("filter_rack_added", {"page_name" : self.name,
            "id": fid, "pos": len(self.flist) - 1}, self.m_id)
        else:
            raise ValueError("Filter ID already in the list")

    def remove(self, fid):
        pos = self.filter_pos(fid)
        del self.flist[pos]
        get_app().post_message("filter_rack_removed", {"page_name": self.name, "id": fid, "pos": pos}, self.m_id)

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
            get_app().post_message("filter_rack_up", {"page_name": self.name, "id": fid, "old_pos": pos, "new_pos": pos-1}, self.m_id)
            return pos - 1
        else:
            raise IndexError("Cannot up filter at the beggining of the list")

    def down(self, fid):
        pos = self.filter_pos(fid)
        if pos < len(self.flist) - 1:
            self.flist[pos + 1], self.flist[pos] = self.flist[pos], self.flist[pos + 1]
            get_app().post_message("filter_rack_down", {"page_name": self.name, "id": fid, "old_pos": pos, "new_pos": pos+1}, self.m_id)
            return pos + 1
        else:
            raise IndexError("Cannot down filter at end of the list")

    def ignore(self, fid, ignore = True):
        pos = self.filter_pos(fid)
        self.flist[pos].ignore = ignore
        get_app().post_message("filter_rack_ignore", {"page_name": self.name, "id": fid, "ignore": ignore, "pos": pos}, self.m_id)

    def is_last(self, fid):
        return self.filter_pos(fid) == len(self.flist) - 1

    def is_first(self, fid):
        return self.filter_pos(fid) == 0

    def is_ignored(self, fid):
        pos = self.filter_pos(fid)
        return self.flist[pos].ignore

    def clear_page(self):
        for i in self.id_list():
            self.remove(i)

    def __len__(self):
        return len(self.flist)

    def get_flow_errors(self):
        """Check if the flow is correct.

        Check each filter to see if its output colorspace is the same input
        colorspace of the next filter.

        Returns
        -------
        []              : if there is no errors
        [(first, next)] : a list containing the id of the first filter of the
        flow that have a wrong output, and the id of next filter, that have the
        wrong input. It checks all the filters. If 'first' is a value and next
        is None, it means that last filter of the list has a wrong output (it
        must be the same as the filter page). If 'next' is a value and 'first'
        is None, it means that the first filter of the list has a wrong input
        (must be the same as the filter page).


        """
        flow_errors = []
        if not len(self.flist):
            return flow_errors

        first = self.flist[0]
        last  = self.flist[-1]

        if first.in_color != self.in_color:
            flow_errors.append((None, first.fid))

        if last.out_color != self.out_color:
            flow_errors.append((last.fid, None))

        for i in range(0, len(self.flist)):
            if i+1 >= len(self.flist):
                break
            if self.flist[i].out_color != self.flist[i+1].in_color:
                flow_errors.append((i, i+1))

        return flow_errors

    def apply_filters(self, frame):
        if self.get_flow_errors():
            raise FilterPageFlowError()

        if frame.color_space != self.in_color:
            raise WrongColorSpace("Frame should be {} and not {}".format(self.in_color, frame.color_space))

        for i in range(0, len(self.flist)):
            if self.flist[i].ignore:
                continue
            p = engine.get_plugin(self.flist[i].fid)
            frame = p.instance.apply_filter(frame)

        if get_app().user_options["preview_source"] == get_app().OPT_PREVIEW_FILTER_PAGE:
            if self.name == get_app().user_options["filter_group"]:
                fs = engine.get_component("frame_stream")
                fs.preview_queue.put(frame.copy())
        return frame

    def get_filter(self, fid):
        return self.flist[self.filter_pos(fid)]

class FilterRack(object):
    def __init__(self):
        self.pages = {}
        self.m_id = get_app().register_message_listener(self)

        self.add_page("Raw", "None", "None")

    def receive_message(self, message_type, message_data, sender):
        pass

    def get_page(self, name):
        return self.pages[name]

    def add_page(self, name, in_color, out_color):
        if name in self.pages:
            raise KeyError("Page '{}' already exists".format(name))
        self.pages[name] = FilterPage(name, in_color, out_color)
        get_app().post_message("filter_page_added", {"name" : name}, self.m_id)

        return self.pages[name]

    def remove_page(self, name):
        if name not in self.pages:
            raise KeyError("Page '{}' not in the filter rack".format(name))
            self.pages[name].clear_page()
        get_app().post_message("filter_page_deleted", {"name": name}, self.m_id)
        del self.pages[name]

    def clear_rack(self):
        for name in self.pages:
            self.remove_page(name)

    def get_filter(self, fid):
        for p in self.pages:
            try:
                return p, self.pages[p].get_filter(fid)
            except:
                pass

        raise KeyError("There is no filter with given ID in the filter rack")
