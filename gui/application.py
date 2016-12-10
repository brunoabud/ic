# coding: latin-1
# Copyright (C) 2016  Bruno Abude Cardoso
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
"""Contains the Application class that shares global states to the entire app.

"""
import sys
import os
from Queue import Queue
from weakref import WeakValueDictionary
from importlib import import_module
import imp
import logging

from PyQt4.QtCore import  (QTimer, QTranslator) #pylint: disable=no-name-in-module
from PyQt4.QtGui import QApplication #pylint: disable=no-name-in-module
from PyQt4 import uic

from util import find_free_key


LOG = logging.getLogger(__name__)
_DEBUG_MESSAGES = False

class UILoadError(Exception):
    """Raised when the uic module fails to load an ui file.

    """
    pass


class InvalidMessageReceiverError(Exception):
    """Raised when the object provided doesn't have the receive_message method.

    """
    pass


def get_app():
    """Return the unique instance of the Application class.

    """
    return Application.instance()


class Application(object):
    """The Main application class.

    The Application class is responsible for holding global data that will be
    shared between the whole application. It also provides a message dispatching
    system for intercommunication and methods for loading resources.

    This class is a singleton. The instance can be retrived by the function
    get_app avaible in the module `application`.

    Attributes:
      settings: a dictionary containing application-wide settings.
      user_options: a dictionary containing options that can be changed by
        user when interacting with the GUI.
    """
    _INSTANCE = None
    PATH = ""
    # This option tells the application to pump raw frames to the preview queue
    OPT_PREVIEW_RAW = 0x1
    # This options tells the application to pump frames right after they got
    # processed by the analysis plugin
    OPT_PREVIEW_POST_ANALYSIS = 0x2
    OPT_PREVIEW_FILTER_PAGE = 0x3

    def __init__(self, argv):
        assert Application._INSTANCE is None
        Application._INSTANCE = self

        self._qapp = QApplication(argv)

        pjoin = os.path.join

        # The application main path (the local where the main script was
        # invoked by the interpreter)
        Application.PATH = sys.path[0]

        self.settings = {
            # The max frames that can be put in the raw queue
            'raw_queue_len' : 1,
            # The max frames that can be put in the preview queue
            'preview_queue_len' : 1,
            # The directory of the installed plugins
            'plugins_dir' : pjoin(self.PATH, 'plugins'),
            # The directory of the application resources (imgs, icons, ui, etc.)
            'resources_dir' : pjoin(self.PATH, 'resources'),
            # Max time to wait for a worker thread to finish
            'thread_wait_timeout': 500,
            'lang_dir' : pjoin(self.PATH, 'lang')
        }
        # Holds all the ui files loaded by calling the method load_ui.
        self._loaded_ui_objects = {}
        # Holds all imported resources modules name
        self._loaded_resources = {}
        # A thread-safe queue that contains the messages to be dispatched
        self._messages = Queue()
        # A set containing all the objects that can receive messages.
        # Each element of this set is a tuple containing an unique identifier
        # and the object itself.
        self._message_listeners = WeakValueDictionary()
        # The timer that is responsible for dispatching the messages
        self._message_timer = QTimer()
        self._message_timer.setInterval(20)
        self._message_timer.timeout.connect(self._dispatch_messages)
        self.user_options = {
            "preview_source": Application.OPT_PREVIEW_POST_ANALYSIS,
            "filter_group"  : "Raw"
            }
        # Current installed QTranslator
        self._translator = None
        self._message_timer.start()

    @classmethod
    def instance(cls):
        """Return the singleton instance of the Application class.

        """
        return cls._INSTANCE

    def get_ui(self, name):
        """Return the instance of a previously loaded ui file.

        The ui object will be a QObject. To load a new a new ui file use the
        `load_ui` method.

        Args:
          name (str): the ui object's name/alias.

        Returns:
          QObject: the object that was created when the correspondent ui file
            was loaded.

        Raises:
          KeyError: if there is no ui object with the given name.

        """
        if name not in self._loaded_ui_objects:
            raise KeyError("No ui object loaded with that name.")
        else:
            return self._loaded_ui_objects[name]

    def load_ui(self, name, ui_file, base_instance=None):
        """Load a .ui file from the resources directory and return it.

        This method loads a QtDesigner `.ui` file from the resources directory
        using the `uic` module and returns the instance. A name must be given
        for saving the instance in the application's dictionary. The name must
        be an alias, like 'main_window' or `console_window` so it can be shared
        across the application.

        Args:
          name (str): The name that will be used to share the object between the appli-
            cation modules. If the string is empty, the ui object will be returned
            but not saved in the dictionary.
          ui_file (str): The name of the ui file located in the resources
            directory. The `.ui` extension is optional.
          base_instance (QObject): The base instance to load the ui file. The
            default value is None. When it's `None`, the uic module will created
            a new instance, when an proper QWidget is given, the uic will use it
            as a baseclass.

        Returns:
          QObject: The QObject file described by the ui file.

        Raises:
          IOError: If the file was not found or has an invalid format/extension.
          KeyError: If there is an already loaded ui instance with the same name
          TypeError: If the base_instance is not the same as the one in the ui
            file.
          UILoadError: If the `uic` module raises a exception
        """
        if name in self._loaded_ui_objects:
            raise KeyError("A ui with that name is already loaded")

        join = os.path.join
        isfile = os.path.isfile
        splitext = os.path.splitext

        fname, ext = splitext(ui_file)

        if ext == "":
            ui_file = fname + ".ui"
        else:
            if ext != ".ui":
                raise IOError("File extension must be .ui")
        ui_path = join(self.settings["resources_dir"], "ui", ui_file)
        if not isfile(ui_path):
            raise IOError("The file x does not exist.")
        try:
            if base_instance is not None:
                instance = uic.loadUi(ui_path, base_instance)
                if hasattr(instance, "setupUi"):
                    try:
                        instance.setupUi()
                    except: #pylint: disable=bare-except
                        LOG.error("Error when setting up ui", exc_info=True)

                if hasattr(instance, "retranslateUi"):
                    try:
                        instance.retranslateUi()
                    except: #pylint: disable=bare-except
                        LOG.error("Error when retranslating ui", exc_info=True)
            else:
                instance = uic.loadUi(ui_path)

            if name.strip() != '':
                self._loaded_ui_objects[name] = instance
            return instance
        except Exception:
            LOG.error("Error when loading ui file", exc_info=True)
            raise UILoadError()


    def register_message_listener(self, listener):
        """Register a object so the application dispatch messages to it.

        The message listener is registered using a Weak Reference, so the
        messages system will not keep the objects alive when all the other
        references are deleted.

        Args:
          listener: the object that will receive the message.

        Returns:
          int: an unique identifier to use when referencing to this listener in
          the messages system.

        Raises:
          ValueError: if the listener object is already registered.
        """
        for ref in self._message_listeners.itervaluerefs():
            if ref() is listener:
                raise ValueError("The object is already registered")
        id_ = find_free_key(self._message_listeners)
        self._message_listeners[id_] = listener
        return id_

    def unregister_message_listener(self, identifier):
        """Tell the pplication to stop dispatching messages to a listener.

        Args:
          identifier (int): The identifier of the listener that will stop
            receiving messages.

        Raises:
          ValueError: If there is no listener object with the given identifier.

        """
        try:
            del self._message_listeners[identifier]
        except KeyError:
            raise ValueError("There is no listener with given id")

    def get_message_listener_instance(self, identifier):
        """Return a registered message listener object with the given identifier.

        Args:
          identifier(int): The unique identifier of the listener object.

        Returns:
          object: The instance of the listener.

        Raises:
          ValueError: If there is no listener object with the given identifier.

        """
        try:
            return self._message_listeners[identifier]
        except KeyError:
            raise ValueError(("There is no message listener"
                              "registered with given id"))

    def post_message(self, message_type, message_data, sender):
        """Post a message to the messages system.

        Args:
          message_type (str): A string containing a name/tag/alias for th
            message type. It should be lowercase and have no leading/trailing
            spaces. The string will be trimmed and changed to lower case anyway.

          message_data: Any kind of object, the listeners should rely on the
            documentation of the message type.

          sender_id (int): The unique identifier of the sender. This will
            prevent the sender to receiving it's own message. If the value is
            `-1`, the message will be considered anonymous.

        """
        self._messages.put((message_type.lower().strip(), message_data, sender))

    def _dispatch_messages(self):
        """Dispatch all the messages in the queue to the registered listeners.

        """
        # Create strong references to the listeners
        items = self._message_listeners.items()
        while not self._messages.empty():
            mtype, mdata, sender = self._messages.get(False)
            if _DEBUG_MESSAGES:
                LOG.debug("<%d, %s>: '%s'", sender, mtype, str(mdata))
            for (recipient, instance) in items:
                if recipient == sender:
                    continue
                try:
                    instance.receive_message(mtype, mdata, sender)
                except: #pylint: disable=bare-except
                    LOG.error("The listener with id %d raised an exception when"
                              " receiving a message and will be removed from"
                              " the list.", recipient)
                    del self._message_listeners[recipient]

    def import_resources(self):
        """Load the resource files contained in the gui package path.

        """
        _, path, _ = imp.find_module("gui")
        # Bugfix for OSX
        if path not in sys.path:
            sys.path.append(path)
        for mod in (f for f in os.listdir(path) if f.endswith("_rc.py")):
            try:
                imported = import_module(mod[:-3])
                self._loaded_resources[mod] = imported
            except ImportError:
                LOG.error("Error when importing resource file %s", mod,
                          exc_info=True)

    def load_plugin_ui(self, plugin_id, name, ui_file, base_instance=None):
        """Load a ui_file from the `ui` directory of the given plugin id.

        This method loads a QtDesigner `.ui` file from the plugin `ui` directory
        using the `uic` module and returns the instance. A name must be given
        for saving the instance in the plugin's ui dictionary. The name must
        be an alias, like 'tools', so it can be shared across the application.

        Args:
          plugin_id (int): The plugin's identifier.
          name (str): The name that will be used to share the object. If name is
            an empty sting, the object will not be saved to the dictionary.
          ui_file (str): The name of the ui file located in the ui directory.
            The `.ui` extension is optional.
          base_instance (QObject): The base instance to load the ui file. The
            default value is None. When its `None`, the uic module will created
            a new instance, when an proper QWidget is given, the uic will use
            it as a base.

        Returns:
          QObject: The loaded QObject.

        Raises:
          IOError: If the file was not found or has an invalid format/extension.
          KeyError: If there is an already loaded ui instance with the same name.
          TypeError: If the base_instance is not the same as the one in the ui
           file.
          UILoadError: If the `uic` module raises an exception.
        """
        # Temporary solution for solving circular dependencies
        engine = sys.modules["ic.engine"]
        plugin = engine.get_plugin(plugin_id)

        if name in plugin.loaded_ui_objects:
            raise KeyError("A ui with the given name ")

        join = os.path.join
        isfile = os.path.isfile
        splitext = os.path.splitext

        fname, ext = splitext(ui_file)
        if ext == "":
            ui_file = fname + ".ui"
        else:
            if ext != ".ui":
                raise IOError("The file name has an invalid extension")
        ui_path = join(plugin.root_path, "ui", ui_file)
        if not isfile(ui_path):
            raise IOError("The given file does not exist.")
        try:
            if base_instance:
                instance = uic.loadUi(ui_path, base_instance)
                if hasattr(instance, "setupUi"):
                    try:
                        instance.setupUi()
                    except: #pylint: disable=bare-except
                        LOG.error("Error when calling plugin ui object"
                                  " setupUi method.", exc_info=True)

                if hasattr(instance, "retranslateUi"):
                    try:
                        instance.retranslateUi()
                    except: #pylint: disable=bare-except
                        LOG.error("Error when calling plugin ui object"
                                  " retranslateUi method.", exc_info=True)
            else:
                instance = uic.loadUi(ui_path)
            if name:
                plugin.loaded_ui_objects[name] = instance
            return instance
        except:
            raise UILoadError()

    def get_plugin_ui(self, plugin_id, name):
        """Return the instance of a previously loaded ui file of a plugin.

        The ui object will be a QObject. To load a new a new ui file use the
        `load_plugin_ui` method.

        Args:
          plugin_id (int): The unique identifier of the plugin.
          name (str): The ui object's name/alias.

        Returns:
          QObject: The loaded QObject.

        Raises:
          KeyError: If there is no ui object with the given name.

        """
        # Temporary solution for solving circular dependencies errors
        engine = sys.modules["ic.engine"]
        plugin = engine.get_plugin(plugin_id)
        if name not in plugin.loaded_ui_objects:
            raise KeyError("There is no ui object with given name")
        else:
            return plugin.loaded_ui_objects[name]


    def set_language(self, locale_str):
        """Remove the current translator and install one based on the locale_str.

        This method will look for an installed qm file with the locale str pro-
        vided. If one is found it will remove the current one and install the
        new. After the installation it will call the retranslateUi for all the
        loaded ui objects. If a loaded ui object does not have the retranslateUi
        method, it will just ignore it.

        Args:
          locale_str (str): The locale code, i.e. "pt_BR", "en_US". It can also
            be "default" and if so, the current translator will be removed and
            the language will be send to default (en_US).

        Raises:
          ValueError: If there is no locale installed with the given code.
        """
        # Temporary solution for solving circular dependencies errors
        engine = sys.modules["ic.engine"]
        join = os.path.join
        isfile = os.path.isfile

        qm_file = join(self.settings["lang_dir"], "qm", locale_str+".qm")

        if isfile(qm_file) or locale_str == "default":
            if self._translator is not None:
                self._qapp.removeTranslator(self._translator)
                self._translator = None
            if isfile(qm_file):
                self._translator = QTranslator()
                self._translator.load(qm_file)
                self._qapp.installTranslator(self._translator)
            for ui in self._loaded_ui_objects.values():
                if hasattr(ui, "retranslateUi"):
                    try:
                        ui.retranslateUi()
                    except: #pylint: disable=bare-except
                        LOG.error("Error when calling retranslateUi method for"
                                  " ui object.", exc_info=True)

            for plugin in engine.loaded_plugins().values():
                for ui in plugin.loaded_ui_objects:
                    if hasattr(ui, "retranslateUi"):
                        try:
                            ui.retranslateUi()
                        except: #pylint: disable=bare-except
                            LOG.error("Error when calling retranslateUi method for"
                                      " ui object.", exc_info=True)

                if plugin.gui_interface is not None:
                    plugin.gui_interface.retranslateUi()
            # Post an anonymous message signaling the language change
            self.post_message("language_changed", {"locale_str": locale_str}, -1)
        else:
            raise ValueError("There is no locale installed with the given code")

    def exec_(self):
        """Wraps the QApplication instance `exec_` method.

        """
        return self._qapp.exec_()

    def release(self):
        """Releases all resources used by the application.

        """
        pass
