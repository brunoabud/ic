import logging
import os
from xml.dom import minidom, Node
import imp
log = logging.getLogger(__name__)

from gui.gui_interface import GUI_Interface
from util import find_free_key
from gui.application import get_app

# Exception raised when a plugin could not be initialized
class PluginInitError(Exception):
    pass


# Plugin type constants
PLUGIN_TYPE_ANY            = 0x0
PLUGIN_TYPE_VIDEO_INPUT    = 0x1
PLUGIN_TYPE_ANALYSIS       = 0x2
PLUGIN_TYPE_FILTER         = 0x3

def init():
    if Engine._INSTANCE is None:
        Engine()

def get_component(name):
    return Engine._INSTANCE.components[name]

def load_component(name, cls, *args, **kwargs):
    """Creates and register a new instance of cls, using args and kwargs.

    """
    try:
        engine = Engine._INSTANCE
        if name in engine.components:
            return
        instance = cls(*args, **kwargs)
        engine.components[name] = instance
    except:
        log.error("Could not load component '{}'".format(cls))

def init_input_plugin(pid):
    """Sets the current Video Input Plugin.

    This methods close any previously loaded Plugin and initialize the new
    one. It does not load or unload the plugins, just init and close them.

    """
    return Engine._INSTANCE._init_input(pid)

def get_input_plugin():
    return Engine._INSTANCE.input_plugin

def init_analysis_plugin(pid):
    pass

def close_input_plugin():
    pass

def close_analysis_plugin():
    pass

def list_plugins(plugin_type = PLUGIN_TYPE_ANY):
    """Return a list with all the installed plugins of the specified type.

    Parameters
    ----------
    plugin_type : int
        The type of plugin to be listed

    Returns
    -------
    list of (type: int, name: str, path: str, info: dict)

    """
    return Engine._INSTANCE._list_plugins(plugin_type)

def load_plugin(plugin_name):
    """Load a plugin, give it a unique identifier and return the object.

    Its important to notice that this method only loads the plugin, but not
    initializes it. To initialize a plugin object, an appropriate method
    should be called, based on the type of the plugin.

    A VideoInput plugin object will be initialized when the method
    `set_video_input` is called; a Filter plugin will be initialized
    when the method `FR_add_filter` is called; a Analysis plugin will be
    initialized when the method `set_analysis_plugin` is called.

    Parameters
    ----------
    plugin_name : str
        The name of the plugin to be loaded

    Returns
    -------
    tuple(plugin_id, plugin)

    plugin_id : int
        The unique plugin identifier

    plugin : Plugin
        A Plugin object

    Raises
    ------
    ValueError : If the plugin name is not installed

    Exception : Exceptions that may be raised when importing the module
    """
    return Engine._INSTANCE._load_plugin(plugin_name)

def unload_plugin(plugin_id):
    """Unload a previously loaded plugin.

    Parameters
    ----------
    plugin_id : int
        The id of the plugin to be unloaded

    Raises
    ------
    ValueError : If the plugin_id is invalid
    """
    return Engine._INSTANCE._unload_plugin(plugin_id)

def get_plugin(plugin_id):
    """Return a the Plugin object correspondent to given id.

    Parameters
    ----------
    plugin_id : int
        The id of the plugin to be unloaded

    Raises
    ------
    ValueError : If the plugin_id is invalid.

    """
    return Engine._INSTANCE._get_plugin(plugin_id)

def loaded_plugins():
    return Engine._INSTANCE._loaded_plugins

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
        self.input_plugin    = None
        # Dictionary containing the currently initialized analy. plugin and it's
        # GUI_Interface object mong other informations about the plugin.
        self.analysis_plugin = None
        # This dictionary holds all the plugin objects loaded using the
        # load_plugin method, all plugin objects have a unique id. They can be
        # retrivied by calling the method get_plugin
        self._loaded_plugins = {}

    def _list_plugins(self, plugin_type = PLUGIN_TYPE_ANY):
        join = os.path.join
        listdir = os.listdir
        isdir = os.path.isdir
        isfile = os.path.isfile
        app = get_app()

        #A plugin folder should contain the following structure
        #
        #Plugin_Folder -> info.xml
        #              -> main.py
        #              -> ui      -> [.ui files only]

        #Get the path to the directory that will contain the plugin folders
        plugins_path = app.settings["plugins_dir"]

        #List all the folders inside the directory
        folders = listdir(plugins_path)

        #The list of plugin loadeds
        plugin_list = []

        #Iterate over the folders and extract the plugin info
        for folder in folders:
            full_path = join(plugins_path, folder)

            try:
                #Open the xml file to extract its info
                doc = minidom.parse(join(full_path, "info.xml"))

                #The correspondent plugin_type value for each node Name
                type_list = {
                    "VideoInput" : PLUGIN_TYPE_VIDEO_INPUT,
                    "VideoAnalysisModule" : PLUGIN_TYPE_ANALYSIS,
                    "Filter": PLUGIN_TYPE_FILTER
                    }

                #Get the tag name of the root element
                type_tag = doc.documentElement.localName
                #Go to the next folder if the type is not the specified
                if (plugin_type != PLUGIN_TYPE_ANY and
                type_list[type_tag] != plugin_type):
                    continue

                #List of tags to be extracted
                tags = ["Title", "Description", "Author", "Version"]
                #List of text nodes extracted from the xml file
                infos = {t:
                [i.nodeValue for i in doc.getElementsByTagName(t)[0].childNodes if
                i.nodeType == Node.TEXT_NODE][0] for t in tags}

                #(type: int, name: str, path: str, info: dict)
                plugin_list.append( (type_list[type_tag], folder, full_path, infos) )
            except:
                log.error("Plugin {} raised exception, ignoring it.".format(folder), exc_info=True)
        #Return the list containing the found plugins
        return plugin_list

    def _load_plugin(self, plugin_name):
        # The `Plugin` class holds information about the plugin.
        # The loaded_ui_objects is a list of the loaded ui objects, but these
        # ui are those located in the plugin's `ui` dir, and their names are
        # local to the 'plugin scope', thus they have their own list.
        class Plugin(object):
            def __init__(slf, plugin_type, plugin_name, root_path, instance):
                slf.plugin_type       = plugin_type
                slf.plugin_name       = plugin_name
                slf.root_path         = root_path
                slf.instance          = instance
                slf.loaded_ui_objects = {}
                slf.gui_interface     = None

        join = os.path.join
        listdir = os.listdir
        isdir = os.path.isdir
        isfile = os.path.isfile
        app = get_app()

        #A plugin folder should contain the following structure
        #
        #Plugin_Folder -> info.xml
        #              -> main.py
        #              -> ui      -> [.ui files only]

        #Get a list to the installed plugins
        plist = self._list_plugins()
        #Check if the plugin is in the list and get it
        p = [p_data for p_data in plist if p_data[1] == plugin_name]
        if not p:
            raise ValueError("There is no plugin '{}' installed".format(plugin_name))

        #Unpack the data
        ptype, pname, ppath, pinfo = p[0]

        #Check if there is a main.py file in the root folder
        main_path = join(ppath, "main.py")
        if not isfile(main_path):
            raise IOError("The plugin '{}' doesn't have a main module".format(plugin_name))

        #Load the module containing the main() function and call it to create
        #the plugin instance
        instance = None
        try:
            with open(main_path, "r") as f:
                #Load the plugin module
                plugin_module = imp.load_module("main", f, main_path, (".py", "r", imp.PY_SOURCE))
                #Call the main method to construct the plugin instance
                instance = plugin_module.main(ppath)
        except:
            raise

        #Create the plugin object that will be hold in the dictionary
        plugin = Plugin(ptype, pname, ppath, instance)
        #Find a free id
        id_ = find_free_key(self._loaded_plugins)
        #Save it to the dictionary and return the plugin object
        self._loaded_plugins[id_] = plugin

        app.post_message("plugin_loaded",
            {"id": id_, "type": plugin.plugin_type,
            "plugin": plugin}, -1)

        return (id_, plugin)

    def _close_input(self):
        pass

    def _close_analysis(self):
        pass

    def _init_input(self, plugin_id):
        try:
            video_source = get_component("video_source")
            app = get_app()
            # Check if the plugin_id is valid
            new_plugin = self._get_plugin(plugin_id)
            if not new_plugin.plugin_type == PLUGIN_TYPE_VIDEO_INPUT:
                raise TypeError("Wrong Plugin Type {}".format(new_plugin.plugin_type))

            # Close the current input plugin if there is one
            if self.input_plugin is not None:
                current_id = self.input_plugin["plugin_id"]
                current_plugin = app.get_plugin(current_id)

                #Call the plugin close method
                try:
                    current_plugin.instance.close_plugin()
                except:
                    log.error("Error when closing the plugin", exc_info=True)
                #Release the gui interface
                try:
                    current_plugin.gui_interface.release()
                    current_plugin.gui_interface = None
                except:
                    log.error("Error when releasing the gui interface", exc_info=True)
                #Clean the input plugin info
                self.input_plugin = None
                #Close the VideoSource bridge
                video_source.close_bridge()
                #Post the message signaling that the video input was closed
                app.post_message("video_input_closed", {"plugin_id": current_id}, -1)

            #Get a input bridge to the video source object
            video_source_bridge = video_source.get_input_bridge()
            #Object that provides gui access to the plugin
            interface = GUI_Interface(plugin_id)
            #Init the plugin
            try:
                ret = new_plugin.instance.init_plugin(gui_interface=interface, video_source_bridge=video_source_bridge)
                if ret:
                    #Init the VideoSource bridge
                    video_source.init_bridge(new_plugin.instance)
                    new_plugin.gui_interface = interface
                    self.input_plugin=  {"plugin_id": plugin_id}
                    app.post_message("video_input_changed", {"plugin_id": plugin_id}, -1)
                else:
                    interface.release()
                    raise PluginInitError("init_plugin returned False")
            except:
                log.error("Error when initialiazing input plugin", exc_info=True)
                #raise PluginInitError("Plugin init. raised exception")
                interface.release()
                video_source.close_bridge()

        except:
            log.error("Could not init input plugin", exc_info=True)

    def _init_analysis(self, pid):
        pass

    def _unload_plugin(self, plugin_id):
        app = get_app()
        if plugin_id in self._loaded_plugins:
            #The the Plugin instance
            plugin = self._loaded_plugins[plugin_id]
            #Call the plugins release method
            plugin.instance.release()
            #Post a message signaling that the plugin is about to be unloaded
            app.post_message("plugin_unloaded",
                {"id": plugin_id, "type": plugin.plugin_type,
                "plugin": plugin}, -1)
            #Delete from the list
            del self._loaded_plugins[plugin_id]
        else:
            raise ValueError("No plugin with id '{}'".format(plugin_id))

    def _get_plugin(self, plugin_id):
        if plugin_id in self._loaded_plugins:
            return self._loaded_plugins[plugin_id]
        else:
            raise ValueError("No plugin with id '{}'".format(plugin_id))
