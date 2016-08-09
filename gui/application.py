import sys
import os
from Queue import Queue
import traceback
from weakref import WeakValueDictionary
from importlib import import_module
import imp
from xml.dom import minidom, SyntaxErr, Node

from PyQt4 import uic
from PyQt4.QtCore import QTimer, QTranslator, Qt, QEvent
from PyQt4.QtGui import QApplication

from util import find_free_key

_DEBUG_MESSAGES = False

################################################################################
# Before importing this module, a QApplication obj must be created, since the
# Application class uses objects that requires it.
################################################################################

#Exception raised when the uic module fails to load an ui file for some reason
class UILoadError(Exception):
    pass

#Exception raised when the object provided is not a valid message receiver
class InvalidMessageReceiverError(Exception):
    pass

def get_app():
    return Application._INSTANCE


class Application(object):
    """The Main application class.

    The Application class is responsible for holding global data that will be
    shared between the whole application. It also provides a message dispatching
    system for intercommunication. Methods for loading resources are also avail-
    ble.

    This class is a singleton so the constructor will be called just once by
    the `imagem_cinematica` module. The instance can be retrived by the function
    get_app avaible in the module `application`.

    """

    # Singleton instance
    _INSTANCE = None

    # This option tells the application to pump raw frames to the preview queue
    OPT_PREVIEW_RAW            = 0x1
    # This option tells the application to pump frames right after they passed
    # through the filters in the filter rack
    OPT_PREVIEW_POST_FILTER    = 0x2
    # This options tells the application to pump frames right after they got
    # processed by the analysis plugin
    OPT_PREVIEW_POST_ANALYSIS = 0x3

    # Plugin type constants
    PLUGIN_TYPE_ANY            = 0x0
    PLUGIN_TYPE_VIDEO_INPUT    = 0x1
    PLUGIN_TYPE_ANALYSIS       = 0x2
    PLUGIN_TYPE_FILTER         = 0x3

    def __init__(self, argv):
        # Assert that there is no previous created instance
        assert Application._INSTANCE is None
        # Set this instance to the singleton _INSTANCE constant
        Application._INSTANCE = self

        # Create a new QApplication instance
        self._qapp = QApplication(argv)

        pjoin = os.path.join

        # Save the application main path (the local where the main script was
        # invoked by the interpreter)
        self.PATH = sys.path[0]

        # Create a default settings dictionary
        self.settings = {
            # The max frames that can be put in the raw queue
            'raw_queue_len' : 1,
            # The max frames that can be put in the preview queue
            'preview_queue_len' : 1,
            # The directory of the installed plugins
            'plugins_dir' : pjoin(self.PATH, 'plugins')  ,
            # The directory of the application resources (imgs, icons, ui, etc.)
            'resources_dir' : pjoin(self.PATH, 'resources'),
            # Max time to wait for a worker thread to finish
            'thread_wait_timeout': 500,
            'lang_dir' : pjoin(self.PATH, 'lang')
        }

        # This dictionary holds all the ui files loaded by calling the method
        # load_ui. They can be retrived by calling the method get_ui
        self._loaded_ui_objects = {}

        # A thread-safe queue that contains the messages to be dispatched
        self._messages = Queue()
        # A set containing all the objects that can receive messages. To insert
        # an object to the list, the method register_message_listener must be
        # used. The objects must have a `receive_message` method.
        # Each element of this set will be a tuple containing a unique identifier
        # and the object itself.
        self._message_listeners = WeakValueDictionary()
        # The timer that will be responsible for dispatching the messages
        self._message_timer = QTimer()
        # Connect the timeout signal to the method responsible for dispatching
        # the messages in the queue
        self._message_timer.timeout.connect(self._dispatch_messages)

        # This dictionary holds all the plugin objects loaded using the
        # load_plugin method, all plugin objects have a unique id. They can be
        # retrivied by calling the method get_plugin
        self._loaded_plugins = {}

        # If there is a video input plugin loaded, this member will hold info
        # about it, like the ui proxy, id and etc.
        self.video_input_info = None

        # The id of the loaded plugin that does the analysis procedures
        self.analysis_plugin_info = None

        # A dictionary containing options the user can change by interacting with
        # the GUI
        self.user_options = {
            "preview_source": Application.OPT_PREVIEW_RAW
            }

        #Current installed translator
        self._translator = None

        #Start the message-system timer
        self._message_timer.start()

    def get_ui(self, name):
        """Return the instance of a previously loaded ui file.

        The ui object will be a QObject. To load a new a new ui file use the
        `load_ui` method.

        Parameters
        ----------
        name : str
            The ui object's name/alias.

        Returns
        -------
        QObject

        Raises
        ------
        KeyError : If there is no ui object with the given name.

        """
        if name not in self._loaded_ui_objects:
            raise KeyError("There is no ui object with name '{}'".format(name))
        else:
            return self._loaded_ui_objects[name]

    def load_ui(self, name, ui_file, base_instance = None):
        """Load a ui_file from the resources directory and return it.

        This method loads a QtDesigner `.ui` file from the resources directory
        using the `uic` module and returns the instance. A name must be given
        for saving the instance in the application's dictionary. The name must
        be an alias, like 'main_window' or `console_window` so it can be shared
        across the application

        Parameters
        ----------
        name : str
            The name that will be used to share the object between the appli-
        cation modules. If the string is empty, the ui object will not be saved.

        ui_file : str
            The name of the ui file located in the resources directory.
        The `.ui` extension is optional.

        base_instance : QObject, None
            The base instance to load the ui file. The default value
        is None. When its `None`, the uic module will created a new instance,
        when an proper QWidget is given, the uic will use it as a base.

        Returns
        -------
        QObject

        Raises
        ------
        IOError : If the file was not found or has an invalid format/extension.

        KeyError : If there is an already loaded ui instance with the same name

        TypeError : If the base_instance is not the same as the one in the ui
        file.

        UILoadError : If the `uic` module raises any exception
        """
        #Check if there is a loaded ui with the given name
        if name in self._loaded_ui_objects:
            raise KeyError("A ui with name '{}' is already loaded.".format(name))

        join = os.path.join
        isfile = os.path.isfile
        splitext = os.path.splitext

        #Extract the file extension
        fname, ext = splitext(ui_file)

        #If there is no extension, append the right one to the end
        if ext == "":
            ui_file = fname + ".ui"
        #If there is an extensions, check if its right, else raised the IOError
        else:
            if ext != ".ui":
                raise IOError(("The file name has an invalid extension"
                               "'{}'").format(ext))

        #Expand the file to the absolute path
        ui_path = join(self.settings["resources_dir"], "ui", ui_file)

        #Check if the file exists
        if not isfile(ui_path):
            raise IOError("The file '{}' does not exist.".format(ui_file))

        try:
            if base_instance:
                instance = uic.loadUi(ui_path, base_instance)
                if hasattr(instance, "setupUi"):
                    try:
                        instance.setupUi()
                    except:
                        traceback.print_exc()

                if hasattr(instance, "retranslateUi"):
                    try:
                        instance.retranslateUi()
                    except:
                        traceback.print_exc()
            else:
                instance = uic.loadUi(ui_path)

            if name.strip() != '':
                self._loaded_ui_objects[name] = instance
            return instance
        except:
            print "------------------------------------------------------------"
            traceback.print_exc()
            print "------------------------------------------------------------"
            raise UILoadError()


    def register_message_listener(self, listener):
        """Register a object so the application dispatch messages to it.

        The message listener is registered using a Weak Reference, so the
        messages system will not keep the objects alive when all the other
        references are deleted.

        Parameters
        ----------
        listener : obj
            The object that will receive the message.

        Returns
        -------
        int
            An unique identifier to use when referencing the this listener in
            the messages system.

        Raises
        ------
        ValueError : If the listener object is already registered

        """
        #Check if the listener is in the list already
        for r in self._message_listeners.itervaluerefs():
            if r() is listener:
                raise ValueError("The object is already registered")

        id_ = find_free_key(self._message_listeners)
        self._message_listeners[id_] = listener
        return id_

    def unregister_message_listener(self, identifier):
        """Tell the pplication to stop dispatching messages to a listener.

        Parameters
        ----------
        identifier : int
            The identifier of the listener that will stop receiving messages.

        Raises
        ------
        ValueError : If there is no listener with the given identifier

        """
        try:
            del self._message_listeners[identifier]
        except KeyError:
            raise ValueError("There is no listener with id '{}'".format(identifier))

    def get_message_listener_instance(self, identifier):
        """Return a registered message listener with the given identifier.

        Parameters
        ----------
        identifier: int
            The identifier of the listener.

        Returns
        -------
        object
            The instance of the listener.

        Raises
        ------
        Value : If there is no listener with the given identifier.

        """
        try:
            return self._message_listeners[identifier]
        except KeyError:
            raise ValueError(("There is no message listener"
                            "registered with id {}").format(identifier))

    def post_message(self, message_type, message_data, sender):
        """Post a message to the messages system.

        Parameters
        ----------
        message_type : str
            A string containing a name/tag/alias for the message type. It should
            be lowercase and have no leading/trailing spaces. The string will
            be trimmed and changed to lower case.

        message_data :
            Any kind of object

        sender_id : int, class instance or None
            The id or reference of the sender. This will prevent the sender to
            receiving this message. If the type is int, it should be the identi-
            fier of the listener in the messages system. Can also be a reference
            to the sender instead of it's id. If None, the sender is considered
            anonymous, and will receive the message.
            If the id provided is invalid, it will be ignored.

        """
        self._messages.put((message_type.lower().strip(), message_data, sender))

    def _dispatch_messages(self):
        """Dispatch all the messages in the queue to the registered listeners.

        """
        #Create strong references to the listeners
        items = self._message_listeners.items()

        while not self._messages.empty():
            mtype, mdata, sender = self._messages.get(False)
            if _DEBUG_MESSAGES:
                print "<{}, {}>: {}".format(sender, mtype, mdata)
            #Assign an invalid identifier
            sender_id = -1
            #If the sender is an int it should be the sender identifier
            if isinstance(sender, int):
                sender_id = sender
            #If the sender is not an int, it should be a ref to a listener, so
            #try to locate it's id
            elif sender is not None:
                for (identifier, instance) in items:
                    if instance is sender:
                        sender_id = identifier


            for (identifier, instance) in items:
                #Dont dispatch the message to the sender
                if identifier == sender_id:
                    continue
                try:
                    #Call the receive_message method
                    instance.receive_message(mtype, mdata, sender_id)
                except:
                    print ("!! A message listener raised an exception when "
                    "receiving a message and will be removed from the list.")
                    traceback.print_exc()
                    del self._message_listeners[identifier]

    def import_resources(self):
        """Load the resource files contained in the gui package path.

        """
        #Get the path to the `gui` package, where the resource files will be
        #located
        _1, path, _3 = imp.find_module("gui")

        #Import all the files that end with `_rc.py`
        for m in [f for f in os.listdir(path) if f.endswith("_rc.py")]:
            try:
                import_module(m[:-3])
            except:
                pass


    def list_plugins(self, plugin_type = PLUGIN_TYPE_ANY):
        """Return a list with all the installed plugins of the specified type.

        Parameters
        ----------
        plugin_type : int
            The type of plugin to be listed

        Returns
        -------
        list of (type: int, name: str, path: str, info: dict)

        """
        join = os.path.join
        listdir = os.listdir
        isdir = os.path.isdir
        isfile = os.path.isfile

        #A plugin folder should contain the following structure
        #
        #Plugin_Folder -> info.xml
        #              -> main.py
        #              -> gui      -> [.ui files only]

        #Get the path to the directory that will contain the plugin folders
        plugins_path = self.settings["plugins_dir"]

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
                    "VideoInput" : Application.PLUGIN_TYPE_VIDEO_INPUT,
                    "VideoAnalysisModule" : Application.PLUGIN_TYPE_ANALYSIS,
                    "Filter": Application.PLUGIN_TYPE_FILTER
                    }

                #Get the tag name of the root element
                type_tag = doc.documentElement.localName
                #Go to the next folder if the type is not the specified
                if (plugin_type != Application.PLUGIN_TYPE_ANY and
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
            except SyntaxErr:
                traceback.print_exc()
        #Return the list containing the found plugins
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

        # The `Plugin` class holds information about the plugin.
        # The loaded_ui_objects is a list of the loaded ui objects, but these
        # ui are those located in the plugin's `ui` dir, and their names are
        # local to the 'plugin scope', thus they have their own list.

        class Plugin(object):
            def __init__(self, plugin_type, plugin_name, root_path, instance):
                self.plugin_type = plugin_type
                self.plugin_name = plugin_name
                self.root_path = root_path
                self.instance = instance
                self.loaded_ui_objects = {}
                self.gui_interface = None

        join = os.path.join
        listdir = os.listdir
        isdir = os.path.isdir
        isfile = os.path.isfile

        #A plugin folder should contain the following structure
        #
        #Plugin_Folder -> info.xml
        #              -> main.py
        #              -> ui      -> [.ui files only]

        #Get a list to the installed plugins
        plist = self.list_plugins()
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

        self.post_message("plugin_loaded",
            {"id": id_, "type": plugin.plugin_type,
            "plugin": plugin}, -1)

        return (id_, plugin)

    def unload_plugin(self, plugin_id):
        """Unload a previously loaded plugin.

        Parameters
        ----------
        plugin_id : int
            The id of the plugin to be unloaded

        Raises
        ------
        ValueError : If the plugin_id is invalid
        """
        if plugin_id in self._loaded_plugins:
            #The the Plugin instance
            plugin = self._loaded_plugins[plugin_id]
            #Call the plugins release method
            plugin.instance.release()
            #Post a message signaling that the plugin is about to be unloaded
            self.post_message("plugin_unloaded",
                {"id": id_, "type": plugin.plugin_type,
                "plugin": plugin}, -1)
            #Delete from the list
            del self._loaded_plugins[plugin_id]
        else:
            raise ValueError("No plugin with id '{}'".format(plugin_id))

    def get_plugin(self, plugin_id):
        """Return a the Plugin object correspondent to given id.

        Parameters
        ----------
        plugin_id : int
            The id of the plugin to be unloaded

        Raises
        ------
        ValueError : If the plugin_id is invalid.

        """
        if plugin_id in self._loaded_plugins:
            return self._loaded_plugins[plugin_id]
        else:
            raise ValueError("No plugin with id '{}'".format(plugin_id))

    def load_plugin_ui(self, plugin_id, name, ui_file, base_instance = None):
        """Load a ui_file from the `ui` directory of the given plugin id.

        This method loads a QtDesigner `.ui` file from the resources directory
        using the `uic` module and returns the instance. A name must be given
        for saving the instance in the plugin's dictionary. The name must
        be an alias, like 'tools', so it can be shared across the application.

        Parameters
        ----------
        plugin_id : int
            The plugin's identifier

        name : str
            The name that will be used to share the object.

        ui_file : str
            The name of the ui file located in the resources directory.
        The `.ui` extension is optional.

        base_instance : QObject, None
            The base instance to load the ui file. The default value
        is None. When its `None`, the uic module will created a new instance,
        when an proper QWidget is given, the uic will use it as a base.

        Returns
        -------
        QObject

        Raises
        ------
        IOError : If the file was not found or has an invalid format/extension.

        KeyError : If there is an already loaded ui instance with the same name

        TypeError : If the base_instance is not the same as the one in the ui
        file.

        UILoadError : If the `uic` module raises any exception
        """
        plugin = self.get_plugin(plugin_id)

        #Check if there is a loaded ui with the given name
        if name in plugin.loaded_ui_objects:
            raise KeyError("A ui with name '{}' is already loaded.".format(name))

        join = os.path.join
        isfile = os.path.isfile
        splitext = os.path.splitext

        #Extract the file extension
        fname, ext = splitext(ui_file)

        #If there is no extension, append the right one to the end
        if ext == "":
            ui_file = fname + ".ui"
        #If there is an extensions, check if its right, else raised the IOError
        else:
            if ext != ".ui":
                raise IOError(("The file name has an invalid extension"
                               "'{}'").format(ext))

        #Expand the file to the absolute path
        ui_path = join(plugin.root_path, "ui", ui_file)

        #Check if the file exists
        if not isfile(ui_path):
            raise IOError("The file '{}' does not exist.".format(ui_file))

        try:
            if base_instance:
                instance = uic.loadUi(ui_path, base_instance)
                if hasattr(instance, "setupUi"):
                    try:
                        instance.setupUi()
                    except:
                        traceback.print_exc()

                if hasattr(instance, "retranslateUi"):
                    try:
                        instance.retranslateUi()
                    except:
                        traceback.print_exc()
            else:
                instance = uic.loadUi(ui_path)

            plugin.loaded_ui_objects[name] = instance
            return instance
        except:
            print "------------------------------------------------------------"
            traceback.print_exc()
            print "------------------------------------------------------------"
            raise UILoadError()

    def get_plugin_ui(self, plugin_id, name):
        """Return the instance of a previously loaded ui file of a plugin.

        The ui object will be a QObject. To load a new a new ui file use the
        `load_plugin_ui` method.

        Parameters
        ----------
        plugin_id : int
            The identifier of the plugin

        name : str
            The ui object's name/alias.

        Returns
        -------
        QObject

        Raises
        ------
        KeyError : If there is no ui object with the given name.

        """
        plugin = self.get_plugin(plugin_id)
        if name not in plugin.loaded_ui_objects:
            raise KeyError("There is no ui object with name '{}'".format(name))
        else:
            return plugin.loaded_ui_objects[name]


    def set_language(self, locale_str):
        """Remove the current translator and install one based on the locale_str.

        This method will look for an installed qm file with the locale str pro-
        vided. If one is found it will remove the current one and install the
        new. After the installation it will call the retranslateUi for all the
        loaded ui objects. If a loaded ui object does not have the retranslateUi
        method, it will just ignore it.

        Parameters
        ----------
        locale_str : str
            A str containing the locale, i.e. "pt_BR", "en_US". It can also be
            "default" and if so, the current translator will be removed and the
            language will be send to default.
        """
        join = os.path.join
        isfile = os.path.isfile

        #This the path where the qm file should be located if installed
        #`lang_dir`/qm/`locale_str`.qm
        qm_file = join(self.settings["lang_dir"], "qm", locale_str+".qm")

        #Check if the locale is "default" or if the qm file for the given str
        #does exist.
        if isfile(qm_file) or locale_str == "default":
            #Remove the current translator if there is one installed
            if self._translator is not None:
                self._qapp.removeTranslator(self._translator)
                self._translator = None

            #If the qm file exists, load it and install the translator to the
            #QApplication instance
            if isfile(qm_file):
                self._translator = QTranslator()
                self._translator.load(qm_file)
                self._qapp.installTranslator(self._translator)

            #Call the retranslanteUi method of all the loaded ui objects that
            #have it.
            for ui in self._loaded_ui_objects.values():
                if hasattr(ui, "retranslateUi"):
                    try:
                        ui.retranslateUi()
                    except:
                        traceback.print_exc()

            #Translate the loaded ui objects of the plugins
            for plugin in self._loaded_plugins.values():
                for ui in plugin.loaded_ui_objects:
                    if hasattr(ui, "retranslateUi"):
                        try:
                            ui.retranslateUi()
                        except:
                            traceback.print_exc()

                if plugin.gui_interface is not None:
                    plugin.gui_interface.retranslateUi()
            #Post an anonymous message signaling the language change
            self.post_message("language_changed", {"locale_str": locale_str}, -1)

        #If the file does not exist nor the string is equals to "default", raise
        #an error
        else:
            raise ValueError("There is no locale '{}' installed".format(locale_str))

    def exec_(self):
        """Just wrappers the QApplication instance `exec_` method.

        """
        return self._qapp.exec_()

    def release(self):
        #TODO
        pass
