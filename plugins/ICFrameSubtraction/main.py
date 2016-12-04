#coding: utf-8
import logging
log = logging.getLogger("ICFrameSubtraction")
from Queue import Queue
import cv2
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from PyQt4.QtGui  import (QGraphicsScene, QBrush, QColor, QGraphicsView,
                             QGraphicsLayout, QGraphicsPixmapItem, QPixmap,
                             QPainter, QFont, QWidget, QGridLayout)
from PyQt4.QtCore import (QState, QStateMachine, QPropertyAnimation,
                             QEasingCurve, QRectF, Qt, )

def impar(value):
    return value | 0x01

class Analyzer(object):
    def __init__(self):
        self.filter_rack = None
        self.buffer    = Queue()
        self.min_frameskip = 0
        # Adaptive Frame Skipping
        self.max_frameskip = 4
        log.debug("Initializing analyzer\nFrameskip   : 1\nBuffer Limit: None")
        # Holds a numpy's ndarray object at the size of the current video source
        # one for the x values found, one for the y values and one for the time
        # length. If a frame that will be processed has a position greather than
        # the current size of this array, it will be expanded in units of
        # ARRAY_RESIZE_LENGTH until it can hold the new frame.
        self.time = np.zeros((1))
        self.data_x    = np.zeros((1))
        self.data_y    = np.zeros((1))

        # The lines object for each one of the plots
        self.line_x   = None        # X Line plot
        self.line_y   = None        # Y Line Plot

        # The axes objects for each one of the graphics
        self.axes_x  = None        # X POS Plot
        self.axes_y  = None        # Y POS Plot

        self.writer_y = open("/home/bruno/Desktop/pontos_y.csv", "wb")
        self.writer_x = open("/home/bruno/Desktop/pontos_x.csv", "wb")
        self.writer_y.write("Seconds,Centimeters\n")
        self.writer_x.write("Seconds,Centimeters\n")
    def analyze_pos(self, first, second, params):
        """Analyze the frame buffer with a given frameskip.

        Returns
        -------
        (x, y, frame, frame_state) or (None, None, None, None)
        x           : int containing the detected x pos
        y           : int containing the detected y pos
        """
        gray1        = self.filter_rack["Pre-Filter"].apply_filters(first)
        gray2        = self.filter_rack["Pre-Filter"].apply_filters(second)

        diff         = gray1.copy()
        diff.data    = cv2.absdiff(gray2.data, gray1.data)
    	diff         = self.filter_rack["Post-Filter"].apply_filters(diff)

    	binary       = self.filter_rack["Threshold"].apply_filters(diff)

    	binary       = self.filter_rack["Dilatation"].apply_filters(binary)


    	_, contorno, h  = cv2.findContours(binary.data, cv2.RETR_EXTERNAL,
    					  cv2.CHAIN_APPROX_SIMPLE)

        if contorno:
            try:
                M = cv2.moments(contorno[0])
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
                return (int(x), int(y))
            except:
                return (None, None)
        else:
            return (None, None)

    def process_frame(self, frame, params):
        # Add the frame to the buffer queue
        self.buffer.put(frame)
        # Always keep `self.max_frameskip + 1` frames in the buffer
        # Do nothing if it has fewer frames in the buffer than the needed
        if self.buffer.qsize() < self.max_frameskip + 2:
            return (frame)
        # Discard first frames it has more than needed
        if self.buffer.qsize() > self.max_frameskip + 2:
          while self.buffer.qsize() > self.max_frameskip + 2:
              self.buffer.get()
        # "Adaptive FrameSkip"
        for frameskip in range(params["skip"], self.max_frameskip + 1):
            x, y = self.analyze_pos(self.buffer.queue[0].copy(),
             self.buffer.queue[frameskip + 1].copy(), params)
            processed_frame = self.buffer.queue[0]
            for i in xrange(0, self.time.shape[0]):
                if self.data_x[i] is not np.nan and self.data_y[i] is not np.nan:
                    try:
                        processed_frame.data = cv2.circle(processed_frame.data, (int(self.data_x[i]), int(self.data_y[i])), 2, (0, 0, 255, 20), 1)
                    except:
                        pass
            if all((x, y)):
                self.buffer.queue.popleft()
                processed_frame.data = cv2.circle(processed_frame.data, (x, y), 8, (255, 0, 0), 2)
                processed_frame.data = cv2.line(processed_frame.data, (x-15, y), (x+15, y), (255, 0, 0), 2)
                processed_frame.data = cv2.line(processed_frame.data, (x, y-15), (x, y+15), (255, 0, 0), 2)
                self.data_x[frame.pos] = int(x)
                self.data_y[frame.pos] = int(y)
                self.time[frame.pos]   = frame.pos
                try:
                    try:
                        if frame.pos < self.last_pos:
                            self.writer_y.close()
                            self.writer_x.close()
                        else:
                            self.writer_y.write("%f,%f\n" % (frame.pos*(1.0/frame.fps), int(y) ))
                            self.writer_x.write("%f,%f\n" % (frame.pos*(1.0/frame.fps), int(x) ))
                            self.last_pos = frame.pos
                    except:
                        self.last_pos = frame.pos
                except:
                    pass
                self.line_x.set_data(self.time, self.data_x)
                self.line_y.set_data(self.time, self.data_y)
                return processed_frame
        # If nothing was found, return the given frame
        for i in xrange(0, self.time.shape[0]):
            if self.data_x[i] is not np.nan and self.data_y[i] is not np.nan:
                try:
                    frame.data = cv2.circle(frame.data, (int(self.data_x[i]), int(self.data_y[i])), 2, (0, 0, 255, 20), 1)
                except:
                    pass
        return frame

class PlotCanvas(FigureCanvas):
    def __init__(self):
        figure = Figure(figsize=(5, 4), dpi=100)
        FigureCanvas.__init__(self, figure)


class ICFrameSubtraction(object):
    ARRAY_RESIZE_LENGTH = 20
    def __init__(self):
        self.analyzer = Analyzer()
        self.last_plot_update = 0

    def init_plugin(self, gui_interface, rack_interface):
        self.analyzer.filter_rack = rack_interface
        gui            = gui_interface
        self.rack_interface = rack_interface

        self.skip      = gui.int_parameter(1 , (0,  self.analyzer.max_frameskip), "Quantidade mínima de frames a serem pulados")
        self.params = {"skip": self.skip}

        self.mplcanvas = FigureCanvas(Figure(figsize=(6, 5), dpi=100))
        self.gui       = gui

        tab_plots      = gui_interface.load_ui("tab_plots", "tab_plots.ui")
        plots_widget   = QWidget()
        xplot          = PlotCanvas()
        yplot          = PlotCanvas()

        self.analyzer.axes_x    = xplot.figure.add_subplot(111)
        self.analyzer.axes_y    = yplot.figure.add_subplot(111)

        self.analyzer.line_x    = self.analyzer.axes_x.plot(self.analyzer.time, self.analyzer.data_x)[0]
        self.analyzer.line_y    = self.analyzer.axes_y.plot(self.analyzer.time, self.analyzer.data_y)[0]

        self.analyzer.line_x.set_linestyle("None")
        self.analyzer.line_y.set_linestyle("None")
        self.analyzer.line_x.set_marker(".")
        self.analyzer.line_y.set_marker(".")

        tab_plots.layout().addWidget(plots_widget, 0, 0, 1, 1)

        # Add the widgets containing the plots
        plots_widget.setLayout(QGridLayout())
        plots_widget.layout().addWidget(xplot, 0, 0, 1, 1)
        plots_widget.layout().addWidget(yplot, 1, 0, 1, 1)

        gui_interface.add_main_tab("tab_plots", "Plots")

        self.tab_plots     = tab_plots
        self.plots_widget  = plots_widget
        self.xplot = xplot
        self.yplot = yplot
        return True

    def process_frame(self, frame):
        if frame.pos >= self.analyzer.time.shape[0]:
            p20 = self.analyzer.time.shape[0] + int(self.analyzer.time.shape[0] * 0.20)
            log.debug("Resizing array from {} to {}".format(self.analyzer.time.shape[0], p20))
            self.analyzer.time.resize((p20), refcheck=False)
            self.analyzer.data_x.resize((p20), refcheck=False)
            self.analyzer.data_y.resize((p20), refcheck=False)

        new_frame = self.analyzer.process_frame(frame, {param:getattr(self, param).value for param in self.params})
        if new_frame.pos - self.last_plot_update > 10:
            self.xplot.draw()
            self.yplot.draw()
            self.last_plot_update = new_frame.pos

        self.video_out.write(new_frame.data)

        return new_frame

    def on_media_sought(self, state):
        self.analyzer.buffer.queue.clear()

    def on_media_opened(self, state):
        length = state["length"]
        self.analyzer.data_x = np.full((length), np.nan)
        self.analyzer.data_y = np.full((length), np.nan)
        self.analyzer.time   = np.full((length), np.nan)

        self.analyzer.axes_x.set_ylim(0, state["size"][0])
        self.analyzer.axes_y.set_ylim(0, state["size"][1])

        self.analyzer.axes_x.set_xlim(0, state["length"])
        self.analyzer.axes_y.set_xlim(0, state["length"])

        self.fourcc = cv2.VideoWriter_fourcc(*"WMV2")
        self.video_out = cv2.VideoWriter("/home/bruno/Desktop/analise.wmv", self.fourcc, state["fps"], state["size"])


    def on_media_closed():
        log.debug("on_media_closed")
        self.video_out.release()

def main(plugin_path):
    return ICFrameSubtraction()
