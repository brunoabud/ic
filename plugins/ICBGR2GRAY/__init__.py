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

from plugin_object import ICBGR2GRAY

TYPE = "filter"
INFO = {
        "title": u"BGR to GRAY Colorspace Converter",
        "author": [u"Bruno Abude Cardoso"],
        "description": "Change the input colorspace from BGR to GRAY",
        "shortname": "BGR to Gray",
        "version": "1.0.0"
        }
COLORSPACE = {
              "in": "BGR",
              "out": "GRAY"
              }
              
def main(**kwargs):
    return ICBGR2GRAY(plugin_path=kwargs["plugin_path"])
