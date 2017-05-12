# coding: latin-1
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
from Queue import Queue

import cv2
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from PyQt4.QtGui  import (QGraphicsScene, QBrush, QColor, QGraphicsView,
                             QGraphicsLayout, QGraphicsPixmapItem, QPixmap,
                             QPainter, QFont, QWidget, QGridLayout, QLabel,
                             QSizePolicy)
from PyQt4.QtCore import (QState, QStateMachine, QPropertyAnimation,
                             QEasingCurve, QRectF, Qt )


import ICFrameSubtraction.teste


LOG = logging.getLogger("ICFrameSubtraction")


class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self):
        figure = Figure(figsize=(5, 4), dpi=100)
        FigureCanvasQTAgg.__init__(self, figure)
        self.setSizePolicy(QSizePolicy.Expanding,
            QSizePolicy.Expanding)

        self._separated = True

        self.h_plot = None
        self.v_plot = None

        self.h_data = None
        self.v_data = None

    def set_separated(self, separated):
        self._separated = separated


class TabPlots(object):
    def __init__(self, ui):
        self.ui     = ui
        self.canvas = PlotCanvas()

        self.replace_charts_placeholder()

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
    def __init__(self):
        pass

    def init_plugin(self, gui_interface, rack_interface):
        gui            = gui_interface
        tab_plots      = TabPlots(gui_interface.load_ui("tab_plots", "tab_plots.ui"))
        gui_interface.add_main_tab("tab_plots", "Plots")

        self.tab_plots = tab_plots
        return True

    def process_frame(self, frame):
        return frame

    def on_media_sought(self, state):
        pass

    def on_media_opened(self, state):
        pass

    def on_media_closed():
        pass

def main(plugin_path):
    return ICFrameSubtraction()
