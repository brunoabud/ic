#coding: utf-8
r"""This module can list, load and retrieve information about plugins."""

__all__     = ['load_plugin', 'list_plugins', 'get_plugin_info', 'PluginLoadError']
__author__  = "Bruno Abude Cardoso"
__version__ = "0.4.0"

from xml.dom import minidom as dom
from xml.dom import Node
from importlib import import_module
import os
import sys

from enum import Enum

import log
import main


class PluginType(Enum):
    r"""Enum containing the type of plugin objects."""
    Any = 1
    VideoInput = 2
    VideoAnalysis = 3
    Filter = 4


class PluginLoadError(Exception):
    pass


def load_plugin(plugin_dir, plugin_name):
    r"""Call the main() method of the plugin module and return the plugin object.

    Parameters
    ----------
    plugin_dir  : str
        The directory where the plugin files are located
    plugin_name : str
        The name of the module containing the plugin

    Returns
    -------
    plugin : object
        The plugin object has it's own class so the type is not checked. It must follow the
        Plugin Model

    Raises
    ------
    PluginLoadError
        If an error ocurred and the plugin could not be loaded


    """
    try:
        plugin_dir = str(plugin_dir)
        #Allows the import_module to look for the plugin module inside the plugin_dir
        sys.path.append(plugin_dir)
        plugin_module = import_module(plugin_name)
        main = getattr(plugin_module, 'main')
        plugin = main()
        return plugin
    except:
        log.dump_traceback()
        raise PluginLoadError()
    finally:
        sys.path.remove(plugin_dir)

def list_plugins(plugin_dir, plugin_type = PluginType.Any):
    r"""List all the plugins inside the plugin_dir of the specified type.

    Parameters
    ----------
    plugin_dir  : str
        The directory where the plugin files are located
    plugin_type : PluginType enum
        The type of the plugins to list. The default value (Any) searchs for any type of plugin

    Returns
    -------
    list of str
        List containing the names of plugins found inside the dir of the specified type

    """
    try:
        plugin_dir = str(plugin_dir)
        #Allows the import_module to look for the plugin module inside the plugin_dir
        sys.path.append(plugin_dir)
        plugins = []
        #Iterate through all the xml files of the dir
        for xml_file in [f for f in os.listdir(plugin_dir) if f.lower().endswith('.xml')]:
            #Remove the '.xml' to get the plugin name
            name = xml_file[:-4]
            #Ignore this name if there is not a python file with same name of the xml file
            if not os.path.isfile(os.path.join(plugin_dir, name + '.py')): continue
            try:
                module = import_module(name)
            except:
                log.dump_traceback()
                continue
            if not hasattr(module, 'main'):
                Log.write("Plugin '{}' module has no main() method".format(plugin_name))
                continue
            if plugin_type is PluginType.Any:
                plugins.append(name)
            else:
                try:
                    doc = dom.parse(os.path.join(plugin_dir, f))
                    if doc.documentElement.localName == plugin_type.name: plugins.append(name)
                except:
                    log.dump_traceback()
        return plugins
    except:
        log.dump_traceback()
        return []
    finally:
        sys.path.remove(plugin_dir)

def get_plugin_info(plugin_dir, plugin_name):
    """Return a dict containing the informations provided by the plugin's xml file.

    Parameters
    ----------
    plugin_dir  : str
        The directory where the plugin files are located
    plugin_name : str
        The name of the plugin module

    Returns
    -------
    dict
        The dictionary contains the keys `name`, `Author`, `Title`, `Version` and `Description`.

    """
    try:
        plugin_dir   = str(plugin_dir)
        plugin_name  = str(plugin_name)
        info         = {}
        doc          = dom.parse(os.path.join(plugin_dir, plugin_name+'.xml'))
        info_tags    = ['Author', 'Title', 'Version', 'Description']
        info         = {tag:doc.getElementsByTagName(tag)[0].childNodes[0].nodeValue for tag in info_tags}
        info['name'] = plugin_name
        return info
    except:
        log.dump_traceback()
        return None
