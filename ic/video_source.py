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
"""Contains the VideoSource class, responsible for comunnicating with the Video Input.
"""
import logging
import types
from xml.dom import Node, minidom
import os
import sys

from gui.application import get_app, Application
from gui.gui_interface import GUI_Interface

LOG = logging.getLogger(__name__)


class SourceClosedError(Exception):
    """Raised when a closed VideoSource is accessed.
    """
    pass


class VideoSource(object):
    """Class responsible for communicating with the VideoInput.

    This class exposes methods to the VideoInput plugin to communicate when
    video sources are avaible. It is also responsible for signaling to the main
    application when a video source is or is not available.

    A Bridge to some of the Video Input Plugin methods is provided. It makes
    possible to call functions like `seek`, `tell`, `get_fps`, etc.

    """
    _INSTANCE = None

    def create_bridge(self):
        class InputBridge(object):
            """Class that exposes the _open and _close methods of the VideoSource instance.

            The input plugins will receive this bridge to signal that a video source is
            available or not.
            """
            def __init__(slf):
                pass

            def open(slf, *args, **kwargs):
                self._open(*args, **kwargs)

            def close(slf, *args, **kwargs):
                self._close(*args, **kwargs)

        return InputBridge()

    def __init__(self):
        assert VideoSource._INSTANCE is None
        VideoSource._INSTANCE = self
        # Is the video source open?
        self._source_open = False
        # List of bridged methods (Since they have the same behaviour, they will
        # be dynamically generated when the bridge is initialized)
        self._bridge_methods = ["seek", "tell", "get_length", "get_fps",
                                "get_size", "next"]
        # Create the bridge object that will be provided to the VideoInput
        self._input_bridge = self.create_bridge()
        # The current bridged plugin instance
        self._plugin_instance = None
        self.mid = get_app().register_message_listener(self)
        self.color_space = None

    def _open(self, *args, **kwargs):
        """Signal that a new video source is available.

        This method should be called by the Video Input Plugin to make a Video
        Source avaible to the application. The Video Input Plugin will have
        access to it by a bridge object, that will be provided when the init_plugin
        method of the plugin is called. This will be done by the Application
        object when the plugin is loaded. The bridge used can be obtained by
        calling VideoSource.create_input_bridge.
        """
        self._source_open = True
        get_app().post_message("video_source_opened", kwargs, self.mid)
        return True


    def _close(self, *args, **kwargs):
        """Signal that the current video source is now unavailable.

        This method should be called by the Video Input Plugin to make a Video
        Source unavailable to the application. The Video Input Plugin will have
        access to it by a bridge object, that will be provided when the init_plugin
        method of the plugin is called. This will be done by the Application
        object when the plugin is loaded. The bridge used can be obtained by
        calling VideoSource.get_input_bridge.
        """
        if self._source_open:
            self._source_open = False
            get_app().post_message("video_source_closed", kwargs, self.mid)
            return True

    def get_input_bridge(self):
        """Return the Input Bridge object.
        """
        return self._input_bridge

    def init_bridge(self, plugin):
        """Initialize an Video Input Plugin.

        This is the main method of the class. When a new Video Input Plugin is
        initialized, this function should be called. It will be responsible for:
         . Creating the bridge methods
         . Starting the state handling for the video input plugin
        When the Plugin is unloaded, the method `close_bridge` should be called
        """
        plugin_instance = plugin.instance
        # Extract the Input plugin OUT color space
        doc = minidom.parse(os.path.join(plugin.root_path, "info.xml"))
        color_space = doc.getElementsByTagName("out")[0].getAttribute("colorspace")
        self.color_space = color_space
        for m in self._bridge_methods:
            if not hasattr(plugin_instance,  m):
                raise NameError("The plugin does not have the method to be bridged")
            # Create a method that checks if the video source is open before
            # calling the bridge method. This is a bound method so the "self"
            # argument needs to be here.
            def create_method(name):
                def method(*args, **kwargs):
                    if not self._source_open:
                        raise SourceClosedError()
                    return getattr(plugin_instance, name).__call__(*args, **kwargs)
                return method

            # Add the bridged method to this object
            setattr(self, m, create_method(m))
        self._source_open = False
        self._plugin_instance = plugin_instance

    def close_bridge(self):
        """Reset all the states and remove the generated bridge methods.
        """
        # Remove the bridge methods
        for m in self._bridge_methods:
            if hasattr(self, m):
                delattr(self, m)
        # Reset the states
        self._source_open = False
        self.color_space = None
        # Tell the plugin to close the video source
        self._plugin_instance.close_source()
        self._plugin_instance = None

    def receive_message(self, mtype, mdata, sender):
        pass

    def is_open(self):
        return self._source_open

    def source_state(self):
        if not self.is_open():
            raise SourceClosedError()
        return {
            "fps": self._plugin_instance.get_fps(),
            "pos": self._plugin_instance.tell(),
            "length": self._plugin_instance.get_length(),
            "size": self._plugin_instance.get_size(),
            "color_space": self.color_space
        }
