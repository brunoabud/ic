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

from ic import log as ic_log

ERROR_ENGINE_INITIALIZATION = ("Error when initializing the engine module.")
ERROR_MAIN_MODULE_IMPORT = ("Error when importing a main module.")
ERROR_APPLICATION_INIT = ("Error when creating the application object.")
ERROR_MAIN_WINDOW_LOAD = ("Error when loading the main window.")

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
    try:
        from gui import application
        from gui.main_window import MainWindow
        from ic import engine
        from ic.filter_rack import FilterRack
        from ic.frame_stream import FrameStream
        from ic.video_source import VideoSource
    except:
        LOG.critical(ERROR_MAIN_MODULE_IMPORT, exc_info=True)
        sys.exit(ERROR_MAIN_MODULE_IMPORT)
    try:
        app = application.Application(sys.argv)
    except:
        LOG.critical(ERROR_APPLICATION_INIT, exc_info=True)
        sys.exit(ERROR_APPLICATION_INIT)
    try:
        engine.init()
        engine.get_engine().load_component("filter_rack", FilterRack)
        engine.get_engine().load_component("frame_stream", FrameStream, 1, 1)
        engine.get_engine().load_component("video_source", VideoSource)
    except:
        LOG.critical(ERROR_ENGINE_INITIALIZATION, exc_info=True)
        sys.exit(ERROR_ENGINE_INITIALIZATION)
    try:
        app.import_resources()
        main_window = app.load_ui("main_window", "main_window.ui", MainWindow())
        main_window.show()
    except:
        LOG.error("Error when importing resources, some things may not be properly shown.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    create_logger()
    main()
