import sys
import logging

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QTimer, QCoreApplication
import colorama

import ic.log
from ic import engine

# Error Codes
ERROR_ENGINE_INITIALIZATION = 0x001
ERROR_MAIN_MODULE_IMPORT    = 0x002
ERROR_APPLICATION_INIT      = 0x003
ERROR_MAIN_WINDOW_LOAD      = 0x004

if __name__ == "__main__":
    # Init the logging utilities
    handler   = logging.StreamHandler()
    formatter = ic.log.ANSIFormatter()
    root    = logging.getLogger()
    # Setup the handler formater and level
    handler.setFormatter(formatter)
    root.addHandler(handler)
    handler.setLevel(logging.DEBUG)
    root.setLevel(logging.NOTSET)
    # Filter out the PyQt4 logging messages
    handler.addFilter(ic.log.NameFilter("PyQt4"))

    log = logging.getLogger(__name__)
    # Import all main modules
    try:
        from gui             import application
        from ic.video_source import VideoSource
        from ic.frame_stream import FrameStream
        from ic.filter_rack  import FilterRack
        from gui.main_window import MainWindow
    except:
        log.critical("Error when importing a main module", exc_info=True)
        sys.exit(ERROR_MAIN_MODULE_IMPORT)

    # Create the application object
    try:
        app = application.Application(sys.argv)
    except:
        log.critical("Error when creating the Application object", exc_info=True)
        sys.exit(ERROR_APPLICATION_INIT)

    # Initialize the engine and load main components
    try:
        log.debug("Initialiazing Engine...")
        engine.init()
        engine.load_component("filter_rack", FilterRack)
        engine.load_component("video_source", VideoSource)
        engine.load_component("frame_stream", FrameStream, 1, 1)
        log.debug("Engine initialized")
    except:
        log.critical("A engine main component could not be initialized.", exc_info=True)
        app.exit(ERROR_ENGINE_INITIALIZATION)

    # Import all the resource modules inside the gui package
    try:
        app.import_resources()
    except:
        log.error("Error when importing resources, some things may not be properly shown")


    # Load the Main Window
    try:
        mainWindow = app.load_ui("main_window", "mainWindow.ui", MainWindow())
        mainWindow.show()
    except:
        log.critical("Error when loading the main window", exc_info=True)
        sys.exit(ERROR_MAIN_WINDOW_LOAD)

    sys.exit(app.exec_())
