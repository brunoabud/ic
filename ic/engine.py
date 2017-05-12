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
"""Module that controls the analysis.

This module contains the singleton Engine class that is responsible for loading
main components of the application and managing plugins.
"""
import logging
import os
import sys
from xml.dom import minidom, Node
import imp

from gui.gui_interface import GUI_Interface
from util import find_free_key
from gui.application import get_app


LOG = logging.getLogger(__name__)

class PluginInitError(Exception):
    """Raised when a plugin could not be initialized.

    """
    pass


PLUGIN_TYPE_ANY = 0x0
PLUGIN_TYPE_VIDEO_INPUT = 0x1
PLUGIN_TYPE_ANALYSIS = 0x2
PLUGIN_TYPE_FILTER = 0x3


def init():
    """Initialize the Engine module and class.
    """
    if Engine.instance() is None:
        Engine()


def get_engine():
    """Return the unique Engine class instance.
    """
    return Engine.instance()


class Engine(object):
    """Class that holds all Analysis Components.

    """
    _INSTANCE = None

    def __init__(self):
        assert Engine._INSTANCE is None
        Engine._INSTANCE = self
        # Dictionary containing all loaded engine components
        self.components = {}
        # Dictionary containing the currently initialized input plugin and it's
        # GUI_Interface object among other informations about the plugin.
        self.input_plugin = None
        # Dictionary containing the currently initialized analy. plugin and it's
        # GUI_Interface object mong other informations about the plugin.
        self.analysis_plugin = None
        # This dictionary holds all the plugin objects loaded using the
        # load_plugin method, all plugin objects have a unique id. They can be
        # retrivied by calling the method get_plugin
        self._loaded_plugins = {}

        self.identifier = get_app().register_message_listener(self)

    @classmethod
    def instance(cls):
        return cls._INSTANCE

    def get_component(self, component):
        """Return a previously loaded component.
        """
        return self.components[component]

    def load_component(self, name, cls, *args, **kwargs):
        """Create and register a new instance of cls, using *args and **kwargs.

        This method will created a new instance of cls, passing *args and
        **kwargs to the constructor and then save it in the components dict
        using `name` as the key. Components that are already loaded will be
        ignored.
        """
        try:
            if name in self.components:
                return
            instance = cls(*args, **kwargs)
            self.components[name] = instance
        except:
            LOG.error("Could not load component %s", str(cls), exc_info=True)

    def receive_message(self, message_type, message_data, sender):
        _ = message_data, sender
        analysis_plugin = None
        video_source = self.get_component("video_source")
        try:
            analysis_plugin_info = self.get_analysis_plugin()
            if analysis_plugin_info is not None:
                analysis_plugin = self.get_plugin(analysis_plugin_info["plugin_id"])
        except: #pylint: disable=bare-except
            LOG.debug("Could not get analysis plugin", exc_info=True)

        if message_type == "frame_stream_sought":
            if analysis_plugin:
                try:
                    analysis_plugin.instance.on_media_sought(state=video_source.source_state())
                except: #pylint: disable=bare-except
                    LOG.error("Error when calling plugin media_sought callback", exc_info=True)
        elif message_type == "video_source_opened":
            if analysis_plugin:
                try:
                    analysis_plugin.instance.on_media_opened(video_source.source_state())
                except: #pylint: disable=bare-except
                    LOG.error("Error when calling plugin media_sought callback", exc_info=True)
        elif message_type == "video_source_closed":
            if analysis_plugin:
                try:
                    analysis_plugin.instance.on_media_closed(video_source.source_state())
                except:
                    LOG.error("Error when calling plugin media_sought callback", exc_info=True)

    @classmethod
    def list_plugins(cls, plugin_type=PLUGIN_TYPE_ANY):
        """Return a list with all the installed plugins of the specified type.

        Args:
          plugin_type (int): The type of plugin to be listed. One of the engine
          module constants

        Returns:
          list: The list contains tuples containing (type, name, path, info) in
          which:
            type (int): The type constant of the plugin.
            name (str): The name of the plugin.
            path (str): The absolute path of the plugin's root folder.
            info (dict): A dict containing info like Description, Author etc.,
              parsed from the plugin's `info.xml` file. On this dict, both keys
              and value are unicode strings.

        """
        join = os.path.join
        listdir = os.listdir
        app = get_app()

        # A plugin folder should contain the following structure
        #
        # Plugin_Folder(name) -> info.xml
        #                     -> main.py
        #                     -> ui      -> [.ui files only]
        plugins_path = app.settings["plugins_dir"]
        folders = listdir(plugins_path)
        plugin_list = []
        for folder in folders:
            full_path = join(plugins_path, folder)
            try:
                doc = minidom.parse(join(full_path, "info.xml"))
                type_list = {
                    "VideoInput" : PLUGIN_TYPE_VIDEO_INPUT,
                    "VideoAnalysis" : PLUGIN_TYPE_ANALYSIS,
                    "Filter": PLUGIN_TYPE_FILTER
                    }
                type_tag = doc.documentElement.localName
                if (plugin_type != PLUGIN_TYPE_ANY and
                        type_list[type_tag] != plugin_type):
                    continue
                tags = ["Title", "Description", "Author", "Version"]
                infos = {t: [i.nodeValue for i in doc.getElementsByTagName(t)[0].childNodes if
                             i.nodeType == Node.TEXT_NODE][0] for t in tags}
                # (type: int, name: str, path: str, info: dict)
                plugin_list.append((type_list[type_tag], folder, full_path, infos))
            except: #pylint: disable=bare-except
                LOG.error("Plugin %s raised exception, ignoring it.", folder, exc_info=True)
        return plugin_list

    def load_plugin(self, plugin_name):
        """Load a plugin, give it a unique identifier and return the object.

        Its important to notice that this method only loads the plugin, but not
        initializes it. To initialize a plugin object, an appropriate method
        should be called, based on the type of the plugin.

        A VideoInput plugin object will be initialized when the method
        `set_video_input` is called; a Filter plugin will be initialized
        when the method `FR_add_filter` is called; a Analysis plugin will be
        initialized when the method `set_analysis_plugin` is called.

        Args:
          plugin_name (str): The name of the plugin to be loaded.

        Returns:
          (plugin_id, plugin): where
            plugin_id (int): The unique plugin identifier.
            plugin (Plugin): The Plugin object.

        Raises:
          ValueError: If the plugin with given name is not installed.
          Exception: Exceptions that may be raised when importing the module.
        """
        # The `Plugin` class holds information about the plugin.
        # The loaded_ui_objects is a list of the loaded ui objects, but these
        # ui are those located in the plugin's `ui` dir, and their names are
        # local to the 'plugin scope', thus they have their own list.
        class Plugin(object):
            def __init__(slf, plugin_type, plugin_name, root_path, instance): #pylint: disable=no-self-argument
                slf.plugin_type = plugin_type
                slf.plugin_name = plugin_name
                slf.root_path = root_path
                slf.instance = instance
                slf.loaded_ui_objects = {}
                slf.gui_interface = None

        join = os.path.join
        isfile = os.path.isfile
        app = get_app()

        # A plugin folder should contain the following structure
        #
        # Plugin_Folder -> info.xml
        #               -> main.py
        #               -> ui      -> [.ui files only]

        plist = self.list_plugins()
        p = [p_data for p_data in plist if p_data[1] == plugin_name]
        if not p:
            raise ValueError("There is no plugin with given name installed")

        ptype, pname, ppath, _ = p[0]

        main_path = join(ppath, "main.py")
        if not isfile(main_path):
            raise IOError("The plugin  doesn't have a main module")
        instance = None
        with open(main_path, "r") as f:
            plugin_module = imp.load_module("main", f, main_path, (".py", "r", imp.PY_SOURCE))
            instance = plugin_module.main(ppath)
        plugin = Plugin(ptype, pname, ppath, instance)
        id_ = find_free_key(self._loaded_plugins)
        self._loaded_plugins[id_] = plugin
        app.post_message("plugin_loaded",
                         {"id": id_, "type": plugin.plugin_type,
                          "plugin": plugin}, -1)
        return (id_, plugin)

    def close_input(self):
        raise NotImplementedError()

    def close_analysis(self):
        raise NotImplementedError()

    def get_input_plugin(self):
        return self.input_plugin

    def get_analysis_plugin(self):
        return self.analysis_plugin

    def init_input_plugin(self, plugin_id):
        """Sets the current Video Input Plugin.

        This methods close any previously loaded Plugin and initialize the new
        one. It does not load or unload the plugins, just init and close them.

        """
        try:
            video_source = self.get_component("video_source")
            app = get_app()
            new_plugin = self.get_plugin(plugin_id)
            if not new_plugin.plugin_type == PLUGIN_TYPE_VIDEO_INPUT:
                raise TypeError("Wrong Plugin Type")
            if self.input_plugin is not None:
                current_id = self.input_plugin["plugin_id"]
                current_plugin = self.get_plugin(current_id)
                try:
                    current_plugin.instance.close_plugin()
                except: #pylint: disable=bare-except
                    LOG.error("Error when closing the plugin", exc_info=True)
                try:
                    current_plugin.gui_interface.release()
                    current_plugin.gui_interface = None
                except: #pylint: disable=bare-except
                    LOG.error("Error when releasing the gui interface", exc_info=True)
                self.input_plugin = None
                video_source.close_bridge()
                app.post_message("video_input_closed", {"plugin_id": current_id}, -1)

            video_source_bridge = video_source.get_input_bridge()
            interface = GUI_Interface(plugin_id)
            try:
                ret = new_plugin.instance.init_plugin(gui_interface=interface,
                                                      video_source_bridge=video_source_bridge)
                if ret:
                    video_source.init_bridge(new_plugin)
                    new_plugin.gui_interface = interface
                    self.input_plugin = {"plugin_id": plugin_id}
                    app.post_message("video_input_changed", {"plugin_id": plugin_id}, -1)
                else:
                    interface.release()
                    raise PluginInitError("init_plugin returned False")
            except: #pylint: disable=bare-except
                LOG.error("Error when initialiazing input plugin", exc_info=True)
                interface.release()
                video_source.close_bridge()

        except: #pylint: disable=bare-except
            LOG.error("Could not init input plugin", exc_info=True)

    def init_analysis_plugin(self, plugin_id):
        """Sets the current Video Analysis Plugin.

        This methods close any previously loaded Plugin and initialize the new
        one. It does not load or unload the plugins, just init and close them.

        """
        try:
            plugin = self.get_plugin(plugin_id)
            if self.analysis_plugin:
                current_id = self.analysis_plugin["plugin_id"]
                current_plugin = self.get_plugin(current_id)
                try:
                    current_plugin.instance.release()
                except:
                    LOG.debug("Error when releasing analysis plugin", exc_info=True)
                try:
                    current_plugin.gui_interface.release()
                except:
                    LOG.error("Error when releasing analysis plugin GUI interface",
                              exc_info=True)
                self.analysis_plugin = None
            gui_interface = GUI_Interface(plugin_id)
            info_path = os.path.join(plugin.root_path, "info.xml")
            doc = minidom.parse(info_path)
            pages = {}
            for element in doc.getElementsByTagName("FilterPage"):
                in_, out, name = [element.getAttribute(n) for n in ["in", "out", "name"]]
                pages[name] = {
                    "in"     : in_,
                    "out"    : out,
                    "filters": [],
                    "name"   : name
                    }

                for f in [n for n in element.childNodes if
                          n.nodeType == Node.ELEMENT_NODE and
                          n.localName == "Filter"]:
                    pages[name]["filters"].append(f.getAttribute("name"))

            rack_interface = {}
            for page in pages.values():
                rack = self.get_component("filter_rack")
                p = rack.add_page(page["name"], page["in"], page["out"])
                rack_interface[page["name"]] = p
                for f in page["filters"]:
                    try:
                        pid, _ = self.load_plugin(f)
                        p.add(pid)

                    except:
                        LOG.error("Filter '%s' required by Plugin could not be loaded", f,
                                  exc_info=True)
            try:
                if plugin.instance.init_plugin(gui_interface=gui_interface,
                                               rack_interface=rack_interface):
                    plugin.gui_interface = gui_interface
                    plugin.rack_interface = rack_interface
                    self.analysis_plugin = {"plugin_id": plugin_id}
                    video_source = self.get_component("video_source")
                    try:
                        plugin.instance.on_media_opened(video_source.source_state())
                    except sys.modules["ic.video_source"].SourceClosedError:
                        pass
                    except:
                        raise
                else:
                    raise PluginInitError()
            except:
                gui_interface.release()
                raise
        except:
            LOG.error("Could not init analysis plugin", exc_info=True)

    def unload_plugin(self, plugin_id):
        """Unload a previously loaded plugin.

        Args:
          plugin_id (int): The id of the plugin to be unloaded.

        Raises:
          ValueError: If the plugin_id is invalid.
        """
        app = get_app()
        if plugin_id in self._loaded_plugins:
            plugin = self._loaded_plugins[plugin_id]
            plugin.instance.release()
            app.post_message("plugin_unloaded",
                             {"id": plugin_id, "type": plugin.plugin_type,
                              "plugin": plugin}, -1)
            del self._loaded_plugins[plugin_id]
        else:
            raise ValueError("There is no plugin with given id")

    def get_plugin(self, plugin_id):
        """Return a the Plugin object correspondent to given id.

        Args:
          plugin_id (int): The id of the plugin to be unloaded.

        Raises:
          ValueError: If the plugin_id is invalid.

        """
        if plugin_id in self._loaded_plugins:
            return self._loaded_plugins[plugin_id]
        else:
            raise ValueError("There is no plugin with given id")
