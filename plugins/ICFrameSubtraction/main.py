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

    def analyze_pos(self, frame, frame_state, frameskip, params):
        """Analyze the frame buffer with a given frameskip.

        Returns
        -------
        (x, y, frame, frame_state) or (None, None, None, None)
        x           : int containing the detected x pos
        y           : int containing the detected y pos
        frame       : the input frame
        frame_state : the real frame_state (of the first frame in the buffer)
        """
        last, last_state = self.buffer.queue[0]
        last_raw = last
        last = cv2.cvtColor(last, cv2.COLOR_BGR2GRAY)
        last = cv2.blur(last, (params["blur01"],)*2)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.blur(gray, (params["blur01"],)*2)

    	diff             = cv2.absdiff(gray, last)
    	diff             = cv2.blur(diff, (params["blur02"],)*2)

    	binary           = cv2.adaptiveThreshold(diff, 255,
    		              cv2.ADAPTIVE_THRESH_MEAN_C,
                          cv2.THRESH_BINARY_INV, params["thresh"],
                         params["thresh_c"])

    	kernel           = np.ones((params["skernel"],)*2, np.uint8)
    	binary           = cv2.dilate(binary, kernel, iterations=params["dkernel"])

    	_, contorno, h  = cv2.findContours(binary, cv2.RETR_EXTERNAL,
    					  cv2.CHAIN_APPROX_SIMPLE)

        if contorno:
            try:
                M = cv2.moments(contorno[0])
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
                return (int(x), int(y), last_raw, last_state)
            except:
                return (None, None, None, None)
        else:
            return (None, None, None, None)

    def process_frame(self, frame, frame_state, params):
        # Add the frame to the buffer queue
        self.buffer.put((frame, frame_state))
        # Always keep `self.max_frameskip + 1` frames in the buffer
        # Do nothing if it has fewer frames in the buffer than the needed
        if self.buffer.qsize() < self.max_frameskip + 2:
            return (frame_state, frame)
        # Discard first frames it has more than needed
        if self.buffer.qsize() > self.max_frameskip + 2:
          while self.buffer.qsize() > self.max_frameskip + 2:
              self.buffer.get()
        # "Adaptive FrameSkip"
        for frameskip in range(params["skip"], self.max_frameskip + 1):
            last_frame, last_frame_state = self.buffer.queue[frameskip + 1]
            x, y, new_frame, new_frame_state = self.analyze_pos(last_frame, last_frame_state, frameskip, params)
            for i in xrange(0, self.time.shape[0]):
                if self.data_x[i] is not np.nan and self.data_y[i] is not np.nan:
                    try:
                        new_frame = cv2.circle(new_frame, (int(self.data_x[i]), int(self.data_y[i])), 2, (0, 0, 255, 20), 1)
                    except:
                        pass
            if all((x, y)):
                self.buffer.queue.popleft()
                new_frame = cv2.circle(new_frame, (x, y), 8, (255, 0, 0), 2)
                new_frame = cv2.line(new_frame, (x-15, y), (x+15, y), (255, 0, 0), 2)
                new_frame = cv2.line(new_frame, (x, y-15), (x, y+15), (255, 0, 0), 2)
                self.data_x[frame_state["pos"]] = int(x)
                self.data_y[frame_state["pos"]] = int(y)
                self.time[frame_state["pos"]]   = frame_state["pos"]
                self.line_x.set_data(self.time, self.data_x)
                self.line_y.set_data(self.time, self.data_y)
                return new_frame_state, new_frame
        # If nothing was found, return the given frame and state
        for i in xrange(0, self.time.shape[0]):
            if self.data_x[i] is not np.nan and self.data_y[i] is not np.nan:
                try:
                    frame = cv2.circle(frame, (int(self.data_x[i]), int(self.data_y[i])), 2, (0, 0, 255, 20), 1)
                except:
                    pass
        return frame_state, frame

class PlotCanvas(FigureCanvas):
    def __init__(self):
        figure = Figure(figsize=(5, 4), dpi=100)
        FigureCanvas.__init__(self, figure)


class ICFrameSubtraction(object):
    ARRAY_RESIZE_LENGTH = 20
    def __init__(self):
        self.analyzer = Analyzer()
        self.last_plot_update = 0

    def init_plugin(self, gui_interface):
        gui            = gui_interface
        self.thresh    = gui.int_parameter(13, (3, 99), "Valor do threshold", adjust_func = impar)
        self.thresh_c  = gui.int_parameter(8 , (0, 99), "Constante de treshold")
        self.blur01    = gui.int_parameter(3 , (3, 99), "Primeiro blur", adjust_func = impar)
        self.blur02    = gui.int_parameter(3 , (3, 99), "Segundo blur", adjust_func = impar)
        self.dkernel   = gui.int_parameter(5 , (3, 99), "Tamanho do kernel de dilatacao", adjust_func = impar)
        self.skernel   = gui.int_parameter(4 , (3, 99), "Quantidade de passos da dilatacao")
        self.skip      = gui.int_parameter(1 , (0,  self.analyzer.max_frameskip), "Quantidade mínima de frames a serem pulados")
        self.mplcanvas = FigureCanvas(Figure(figsize=(6, 5), dpi=100))
        self.gui       = gui
        self.params    = ["thresh", "thresh_c", "blur01", "blur02", "dkernel",
            "skernel", "skip"]
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

    def process_frame(self, frame, state):
        if state["pos"] >= self.analyzer.time.shape[0]:
            p20 = self.analyzer.time.shape[0] + int(self.analyzer.time.shape[0] * 0.20)
            log.debug("Resizing array from {} to {}".format(self.analyzer.time.shape[0], p20))
            self.analyzer.time.resize((p20), refcheck=False)
            self.analyzer.data_x.resize((p20), refcheck=False)
            self.analyzer.data_y.resize((p20), refcheck=False)

        new_state, new_frame = self.analyzer.process_frame(frame, state, {param:getattr(self, param).value for param in self.params})
        if new_state["pos"] - self.last_plot_update > 10:
            self.xplot.draw()
            self.yplot.draw()
            self.last_plot_update = new_state["pos"]

        return new_state, new_frame

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

    def on_media_closed():
        log.debug("on_media_closed")

def main(plugin_path):
    return ICFrameSubtraction()
