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
import os

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QCoreApplication, QString
from PyQt4 import uic

from ic import settings

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig = ""):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig = ""):
        return QApplication.translate(context, text, disambig)


def tr(*args, **kwargs):
    return _translate(*args, **kwargs)

def load_ui(file_path, base_object=None):
    file_path = file_path+".ui" if file_path[-3:] != ".ui" else file_path
    path = os.path.normpath(os.path.join(settings.get("resources_dir"), "ui", file_path))
    return uic.loadUi(path, base_object)
