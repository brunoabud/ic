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

import cv2

class ICAdaptiveThreshold(object):
    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.parameters = [
                           ("max_value", u"Max Pixel Value", "int", 0, 255, 1, 255),
                           ("kernel_size", u"Kernel Size", "int", 1, 31, 1, 3),
                           ("threshold_c", u"Threshold Constant", "int", 0, 10, 1, 2)
                          ]

        self.v = {}
        self.v["max_value"] = 255
        self.v["kernel_size"] = 3
        self.v["threshold_c"] = 2

    def parameter_changed(self, param_name, value):
        if param_name == "kernel_size":
            self.v["kernel_size"] = value | 1
            return self.v["kernel_size"]
        else:
            self.v[param_name] = value
            return value

    def apply_filter(self, frame):
        colorspace, data, pos, timestamp = frame
        data = cv2.adaptiveThreshold(data, self.v["max_value"],
    		              cv2.ADAPTIVE_THRESH_MEAN_C,
                          cv2.THRESH_BINARY_INV,  self.v["kernel_size"],
                         self.v["threshold_c"])
        return (colorspace, data)

    def release_plugin(self, error_level=0):
        pass

