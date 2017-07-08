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

class ICGRAY2BGR(object):
    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.parameters = []

    def parameter_changed(self, param_name, value):
        return None

    def apply_filter(self, frame):
        colorspace, data, pos, timestamp = frame
        data = cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
        return ("BGR", data)

    def release_plugin(self, error_level=0):
        pass

