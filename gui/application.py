# coding: utf-8
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
import imp
import logging
import imp
from importlib import import_module
from imp import find_module

from PyQt4.QtCore import  (QTimer, QTranslator)
from PyQt4.QtGui import QApplication
from PyQt4 import uic

from ic import messages
from ic import engine
from ic import settings

LOG = logging.getLogger(__name__)

class UILoadError(Exception):
    """Raised when the uic module fails to load an ui file.

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

    def __init__(self, argv):
        assert Application._INSTANCE is None
        Application._INSTANCE = self

        self._qapp = QApplication(argv)

        pjoin = os.path.join

        # The application main path (the local where the main script was
        # invoked by the interpreter)
        Application.PATH = sys.path[0]

        settings.change("resources_dir", pjoin(self.PATH, "res"))
        settings.change("lang_dir", pjoin(self.PATH, "lang"))
        # Holds all the ui files loaded by calling the method load_ui.
        self._loaded_ui_objects = {}
        # Holds all imported resources modules name
        self._loaded_resources = {}
        # Current installed QTranslator
        self._translator = None

        if settings.get("locale_str"):
            self.set_language(settings.get("locale_str"))

        self.import_resources()

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
        join = os.path.join
        isfile = os.path.isfile

        qm_file = join(settings.get("lang_dir"), "qm", locale_str+".qm")

        if isfile(qm_file) or locale_str == "default":
            if self._translator is not None:
                self._qapp.removeTranslator(self._translator)
                self._translator = None
            if isfile(qm_file):
                self._translator = QTranslator()
                self._translator.load(qm_file)
                self._qapp.installTranslator(self._translator)
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
