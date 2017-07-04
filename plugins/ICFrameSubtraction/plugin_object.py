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
import sys
import logging
from Queue import Queue
import os

import cv2
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from PyQt4.QtGui  import (QGraphicsScene, QBrush, QColor, QGraphicsView,
                             QGraphicsLayout, QGraphicsPixmapItem, QPixmap,
                             QPainter, QFont, QWidget, QGridLayout, QLabel,
                             QSizePolicy, QMessageBox, QStandardItemModel,
                             QStandardItem, QIcon, QColorDialog, QFileDialog)
from PyQt4.QtCore import (QState, QStateMachine, QPropertyAnimation,
                             QEasingCurve, QRectF, Qt, QString, pyqtSlot, QTimer )
from PyQt4 import uic

import resources_rc
from analysis import Analysis

LOG = logging.getLogger("ICFrameSubtraction")

MARKERS = {
            ("Pixel", ":/plot_icons/,", ","),
            ("Point", ":/plot_icons/point", "."),
            ("Star", ":/plot_icons/*", "*"),
            ("Circle", ":/plot_icons/o","o"),
            ("Triangle Down", ":/plot_icons/v", "v"),
            ("Triagle Up", ":/plot_icons/^", "^"),
            ("Triangle Left", ":/plot_icons/<", "<"),
            ("Triangle Right", ":/plot_icons/>", ">")

            }

class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self):
        figure = Figure(figsize=(5, 4), dpi=100)
        FigureCanvasQTAgg.__init__(self, figure)
        self.setSizePolicy(QSizePolicy.Expanding,
            QSizePolicy.Expanding)

        self.series = {"horizontal": {}, "vertical": {}}

        self.series["horizontal"] = {
                                     "color": "b",
                                     "marker": ".",
                                     "marker_size": 4,
                                     "linestyle": "",
                                     "xlim": [0, 10],
                                     "ylim": [0, 20],
                                     "x_data": np.empty((0)),
                                     "y_data": np.empty((0)),
                                     "timestamp": np.empty((0)),
                                     "title": "Horizontal Positions",
                                     "lines": None,
                                     "axes": None
                                     }
        self.series["vertical"] = {
                                     "color": "g",
                                     "marker": ".",
                                     "marker_size": 4,
                                     "linestyle": "",
                                     "xlim": [0, 10],
                                     "ylim": [0, 100],
                                     "x_data": np.empty((0)),
                                     "y_data": np.empty((0)),
                                     "timestamp": np.empty((0)),
                                     "title": "Vertical Positions",
                                     "lines": None,
                                     "axes": None
                                     }

        self._separated = True
        self.set_separated(False)

    def update_figure(self):
        self.figure.clear()
        fig = self.figure
        if not self._separated:
            joined_axes = self.figure.add_subplot(1, 1, 1)
            joined_axes.set_title(",".join([s["title"] for s in self.series.values()]))
            min_x = min([np.amin(i["xlim"][0]) for i in self.series.values()])
            max_x = max([np.amax(i["xlim"][1]) for i in self.series.values()])
            min_y = min([np.amin(i["ylim"][0]) for i in self.series.values()])
            max_y = max([np.amax(i["ylim"][1]) for i in self.series.values()])
            joined_axes.axis([min_x, max_x, min_y, max_y])

        nseries = len(self.series)
        for i, s in enumerate(self.series):
            series = self.series[s]
            if self._separated:
                series["axes"] = fig.add_subplot(nseries, 1, i+1)
            else:
                series["axes"] = joined_axes
            series["lines"] = series["axes"].plot(series["x_data"], series["y_data"])[0]

            lines = series["lines"]
            lines.set_marker(series["marker"])
            lines.set_linestyle(series["linestyle"])
            lines.set_color(series["color"])
            lines.set_markersize(series["marker_size"])
            if self._separated:
                series["axes"].set_title(series["title"])
                series["axes"].axis(series["xlim"]+series["ylim"])

    def set_separated(self, separated=True):
        if separated == self._separated:
            return
        self._separated = separated

        self.update_figure()
        self.draw()

    def series_update_data(self, series=None):
        l = [self.series[series]] if series is not None else self.series
        for i in l:
            s = self.series[i]
            s["lines"].set_data(s["x_data"], s["y_data"])
        self.draw()

    def series_set(self, series, key, value):
        s = self.series[series]
        if key == "marker":
            s["lines"].set_marker(value)
            s["marker"] = value
        elif key == "marker_size":
            s["lines"].set_markersize(value)
            s["marker_size"] = value
        elif key == "color":
            s["lines"].set_color(value)
            s["color"] = value

        self.draw()


class TabPlots(object):
    def __init__(self, ui):
        self.ui     = ui
        self.canvas = PlotCanvas()

        self.replace_charts_placeholder()

        self.ui.cb_separate_charts.toggled.connect(self._change_separated)
        self.ui.pb_clear.clicked.connect(self._clear_clicked)
        self.ui.cb_horizontal_marker.currentIndexChanged.connect(self._horizontal_marker_changed)
        self.ui.cb_vertical_marker.currentIndexChanged.connect(self._vertical_marker_changed)
        self.ui.spb_horizontal_marker.valueChanged.connect(self._h_marker_size_changed)
        self.ui.spb_vertical_marker.valueChanged.connect(self._v_marker_size_changed)
        self.ui.pb_export_tables.clicked.connect(self.export_tables)
        self.ui.pb_export_plot.clicked.connect(self.export_plot)

        model = QStandardItemModel()

        for m in MARKERS:
            text, icon, value = m
            item = QStandardItem(QIcon(icon), text)
            item.setData(value, 35)
            model.appendRow(item)

        self.ui.cb_horizontal_marker.setModel(model)
        self.ui.cb_vertical_marker.setModel(model)
        self.update_timer = QTimer()
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self._update_plot)
        self.update_timer.start()

    def export_plot(self, checked):
        path = QFileDialog.getSaveFileName(None, "Export Plot", "", "PNG (*.png)")
        if path != "":
            self.canvas.figure.savefig(str(path))

    def export_tables(self, checked):
        horizontal = ['"Horizontal Positions"']
        vertical = ['"Vertical Positions"']
        timestamp = ['"Timestamps"']
        pos = ['"Frame Positions"']

        for i in range(0, self.canvas.series["horizontal"]["x_data"].shape[0]):
            pos.append('"%d"' % self.canvas.series["horizontal"]["x_data"][i])
            timestamp.append('"%d"' % self.canvas.series["horizontal"]["timestamp"][i])
            horizontal.append('"%d"' % self.canvas.series["horizontal"]["y_data"][i])
            vertical.append('"%d"' % self.canvas.series["vertical"]["y_data"][i])

        path = QFileDialog.getSaveFileName(None, "Export plot table", "", "CSV (*.csv)")
        if path != "":
            with open(path, "w") as f:
                for i in range(0, len(horizontal)):
                    f.write(pos[i]+",")
                    f.write(timestamp[i]+",")
                    if self.ui.cb_table_export_horizontal.isChecked():
                        f.write(horizontal[i]+",")
                    if self.ui.cb_table_export_vertical.isChecked():
                        f.write(vertical[i]+",")
                    f.write("\n")

    def _update_plot(self):
        self.canvas.series_update_data()

    def _h_marker_size_changed(self, value):
        self.canvas.series_set("horizontal", "marker_size", float(value))

    def _v_marker_size_changed(self, value):
        self.canvas.series_set("vertical", "marker_size", float(value))

    def _horizontal_marker_changed(self, index):
        self.canvas.series_set("horizontal", "marker", str(self.ui.cb_horizontal_marker.itemData(index, 35).toPyObject()))

    def _vertical_marker_changed(self, index):
        self.canvas.series_set("vertical", "marker", str(self.ui.cb_vertical_marker.itemData(index, 35).toPyObject()))

    def _clear_clicked(self, checked):
        ret = QMessageBox.warning(None, "Clear Plot",
                ("Clearing the Plot will cause all the data to be lost."
                    " Clear anyway?"), QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            pass

    def _change_separated(self, checked):
        self.canvas.set_separated(checked)

    def replace_charts_placeholder(self):
        """Replace the charts placeholder label with the PlotCanvas widget.
        """
        layout = self.ui.frm_charts.layout()
        placeholder_index = layout.indexOf(self.ui.charts_placeholder)
        placeholder_item  = layout.itemAt(placeholder_index)
        r, c, rsp, csp = layout.getItemPosition(placeholder_index)

        layout.removeItem(placeholder_item)
        layout.addWidget(self.canvas, r, c, rsp, csp)
        placeholder_item.widget().deleteLater()

class ICFrameSubtraction(object):
    def __init__(self, plugin_path):
        self.path = plugin_path

    def init_plugin(self, gui_interface, filter_rack):
        gui            = gui_interface
        tab_plots      = TabPlots(uic.loadUi(os.path.join(self.path, "ui", "tab_plots.ui")))
        gui_interface.show_window(tab_plots.ui)
        self.analysis = Analysis(filter_rack)

        self.tab_plots = tab_plots
        return True

    def process_frame(self, frame):
        colorspace, data, pos, timestamp = frame
        self.analysis.buffer_frame(frame)
        ret = self.analysis.next_step()
        if ret[0] is None or ret[1] is None:
            return  (colorspace, ret[2])
        else:
            h, v = self.tab_plots.canvas.series["horizontal"], self.tab_plots.canvas.series["vertical"]
            h["x_data"][pos] = pos
            h["y_data"][pos] = ret[0]
            v["x_data"][pos] = pos
            v["y_data"][pos] = ret[1]
            h["timestamp"][pos] = timestamp / 1000.0
            v["timestamp"][pos] = timestamp / 1000.0
            cv2.circle(ret[2], (ret[0], ret[1]), 6, (255, 0, 0, 20), -1)

            if h["ylim"][1] < ret[2].shape[1]:
                h["ylim"][1] = ret[2].shape[1]
                self.tab_plots.canvas.update_figure()
            if v["ylim"][1] < ret[2].shape[0]:
                v["ylim"][1] = ret[2].shape[0]
                self.tab_plots.canvas.update_figure()


            return ("BGR", ret[2])

    def on_media_sought(self, *args, **kwargs):
        self.analysis.clear_buffer()

    def on_media_opened(self, *args, **kwargs):
        LOG.debug("%s", str(kwargs))
        length = kwargs["length"]
        constlen = kwargs["constlen"]
        h, v = self.tab_plots.canvas.series["horizontal"], self.tab_plots.canvas.series["vertical"]
        if constlen:
            h["x_data"] = np.zeros((length))
            h["y_data"] = np.zeros((length))
            v["x_data"] = np.zeros((length))
            v["y_data"] = np.zeros((length))
            v["timestamp"] = np.zeros((length))
            h["timestamp"]= np.zeros((length))
            h["xlim"] = [0, length]
            v["xlim"] = [0, length]
        else:
            if length is not None:
                h["x_data"] = np.zeros((length))
                h["y_data"] = np.zeros((length))
                v["x_data"] = np.zeros((length))
                v["y_data"] = np.zeros((length))
                h["timestamp"] = np.zeros((length))
                v["timestamp"] = np.zeros((length))
                h["xlim"] = [0, length]
                h["xlim"] = [0, length]
            else:
                h["x_data"] = np.zeros((100))
                h["y_data"] = np.zeros((100))
                v["x_data"] = np.zeros((100))
                v["y_data"] = np.zeros((100))
                h["timestamp"] = np.zeros((100))
                v["timestamp"] = np.zeros((100))
                h["xlim"] = [0, 100]
                v["xlim"] = [0, 100]
        self.tab_plots.canvas.update_figure()
        self.tab_plots.canvas.series_update_data()

    def on_media_closed(self):
        self.analysis.clear_buffer()

    def release_plugin(self, error_level=0):
        pass

def main(plugin_path):
    return ICFrameSubtraction()

if __name__ == "__main__":
    class Interface(object):
        def show_window(slf, widget):
            widget.show()

    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QTimer

    app = QApplication(sys.argv)

    sub = ICFrameSubtraction(sys.path[0])
    sub.init_plugin(Interface(), None)
    app.exec_()
