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
"""Module that contains the FilterRack class.

The FilterRack is responsible for managing the current loaded filter pages and
the filters that compose each filter page. It is also responsible for
applying the filters on a frame.
"""
from os.path import join
import logging
from xml.dom import minidom

from gui.application import get_app
from ic.engine import get_engine
import cv2


class InvalidColorSpace(Exception):
    """Raised when a filter's xml file specifies an invalid color space string."""
    pass


class WrongColorSpace(Exception):
    """Raised when a frame has a different colorspace than theinput colorspace of the Filter Page.
    """
    pass


class FilterPageFlowError(Exception):
    """Raised when a filter page has one or more invalid filter flow.

    """
    pass


LOG = logging.getLogger(__name__)


class FilterElement(object):
    """Class that holds informations about a filter.

    This class is used by the FilterPage to store information about the inserted
    filters.
    """
    def __init__(self, fid):
        self.fid = fid
        self.ignore = False
        f = get_engine().get_plugin(fid)
        doc = minidom.parse(join(f.root_path, "info.xml"))
        self.in_color = str(doc.getElementsByTagName("in")[0].getAttribute("colorspace"))
        self.out_color = str(doc.getElementsByTagName("out")[0].getAttribute("colorspace"))
        # Do a lazy check to see if the colorspaces are contained in the cv2
        # color constants
        color_list = [c for c in dir(cv2) if c.startswith("COLOR")]
        if not [c for c in color_list if self.in_color in c]:
            raise InvalidColorSpace()
        if not [c for c in color_list if self.out_color in c]:
            raise InvalidColorSpace()

class FilterPage(object):
    """Manages a list of FilterElements that will be applied to the frames.

    This class contains a list of FilterElements that can have their positions
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
        _ = sender
        if mtype == "plugin_unloaded":
            if mdata["id"] in self.id_list():
                self.remove(mdata["id"])

    def id_list(self):
        """Return a list containing the filter's ids currently inserted."""
        return [f.fid for f in self.flist]

    def add(self, pid):
        """Add the specified plugin id at the list of filters.

        This method will initialize the plugin as a filter and add it to the
        filters list.

        Args:
          pid (int): The plugin id.

        Raises:
          ValueError: If the filter is already in the list.
        """
        if pid not in self.id_list():
            self.flist.append(FilterElement(pid))
            get_app().post_message("filter_rack_added", {"page_name" : self.name,
            "id": pid, "pos": len(self.flist) - 1}, self.m_id)
        else:
            raise ValueError("Filter ID already in the list")

    def remove(self, fid):
        """Remove a filter from the list.

        Args:
          fid (int): The filter identifier.

        Raises:
          ValueError: If the filter is not in the list.
        """
        if fid not in self.id_list():
            raise ValueError("Filter id not in the list.")
        pos = self.filter_pos(fid)
        del self.flist[pos]
        get_app().post_message("filter_rack_removed", {"page_name": self.name, "id": fid, "pos": pos}, self.m_id)

    def __iter__(self):
        return iter(self.flist)

    def filter_pos(self, fid):
        """Return the filter position on the list.

        Args:
          fid (int): The filter identifier.

        Raises:
          ValueError: If the filter is not in the list.
        """
        for (i, f) in enumerate(self.flist):
            if f.fid == fid:
                return i
        raise ValueError("Filter ID not in the list")

    def up(self, fid):
        """Move the filter one position above on the list.

        Args:
          fid (int): The filter identifier.

        Raises:
          IndexError: If the filter is at the beggining of the list.
        """
        pos = self.filter_pos(fid)
        if pos > 0:
            self.flist[pos - 1], self.flist[pos] = self.flist[pos], self.flist[pos - 1]
            get_app().post_message("filter_rack_up", {"page_name": self.name, "id": fid, "old_pos": pos, "new_pos": pos-1}, self.m_id)
            return pos - 1
        else:
            raise IndexError("Cannot up filter at the beggining of the list")

    def down(self, fid):
        """Move the filter one position below on the list.

        Args:
          fid (int): The filter identifier.

        Raises:
          IndexError: If the filter is at the end of the list.
        """
        pos = self.filter_pos(fid)
        if pos < len(self.flist) - 1:
            self.flist[pos + 1], self.flist[pos] = self.flist[pos], self.flist[pos + 1]
            get_app().post_message("filter_rack_down", {"page_name": self.name, "id": fid, "old_pos": pos, "new_pos": pos+1}, self.m_id)
            return pos + 1
        else:
            raise IndexError("Cannot down filter at end of the list")

    def ignore(self, fid, ignore = True):
        """Set the filter `ignore` value.

        If `ignore` is True, the filter wont be a part of the filtering chain
        and will be ignored.

        Args:
          fid (int): The filter identifier.
          ignore (bool): True to ignore the filter.
        """
        pos = self.filter_pos(fid)
        self.flist[pos].ignore = ignore
        get_app().post_message("filter_rack_ignore", {"page_name": self.name, "id": fid, "ignore": ignore, "pos": pos}, self.m_id)

    def is_last(self, fid):
        """Return True if the filter is the last on the list."""
        return self.filter_pos(fid) == len(self.flist) - 1

    def is_first(self, fid):
        """Return True if the filter is the first on the list."""
        return self.filter_pos(fid) == 0

    def is_ignored(self, fid):
        """Return the filter's `ignore` value on the list."""
        pos = self.filter_pos(fid)
        return self.flist[pos].ignore

    def clear_page(self):
        """Remove all filters from the list."""
        for i in self.id_list():
            self.remove(i)

    def __len__(self):
        return len(self.flist)

    def get_flow_errors(self):
        """Check if the flow is correct.

        Check each filter to see if its output colorspace is the same input
        colorspace of the next filter. Ignored filters don't get checked.

        Returns:
          list (first, next, first_fid, next_fid): Each element of the list is
            a tuple representing an error found, where:
              first (int): position of the filter in which the output colorspace
                is wrong. If first is `None`, it means that there is an error
                between the first filter and the page input colorspace.
              next (int): The position of the filter in which the input
                colorspace is wrong. If next is `None`, it means that there is
                an error between the last filter and the page output colorspace.
              first_fid (int): The identifier of the first filter.
              next_fid (int): The identifier of the next filter.
        """
        flow_errors = []
        if not len(self.flist):
            return flow_errors
        try:
            first = [f for f in self.flist if not f.ignore][0]
            last  = [f for f in self.flist if not f.ignore][-1]

            if first.in_color != self.in_color:
                flow_errors.append((None, 0))

            if last.out_color != self.out_color:
                flow_errors.append((len(self.flist)-1, None))
        except:
            pass

        previousf = -1
        nextf     = -1
        searching = True

        for i in range(0, len(self.flist)):
            if self.flist[i].ignore:
                continue
            if previousf  == -1:
                previousf = i
                continue
            if searching:
                nextf = i
                searching = False
            if not searching:
                if self.flist[previousf].out_color != self.flist[nextf].in_color:
                    flow_errors.append((previousf, nextf, self.flist[previousf].fid, self.flist[nextf].fid))
                    previousf = i
                    searching = True
        return flow_errors

    def apply_filters(self, frame):
        """Sequentially apply the filters on the given frame.

        The ignored filters are not applied.

        Args:
          frame (Frame): The frame object to apply the filters.

        Raises:
          WrongColorSpace: If the frame has a different colorspace than the
            input colorspace of the Filter Page.
        """
        if self.get_flow_errors():
            raise FilterPageFlowError()

        if frame.color_space != self.in_color:
            raise WrongColorSpace("Frame should be {} and not {}".format(self.in_color, frame.color_space))

        for i in range(0, len(self.flist)):
            if self.flist[i].ignore:
                continue
            p = get_engine().get_plugin(self.flist[i].fid)
            frame = p.instance.apply_filter(frame)

        if get_app().user_options["preview_source"] == get_app().OPT_PREVIEW_FILTER_PAGE:
            if self.name == get_app().user_options["filter_group"]:
                fs = get_engine().get_component("frame_stream")
                fs.preview_queue.put(frame.copy())
        return frame

    def get_filter(self, fid):
        return self.flist[self.filter_pos(fid)]

class FilterRack(object):
    """Manages the Filter Pages.

    """
    def __init__(self):
        self.pages = {}
        self.m_id = get_app().register_message_listener(self)

        self.add_page("Raw", "None", "None")

    def receive_message(self, message_type, message_data, sender):
        pass

    def get_page(self, name):
        """Return the page with the given name.

        """
        return self.pages[name]

    def add_page(self, name, in_color, out_color):
        """Add a new page.

        Args:
          name (str): The name of the page.
          in_color (str): A string representing the input colorspace.
          out_color (str): A string representing the output colorspace.

        Raises:
          KeyError: If there is one page with the same name already inserted.
        """
        if name in self.pages:
            raise KeyError("Page already exists.")
        self.pages[name] = FilterPage(name, in_color, out_color)
        get_app().post_message("filter_page_added", {"name" : name}, self.m_id)
        return self.pages[name]

    def remove_page(self, name):
        """Remove a page.

        Args:
          name (str): The name of the page to be removed.

        Raises:
          KeyError: If there is no page with the given name.
        """
        if name not in self.pages:
            raise KeyError("Page not in the filter rack")
        get_app().post_message("filter_page_deleted", {"name": name}, self.m_id)
        del self.pages[name]

    def clear_rack(self):
        """Remove all the Filter pages from the filter rack."""
        for name in self.pages:
            self.remove_page(name)

    def get_filter(self, fid):
        """Find a filter by its id and return the FilterElement and the page name.

        This methods locates the filter with the given id and returns it's
        instance and the page name where it is located.

        Args:
          fid (int): Filter identifier.

        Returns:
          (filter_element, page_name): where
            filter_element (FilterElement): The filters element.
            page_name (str): The name of the page where the filter is in.

        Raises:
          KeyError: If there is no filter with given identifier.
        """
        for p in self.pages:
            try:
                return p, self.pages[p].get_filter(fid)
            except:
                pass

        raise KeyError("There is no filter with given ID in the filter rack")
