#!/usr/bin/env python
# coding: latin-1
# Imagem Cinemática is a free software intended to be used as a tool for teachers
# and students. It utilizes Computer Vision techniques to extract the trajectory
# of moving objects from video data.
#
# The code contained in this project follows the Google Python Style Guide
# Revision 2.59.
# The specifics can be found at http://google.github.io/styleguide/pyguide.html
#
#
# Copyright (C) 2016  Bruno Abude Cardoso
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
"""Module responsible for loading the main components of the application.

"""
import sys
import logging
import os

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import Qt
from ic import log as ic_log

LOG = None

def create_logger():
    """Set up the logging utility, using the formatter that best matches the OS.

    """
    global LOG
    handler = logging.StreamHandler()
    root_logger = logging.getLogger()
    if sys.platform == "linux2":
        handler.setFormatter(ic_log.ANSIFormatter())
    else:
        handler.setFormatter(ic_log.ColorlessFormatter())
    root_logger.addHandler(handler)
    handler.setLevel(logging.DEBUG)
    root_logger.setLevel(logging.NOTSET)
    # Filter out the annoying PyQt4 logging messages
    handler.addFilter(ic_log.NameFilter("PyQt4"))
    LOG = logging.getLogger(__name__)

def main():
    from gui import application
    from gui import main_window
    from ic import engine
    from ic import plugin
    from ic import settings
    from ic import messages

    settings.change("app_path", sys.path[0])

    app = application.Application(sys.argv)
    messages.start_timer()
    mainwindow = main_window.MainWindow()
    desktop = QApplication.desktop().screen()
    mainwindow.show()
    mainwindow.move(mainwindow.frameGeometry().left()-mainwindow.geometry().left(), 0)
    mainwindow.resize(desktop.frameGeometry().width(), 150)
    bordas = mainwindow.frameGeometry().width() - mainwindow.geometry().width()
    mainwindow.filter_rack_window.move(0, mainwindow.frameGeometry().bottom())
    app.exec_()
if __name__ == "__main__":
    create_logger()
    main()
