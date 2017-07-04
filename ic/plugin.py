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

import logging
from xml.dom import Node, minidom
import sys
import os
import imp

from ic import settings

LOG = logging.getLogger(__name__)

class PluginInitError(Exception):
    pass


class PluginNotInstalled(Exception):
    pass


class InvalidPluginType(Exception):
    pass


class Plugin(object):
    def __init__(self, pid, plugin_object, plugin_package):
        self.pid = pid
        self._object = plugin_object
        self._package = plugin_package

    def __getattr__(self, name):
        return getattr(self._object, name)

    def package(self):
        return sys.modules[self._package]

class FilterPlugin(Plugin):
    def __init__(self, pid, plugin_object, plugin_package,
            colorspace, shortname):
        super(FilterPlugin, self).__init__(pid, plugin_object, plugin_package)
        self.colorspace = (colorspace["in"], colorspace["out"])
        self.shortname = shortname
        self.ignore = False
        # Error flags set by the FilterRack to signal that the filter has a flow error
        self.input_status = True
        self.output_status = True


class InputPlugin(Plugin):
    def __init__(self, pid, plugin_object, plugin_package,
            colorspace, gui_interface, bridge):
        super(InputPlugin, self).__init__(pid, plugin_object, plugin_package)
        self.colorspace = colorspace
        self.gui_interface = gui_interface
        self.bridge = bridge

        if not plugin_object.init_plugin(gui_interface=gui_interface,
                                  video_source_bridge=bridge):
            plugin_object.release_plugin(1)
            gui_interface.release()
            raise PluginInitError()


class AnalysisPlugin(Plugin):
    def __init__(self, pid, plugin_object, plugin_package,
            colorspace, gui_interface, filter_rack):
        super(AnalysisPlugin, self).__init__(pid, plugin_object, plugin_package)
        self.colorspace = colorspace
        self.gui_interface = gui_interface

        if not plugin_object.init_plugin(gui_interface=gui_interface,
                                         filter_rack=filter_rack):
            plugin_object.release_plugin(1)
            gui_interface.release()
            raise PluginInitError()


def id_generator():
    i = 0
    while True:
        i += 1
        yield i

next_id = iter(id_generator()).next

def plugins_dir():
    return os.path.join(settings.get("app_path"), "plugins")

def load(package, **kwargs):
    # Locate the package
    f, p, d = imp.find_module(package, [plugins_dir()])

    module = imp.load_module(package, f, p, d)
    plugin_object = module.main(plugin_path=p)

    if module.TYPE == "input":
        p = InputPlugin(next_id(), plugin_object, package,
                module.COLORSPACE["out"], kwargs["gui_interface"],
                kwargs["video_source_bridge"])
        return p
    elif module.TYPE == "filter":
        p = FilterPlugin(next_id(), plugin_object, package,
                module.COLORSPACE, module.INFO["shortname"])
        return p
    elif module.TYPE == "analysis":
        p = AnalysisPlugin(next_id(), plugin_object, package,
                module.COLORSPACE["in"], kwargs["gui_interface"],
                kwargs["filter_rack"])
        return p
    else:
        raise InvalidPluginType()

def list_all(plugin_type=None):
    plugins = []
    for d in os.listdir(plugins_dir()):
        try:
            f, p, d_ = imp.find_module(d, [plugins_dir()])
            m = imp.load_module(d, f, p, d_)
            if not plugin_type or plugin_type == getattr(m, "TYPE"):
                plugins.append(m)
        except Exception as e:
            LOG.debug("Ignoring filter '%s'", d, exc_info=True)
    return plugins

