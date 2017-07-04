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

import cv2

class ICDilateFilter(object):
    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.parameters =[
                           ("kernel_size", u"Kernel Size", "int", 3, 99, 1, 3),
                           ("kernel_steps", u"Dilatation Steps", "int", 3, 99, 4, 1)
                         ]
        self.v = {}
        self.v["kernel_size"] = 3
        self.v["kernel_steps"] = 4

    def parameter_changed(self, param_name, value):
        if param_name == "kernel_size":
            self.v["kernel_size"] = value | 1
            return self.v["kernel_size"]
        else:
            self.v[param_name] = value
            return value

    def apply_filter(self, frame):
        colorspace, data, pos, timestamp = frame
        kernel     = np.ones((self.v["kernel_size"],)*2, np.uint8)
        data = cv2.dilate(data, kernel, iterations=self.v["kernel_steps"])
        return (colorspace, data)

    def release_plugin(self, error_level=0):
        pass

