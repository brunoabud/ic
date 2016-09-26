#coding: utf-8
import sys
import os
from xml.dom import Node, minidom
from xml.dom.minidom import Document
import logging
log = logging.getLogger("ICFileInput")

from PyQt4.QtGui import QFileDialog, QMessageBox, QPushButton, QGridLayout, QWidget
from PyQt4.QtGui import QLabel, QInputDialog
from PyQt4.QtCore import QObject, pyqtSignal, Qt, pyqtSlot
from PyQt4 import QtGui, QtCore
from cv2 import VideoCapture
import cv2

from gui import tr

INFO_FROM_OPENCV  = 0x1
INFO_FROM_FFPROBE = 0x2
INFO_FROM_DEFAULT = 0x3

info_source = 0x0

# Define the function that will be used to read the media info
try:
    import ffmpy
    # Check if the ffprobe executable was found
    probe = ffmpy.FFprobe(global_options="-version")
    probe.run()
    info_source = INFO_FROM_FFPROBE
    log.info("Using ffprobe to get media info")
except ImportError:
    log.warning("ffmpy library not found, using OpenCV methods for getting media info")
    info_source = INFO_FROM_OPENCV
except ffmpy.FFExecutableNotFoundError:
    log.warning("ffprobe executable not found, using OpenCV methods for getting media info")
    info_source = INFO_FROM_OPENCV

def get_info_ffprobe(path):
    # Check if the file exists
    if not os.path.isfile(path):
        raise OSError("file {} not found".format(path))
    # Execute the ffprobe and get the xml data
    probe = ffmpy.FFprobe(inputs={path:"-print_format xml -show_streams -select_streams v:0"})
    xml_data = probe.run()
    # Parse from string
    doc = minidom.parseString(xml_data)
    # Collect the stream node
    stream_element = doc.getElementsByTagName("stream")[0]

    attr = stream_element.attributes
    info = {}

    attrs = {"nb_frames": "length", "width": "width", "height": "height",
    "avg_frame_rate": "fps"}

    # Collect the attributes from the `stream` node
    for i in range(0, attr.length):
        a = attr.item(i)
        try:
            # Convert from unicode if possible
            name = str(a.localName)
            value = str(a.value)
            if name not in attrs:
                continue
            # If it has a / convert to float
            if "/" in value:
                a, b = value.split("/")
                value = float(a) / float(b)
            # Check if it contains only numbers (integer)
            elif all(map(lambda c: c in "1234567890", value)):
                value = int(value)
            info[attrs[name]] = value
        except:
            # Ignore attribute
            pass
    return info

def get_info_opencv(path):
    cap = cv2.VideoCapture()
    if cap.open(path):
        def get_prop(p):
            return cap.get(p)
        fps    = float(get_prop(cv2.CAP_PROP_FPS))
        length = int(get_prop(cv2.CAP_PROP_FRAME_COUNT))
        height = int(get_prop(cv2.CAP_PROP_FRAME_HEIGHT))
        width  = int(get_prop(cv2.CAP_PROP_FRAME_WIDTH))

        if not all([fps, length, height, width]):
            raise cv2.error()
        else:
            return {"width": width, "height": height, "length": length, "fps": fps}
    else:
        raise cv2.error()

def get_info_default(path):
    return  {"width": 800, "height": 600, "length": 100, "fps": 30.0}


class ICFileInput(object):
    # Max number of recent files to save
    MAX_RECENT_FILES = 5

    def __init__(self, plugin_path):
        self.log = logging.getLogger("plugin.ICFileInput")
        self.plugin_path = plugin_path

        # Media state
        self.is_open = False
        self.path    = ''
        self.capture = VideoCapture()

        # Information about the video source when opened
        self.fps    = 0
        self.length = 0
        self.size   = (0, 0)
        self.pos    = 0

        # The recent opened files and the last dir
        self.history = []
        self.lastdir = ""

        # Load the recent files from the xml
        self.load_history()


    def load_history(self):
        """Load the list of recent files from the xml `recent.xml`

        """
        doc = minidom.parse(os.path.join(self.plugin_path, "recent.xml"))

        # Get a list with all the file tag values
        recent_files = [c.nodeValue for f in doc.getElementsByTagName("file") for c in f.childNodes]

        # Get the value of the lastdir, if not found means it empty
        try:
            lastdir = doc.getElementsByTagName("lastdir")[0].childNodes[0].nodeValue
        except IndexError:
            lastdir = u""

        self.history = recent_files
        self.lastdir = lastdir


    def save_history(self):
        """Save the list of recent files to the xml `recent.xml`

        """
        # Create the document and a root element
        doc = Document()
        root = doc.createElement("recent")
        doc.appendChild(root)

        for f in self.history:
            file_element = doc.createElement("file")
            file_text    = doc.createTextNode(f)
            file_element.appendChild(file_text)
            root.appendChild(file_element)

        lastdir_element = doc.createElement("lastdir")
        lastdir_text = doc.createTextNode(self.lastdir)

        lastdir_element.appendChild(lastdir_text)
        root.appendChild(lastdir_element)

        with open(os.path.join(self.plugin_path, "recent.xml"), "w") as f:
            f.write(doc.toprettyxml())

    def update_history(self, file_path):
        """Inserts a file in the history.

        """
        if file_path not in self.history:
            if len(self.history) >= self.MAX_RECENT_FILES:
                self.history = self.history[1:self.MAX_RECENT_FILES]
            self.history.append(file_path)
            self.update_recent_files()
            self.save_history()
        pass

    def update_recent_files(self):
        """Update the gui to show the all the recent files.

        """
        layout = self.tools.gbox_recent.layout()
        count = layout.count()

        # Remove all the widgets from the layout
        while layout.count() > 0:
            w = layout.takeAt(0).widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        # Mouse press event funtion factory
        def mousePressEvent(pb, txt):
            def decored(event):
                self.tools.le_path.setText(txt)
                event.accept()
            return decored

        # Create a button for each file and add to the layout
        for recent in self.history:
            pb = QPushButton(os.path.split(recent)[1])
            pb.setToolTip(recent)
            pb.mousePressEvent = mousePressEvent(pb, recent)
            layout.addWidget(pb)

        # Add a vertical spacer
        layout.addStretch(0)

    def search_file(self):
        """Open the dialog for searching a file at the last directory searched.

        """
        title = tr("ICFileInput", "Select a video file")
        caption =  tr("ICFileInput", "Select a video file")

        selected_file = QFileDialog.getOpenFileName(
            None,
            caption,
            self.lastdir
            )

        if not selected_file.isEmpty():
            self.lastdir = os.path.split(str(selected_file))[0]
            self.tools.le_path.setText(selected_file)

    def load_file(self):
        """Load a video file and open the video source.

        """
        if self.tools.le_path.text().isEmpty():
            title = tr("ICFileInput", "Empty file path")
            caption = tr("ICFileInput", "The file path box is empty!")
            QMessageBox.warning(None, title, caption)
            return

        # Close the current, if there is one
        if self.is_open:
            self.close_file()

        file_path = str(self.tools.le_path.text())

        if self.capture.open(file_path):
            try:
                if info_source == INFO_FROM_FFPROBE:
                    info = get_info_ffprobe(file_path)
                elif info_source == INFO_FROM_OPENCV:
                    info = get_info_opencv(file_path)
            except:
                title = tr("ICFileInput", "Media info could not be obtained")
                caption = tr("ICFileInput", "An error ocurried when trying to get media info using %1. You can use default values or manually input them. Would you like to continue?")
                mode = {INFO_FROM_OPENCV: "OpenCV", INFO_FROM_FFPROBE: "ffprobe"}
                caption = caption.arg(mode[info_source])

                ret = QMessageBox.question(None, title, caption, QMessageBox.Yes | QMessageBox.No)
                if ret == QMessageBox.Yes:
                    info = get_info_default(file_path)

                    for v in info:
                        while True:
                            title = tr("ICFileInput", "Media info values")
                            caption = tr("ICFileInput", "Insert value for '%1'")
                            value, ret = QInputDialog.getText(None, title, caption.arg(str(v)), text = str(info[v]))
                            try:
                                if not ret:
                                    return
                                value = float(str(value))
                                info[v] = value
                                break
                            except:
                                t = tr("ICFileInput", "Invalid value")
                                c = tr("ICFileInput", "The value must be of a numeric type")
                                QMessageBox.warning(None, t, c)
                else:
                    self.capture.release()
                    return

            fps    = float(info["fps"])
            size   = (int(info["width"]), int(info["height"]))
            length = int(info["length"])

            self.fps = fps
            self.size = size
            self.length = length

            self.path = file_path

            # Open the video source
            self.video_source_bridge.open(fps=fps, size=size, length=length)

            self.is_open = True

            self.update_history(file_path)

            self.tools.le_path.setText("")
        else:
            title = tr("ICFileInput",
                "Error when loading file"
                )

            caption = tr("ICFileInput",
                "The OpenCV capture object could not open the file."
                )

            QMessageBox.warning(None, title, caption)

    def init_plugin(self, gui_interface, video_source_bridge):
        self.video_source_bridge = video_source_bridge

        # Load the tools ui tab
        self.tools = gui_interface.load_ui("tools_tab", "tools.ui")
        # Add to the main window tools tab
        gui_interface.add_tool_tab("tools_tab", "File Input")

        self.tools.pb_search.clicked.connect(self.search_file)
        self.tools.pb_load_file.clicked.connect(self.load_file)
        self.tools.pb_clear.clicked.connect(self.clear_history)

        self.update_recent_files()
        return True

    def clear_history(self):
        self.history = []
        self.lastdir = ""
        self.save_history()
        self.update_recent_files()

    def close_file(self):
        if self.is_open:
            self.is_open = False
            self.capture.release()
            self.fps = 0
            self.size = (0, 0)
            self.length = 0
            self.path = 0
            self.pos = 0
            self.video_source_bridge.close()

    def close_plugin(self):
        self.close_file()

    def seek(self, pos):
        try:
            if pos >= 0 and pos < self.length:
                if pos == self.pos or self.capture.set(cv2.CAP_PROP_POS_FRAMES, pos):
                    self.pos = pos
                    return True
                else:
                    return False
            else:
                return None
        except:
            return False

    def tell(self):
        if self.pos >= self.length:
            raise EOFError()
        return self.pos

    def get_length(self):
        return self.length

    def get_fps(self):
        return self.fps

    def get_size(self):
        return self.size

    def next(self):
        if not self.is_open:
            return None

        if self.pos >= self.length:
            raise EOFError()

        ret, frame = self.capture.read()
        if ret:
            self.pos += 1
            return frame

        else:
            return None

    def close_source(self):
        self.close_file()

def main(plugin_path):
    return ICFileInput(plugin_path)
