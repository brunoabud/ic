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
"""Module that controls the analysis.

This module contains the singleton Engine class that is responsible for loading
main components of the application and managing plugins.
"""

import logging
import os
import sys

from ic import messages
from ic import plugin
from ic.filter_rack import FilterRack
from ic.frame_stream import FrameStream
from ic.queue import Queue

LOG = logging.getLogger(__name__)


class InputPluginBridge(object):
    def __init__(self, engine):
        self._engine = engine

    def open(self, **kwargs):
        messages.post("ENGINE_source_opened", ";".join([str(kwargs["seekable"]), str(kwargs["length"])]), self._engine)
        self._engine._media_open_args = kwargs
        if self._engine.analysis_plugin is not None:
            p = self._engine.analysis_plugin
            try:
                p.on_media_opened(**kwargs)
            except:
                LOG.error("", exc_info=True)
        self._engine._vs_open = True

    def close(self):
        messages.post("ENGINE_source_closed", None, self._engine)
        self._engine._media_open_args = None
        if self._engine.analysis_plugin is not None:
            p = self._engine.analysis_plugin
            try:
                p.on_media_closed()
            except:
                LOG.error("", exc_info=True)
        self._engine._vs_open = False

class Engine(object):
    def __init__(self):
        self.filter_rack = FilterRack(self)
        self.frame_stream = FrameStream(self)
        self.raw_queue = Queue(5)
        self.preview_queue = Queue(10)
        self.input_plugin = None
        self.analysis_plugin = None
        self._media_open_args = None

        # The targets buffer is a dict that contains all the targeted frames to be
        # viewed by the user.
        # Each key is a target requested by a Canvas object, and it will be filled
        # at each processing step. The buffer dict will be put into the preview_queue
        # at the end of the step.
        self.targets_buffer = {}

        messages.register(self)

    def message_received(self, message_type, message_data, sender):
        if message_type == "SETTING_changed":
            pass

    def load_input_plugin(self, package, gui_interface):
        """Sets the current Video Input Plugin.

        """
        self.unload_input_plugin()
        try:
            video_source_bridge = InputPluginBridge(self)
            plugin_object = plugin.load(package,
                                        gui_interface=gui_interface,
                                        video_source_bridge=video_source_bridge)
            self.input_plugin = plugin_object
            self.filter_rack["Raw"].in_color = plugin_object.colorspace
            self.filter_rack["Raw"].out_color = plugin_object.colorspace
            messages.post("ENGINE_input_loaded", package, self)
            return plugin_object
        except:
            LOG.error("Could not load input plugin", exc_info=True)
            return None

    def is_vs_open(self):
        return self._vs_open

    def unload_input_plugin(self):
        if self.input_plugin:
            try:
                self.input_plugin.release_plugin()
            except:
                LOG.error("Error when releasing plugin", exc_info=True)
            finally:
                self.input_plugin.gui_interface.release()
                self.input_plugin = None

    def unload_analysis_plugin(self):
        if self.analysis_plugin:
            try:
                self.analysis_plugin.release_plugin()
            except:
                LOG.error("Error when releasing analysis plugin", exc_info=True)
            finally:
                self.analysis_plugin.gui_interface.release()
                self.analysis_plugin = None

    def load_analysis_plugin(self, package, gui_interface):
        """Sets the current Video Analysis Plugin.

        This methods close any previously loaded Plugin and initialize the new
        one. It does not load or unload the plugins, just init and close them.

        """
        self.unload_analysis_plugin()
        plugin_object = plugin.load(package,
                                    gui_interface=gui_interface,
                                    filter_rack=self.filter_rack)

        self.analysis_plugin = plugin_object
        messages.post("ENGINE_analysis_plugin_loaded", package, self)

        self.filter_rack.clear_rack()

        try:
            for p in plugin_object.package().FILTER_PAGES:
                page = plugin_object.package().FILTER_PAGES[p]
                added = self.filter_rack.add_page(p, page["in"], page["out"])
                for f in page["filters"]:
                    self.load_filter_plugin(f, p)
        except:
            self.filter_rack.clear_rack()
            try:
                plugin_object.release_plugin(2)
            except:
                pass
            gui_interface.release(2)
            raise

        if self._media_open_args is not None:
            LOG.debug("REALODING")
            plugin_object.on_media_opened(**self._media_open_args)
            LOG.debug("%s", str(self._media_open_args))

        self.analysis_plugin = plugin_object
        return plugin_object

    def load_filter_plugin(self, package, page_name=None):
        try:
            plugin_object = plugin.load(package)
            if page_name is not None:
                self.filter_rack[page_name].add(plugin_object)
            return plugin_object
        except:
            LOG.error("Error when loading filter plugin", exc_info=True)
            return None
