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
"""Module that contains the FilterRack class.

The FilterRack is responsible for managing the current loaded filter pages and
the filters that compose each filter page. It is also responsible for
applying the filters on a frame.
"""

import logging

import cv2
import numpy as np

from ic import messages
from ic import plugin

class WrongColorSpace(Exception):
    """Raised when a frame has a different color space than theinput colorspace of the Filter Page.
    """
    pass


class FilterPageFlowError(Exception):
    """Raised when a filter page has one or more invalid filter flow.

    """
    pass


LOG = logging.getLogger(__name__)

def copy_frame(f):
    f[0], np.copy(f[1]), f[2], f[3]

class FilterPage(object):
    """Manages a list of Filter Plugins that will be applied to the frames.

    This class contains a list of Filter Plugins that can have their positions
    changed and can be removed or ignored.
    This list is used at the filtering stage when each filter of a page will be
    applied to a frame sequentially.

    """
    def __init__(self, fr, page_name, in_color, out_color):
        self._fr = fr
        self.name = page_name
        self.flist = []
        self.in_color = in_color
        self.out_color = out_color
        self.flow_errors = False
        self.input_status = True
        self.output_status = True

    def id_list(self):
        """Return a list containing the plugin's ids currently inserted."""
        return [f.pid for f in self.flist]

    def add(self, filter_plugin):
        """Add the specified plugin id at the list of filters.

        This method will initialize the plugin as a filter and add it to the
        filters list.

        Args:
          filter_plugin (:class:`.FilterPlugin`): Instance of the ``Filter Plugin Object``
        Raises:
          ValueError: If the filter is already in the list.
        """
        if filter_plugin not in self.flist:
            self.flist.append(filter_plugin)
            self.update_flow_errors()
            messages.post("FR_filter_added", ";".join([self.name, str(filter_plugin.pid)]), self._fr)
        else:
            raise ValueError("Filter already in the list")

    def remove(self, filter_plugin):
        """Remove a filter from the list.

        Args:
          filter_plugi (int or :class:`.FilterPlugin` instance): The plugin identifier or instance.

        Raises:
          ValueError: If the filter is not in the list.
          TypeError: If `filter_plugin` is neither `int` or a `FilterPlugin` instance.
        """
        pos = self.filter_pos(filter_plugin)
        del self.flist[pos]
        self.update_flow_errors()
        messages.post("FR_filter_removed", ";".join([self.name, str(pos)]), self._fr)

    def __iter__(self):
        return iter(self.flist)

    def filter_pos(self, filter_plugin):
        """Return the filter position on the list.

        Args:
            filter_plugin (`int` or :class:`.FilterPlugin` instance): The `Filter Plugin` identifier or the `Filter Plugin Object` instance.

        Raises:
          ValueError: If the filter is not in the list.
          TypeError: If the given argument is neither `int` or `FilterPlugin` instance.
        """
        if isinstance(filter_plugin, int):
            def check(item):
                return filter_plugin == item.pid
        elif isinstance(filter_plugin, plugin.FilterPlugin):
            def check(item):
                return filter_plugin is item
        else:
            raise TypeError("Arg must be filter id or instance")

        for i in range(0, len(self.flist)):
            if check(self.flist[i]):
                return i
        raise ValueError("Filter not in the list.")

    def up(self, filter_plugin):
        """Move the filter one position above on the list.

        Args:
            filter_plugin (`int` or :class:`.FilterPlugin` instance): The `Filter Plugin` identifier or the `Filter Plugin Object` instance.

        Raises:
          IndexError: If the filter is at the beggining of the list.
          ValueError: If the filter is not in the list.
          TypeError: If the given argument is neither `int` or `FilterPlugin` instance.
        """
        pos = self.filter_pos(filter_plugin)
        if not pos:
            raise IndexError("Can't move up a filter on the beggining of the list.")
        f = self.flist
        f[pos-1], f[pos] = f[pos], f[pos-1]
        self.update_flow_errors()
        messages.post("FR_filter_swapped", ";".join([self.name, str(pos-1), str(pos)]), self._fr)

    def down(self, filter_plugin):
        """Move the filter one position below on the list.

        Args:
            filter_plugin (`int` or :class:`.FilterPlugin` instance): The `Filter Plugin` identifier or the `Filter Plugin Object` instance.

        Raises:
          IndexError: If the filter is at the beggining of the list.
          ValueError: If the filter is not in the list.
          TypeError: If the given argument is neither `int` or `FilterPlugin` instance.
        """
        pos = self.filter_pos(filter_plugin)
        if pos == len(self.flist)-1:
            raise IndexError("Can't move down a filter on the end of the list.")
        f = self.flist
        f[pos+1], f[pos] = f[pos], f[pos+1]
        self.update_flow_errors()
        messages.post("FR_filter_swapped", ";".join([self.name, str(pos), str(pos+1)]), self._fr)

    def ignore(self, filter_plugin, ignore = True):
        """Set the filter `ignore` value.

        If `ignore` is True, the filter wont be a part of the filtering chain
        and will be ignored.

        Args:
            filter_plugin (`int` or :class:`.FilterPlugin` instance): The `Filter Plugin` identifier or the `Filter Plugin Object` instance.
            ignore (bool): True to ignore the filter.
        """
        pos = self.filter_pos(filter_plugin)
        self.flist[pos].ignore = ignore
        self.update_flow_errors()
        messages.post("FR_filter_ignore_changed", ";".join([self.name, str(pos), str(ignore)]), self._fr)

    def is_last(self, filter_plugin):
        """Return True if the filter is the last on the list."""
        return self.filter_pos(filter_plugin) == len(self.flist) - 1

    def is_first(self, filter_plugin):
        """Return True if the filter is the first on the list."""
        return self.filter_pos(filter_plugin) == 0

    def is_ignored(self, filter_plugin):
        """Return the filter's `ignore` value on the list."""
        pos = self.filter_pos(filter_plugin)
        return self.flist[pos].ignore

    def clear_page(self):
        """Remove all filters from the list."""
        while self.flist:
            self.remove(self.flist.pop())

    def __len__(self):
        return len(self.flist)

    def update_flow_errors(self):
        """Check if the flow is correct.

        Check each filter to see if its output colorspace is the same input
        colorspace of the next filter. Ignored filters don't get checked.
        """
        self.flow_errors = False
        valid_flag = True
        valid_list = [f for f in self.flist if not f.ignore]
        if not len(valid_list):
            return
        try:
            first = valid_list[0]
            last  = valid_list[-1]

            self.input_status = first.input_status = first.colorspace[0] == self.in_color
            self.output_status = last.output_status = last.colorspace[1] == self.out_color

            valid_flag = valid_flag and first.input_status and last.output_status
        except:
            pass

        for i in range(0, len(valid_list)-1):
            p, n = valid_list[i], valid_list[i+1]
            p.output_status = n.input_status = p.colorspace[1] == n.colorspace[0]
            valid_flag = valid_flag and p.output_status

        self.flow_errors = not valid_flag


    def apply_filters(self, frame):
        """Sequentially apply the filters on the given frame.

        The ignored filters are not applied.

        Args:
          frame (Frame): The frame object to apply the filters.

        Raises:
          WrongColorSpace: If the frame has a different colorspace than the
            input colorspace of the Filter Page.
        """
        if self.flow_errors:
            raise FilterPageFlowError()

        page_before = "filter_page:%s;before" % (self.name)
        page_after = "filter_page:%s;" % self.name
        targets_buffer = self._fr._engine.targets_buffer

        colorspace, data, pos, timestamp = frame

        if colorspace != self.in_color:
            raise WrongColorSpace()

        if page_before in targets_buffer:
            targets_buffer[page_before] = (colorspace, np.copy(data))

        for f in self.flist:
            filter_before = "filter_id:%d;before" % f.pid
            filter_after = "filter_id:%d;" % f.pid

            if filter_before in targets_buffer:
                targets_buffer[filter_before] = (colorspace, np.copy(data))

            if not f.ignore:
                colorspace, data = f.apply_filter((colorspace, data, pos, timestamp))

            if filter_after in targets_buffer:
                targets_buffer[filter_after] = (colorspace, np.copy(data))

        if page_after in targets_buffer:
            targets_buffer[page_after] = (colorspace, np.copy(data))

        return colorspace, data, pos, timestamp

    def get_filter(self, filter_plugin):
        return self.flist[self.filter_pos(filter_plugin)]

class FilterRack(object):
    """Manages the Filter Pages.

    """
    def __init__(self, engine):
        self._engine = engine
        self.pages = {}
        self.add_page("Raw", "BGR", "BGR")


    def get_page(self, name):
        """Return the page with the given name.

        """
        return self.pages[name]

    def __getitem__(self, name):
        return self.get_page(name)

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
        self.pages[name] = FilterPage(self, name, in_color, out_color)
        messages.post("FR_page_added", ";".join([name, in_color, out_color]), self)
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
        messages.post("FR_page_removed", name, self)
        del self.pages[name]

    def clear_rack(self):
        """Remove all the Filter pages from the filter rack."""
        for page in [i for i in self.pages if i != "Raw"]:
            self.remove_page(page)

    def get_filter(self, filter_plugin):
        """Find a filter by its id and return the FilterElement and the page name.

        This methods locates the filter with the given id and returns it's
        instance and the page name where it is located.

        Args:
            filter_plugin (`int` or :class:`.FilterPlugin` instance): The filter plugin identifier
                or instance.
        Returns:
          (filter_plugin, page_name): where
            filter_element (:class:`.FilterPlugin`): The `FilterPlugin` instance.
            page_name (str): The name of the page where the filter is in.

        Raises:
          KeyError: If there is no filter with given identifier.
        """
        for p in self.pages:
            try:
                return p, self.pages[p].get_filter(filter_plugin)
            except:
                pass

        raise KeyError("There is no filter with given ID in the filter rack")
