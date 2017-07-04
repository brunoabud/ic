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
import numpy as np

class ICBlurFilter(object):
    def __init__(self, **kwargs):
        self.plugin_path = kwargs["plugin_path"]
        self.parameters = [
                           ("kernel_size", u"Kernel Size", "int", 1, 15, 1, 3)
                          ]


        self.kernel_size = 3

    def parameter_changed(self, param_name, value):
        if param_name == "kernel_size":
            self.kernel_size = value | 1
            return self.kernel_size
        else:
            return None

    def apply_filter(self, frame):
        colorspace, data, pos, timestamp = frame
        data = cv2.blur(data, (self.kernel_size,)*2)
        return (colorspace, data)

    def release_plugin(self):
        return True

