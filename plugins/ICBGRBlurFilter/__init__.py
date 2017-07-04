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

import numpy as np
import cv2

import plugin_object

LOG = logging.getLogger(__name__)

TYPE = "filter"

INFO = {
        "author": [u"Imagem Cinemática"],
        "version": u"1.0.0",
        "title": u"Blur Filter",
        "shortname": u"Blur",
        "description": u"Apply the CV2 Blur Filter."
        }

COLORSPACE = {
              "in": "BGR",
              "out": "BGR"
              }

def main(*args, **kwargs):
    return plugin_object.ICBlurFilter(**kwargs)
