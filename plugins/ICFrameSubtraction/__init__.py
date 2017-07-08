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

from plugin_object import ICFrameSubtraction

TYPE = "analysis"
INFO = {
        "title": "Frame Subtraction",
        "author": ["Bruno Abude Cardoso", "Gustavo Voltani Von Atzingen"],
        "description": "Movement detection by frame subtraction",
        "version": "1.0.0"
        }

COLORSPACE = {"in": "BGR"}

FILTER_PAGES = {
                "Pre-Filter": {"in": "BGR", "out": "GRAY", "filters": ["ICBGR2GRAY", "ICGrayBlurFilter"]},
                "Threshold": {"in": "GRAY", "out": "GRAY", "filters": ["ICGrayBlurFilter", "ICAdaptiveThreshold"]},
                "Post-Filter": {"in": "GRAY", "out": "GRAY", "filters": ["ICGrayBlurFilter"]},
                "Dilatation": {"in": "GRAY", "out": "BGR", "filters": ["ICDilateFilter", "ICGRAY2BGR"]}
               }
def main(**kwargs):
    return ICFrameSubtraction(plugin_path=kwargs["plugin_path"])
