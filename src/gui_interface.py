from PyQt4.QtGui import QScrollArea, QDial, QSlider, QScrollBar, QBoxLayout
from PyQt4.QtGui import QWidget, QLabel
from PyQt4.QtCore import Qt
from enum import Enum

import log


class SliderType(Enum):
    HSlider = 1
    VSlider = 2
    Dial = 3
    HScrollbar = 4
    VScrollbar = 5


def create_slider(slider_type, r,  d):
    slider = None
    if slider_type is SliderType.HSlider:
        slider = QSlider(Qt.Horizontal)
    elif slider_type is SliderType.VSlider:
        slider = QSlider(Qt.Vertical)
    elif slider_type is SliderType.Dial:
        slider = QDial()
    elif slider_type is SliderType.HScrollbar:
        slider = QScrollBar(Qt.Horizontal)
    elif slider_type is SliderType.VScrollbar:
        slider = QScrollbar(Qt.Vertical)
    else:
        raise TypeError("Invalid slider type")
    slider.setRange(r[0], r[1]); slider.setValue(d)
    return slider

class IntParam(object):
    def getdefault(self):
        return self._default

    def setdefault(self, value):
        self._default = value

    def gettitle(self):
        return str(self._title.text())

    def settitle(self, title):
        self._title.setText(str(title))

    def getvalue(self):
        return self._value

    def getrange(self):
        return self._range

    def setrange(self, value_range):
        self._range = value_range
        self._slider.setRange(value_range[0], value_range[1])

    def default(self):
        self._value = self._default
        self._slider.setValue(self._default)
        return self._value

    value              = property(getvalue, None)
    value_range        = property(getrange, setrange)
    title              = property(gettitle, settitle)
    default            = property(getdefault, setdefault)


    def __init__(self, show_title, value_range,  default_value, slider_type, adjust_func):
        widget = QWidget();
        slider = create_slider(slider_type, value_range, default_value)
        title  = QLabel(str(show_title));
        value  = QLabel(str(default_value))

        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        title.setWordWrap(True)

        value.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        widget.setLayout(QBoxLayout(QBoxLayout.TopToBottom))

        widget.layout().addWidget(title , 1)
        widget.layout().addWidget(slider, 2)
        widget.layout().addWidget(value , 1)
        widget.layout().setSpacing(0)

        adjust_func = (lambda x: x) if adjust_func is None else (adjust_func)

        def slidermoved(v):
            self._value = int(adjust_func(v))
            value.setText(str(self._value))

        slider.sliderMoved.connect(slidermoved)

        self._widget, self._slider , self._title = widget, slider, title
        self._range , self._default, self._value = value_range, int(default_value), int(default_value)

class ICGUI_Interface(object):
    """Provide utlity methods to manipulate the main application GUI."""
    def __init__(self, mainwindow):
        self._paramtab   = QScrollArea()
        self._mainwindow = mainwindow
        self._maintabs   = set()
        self._tooltabs   = set()

        self._paramtab.setWidgetResizable(True)
        self._paramtab.setWidget(QWidget())
        self._paramtab.widget().setLayout(QBoxLayout(QBoxLayout.TopToBottom))
        self._paramtab.widget().layout().setSpacing(2)


    def set_controls_visible(self, visible = False):
        i = self._mainwindow.toolstab.indexOf(self._paramtab)
        if visible and i == -1:
            self._mainwindow.toolstab.addTab(self._paramtab, "Controls")
        if not visible and i != -1:
            self._mainwindow.toolstab.removeTab(i)

    def int_parameter(self, default_value, value_range, title, slider_type = SliderType.HSlider, adjust_func = None):
        """Create an return IntParameter object and add to the GUI.

        title          : title that will be showed to the user
        value_range    : a tuple containing (min, max) values
        default_value  : the default value of the parameter
        adjust_func    : if provided, the adjust_func will be called to adjust
                       : the value choosen by the user. this may be necessary
                       : for parameters that need to have some specific values.
                       : the adjust_func will be called with the users value as
                       : its argument and it should return the adjusted value.
        slider_type    : the type of the widget that will be used. should be
                       : an item from the GUIInterface.SliderType Enum
        """

        param = IntParam(title, value_range, default_value, slider_type, adjust_func)

        self._paramtab.widget().layout().addWidget(param._widget)
        self._paramtab.widget().layout().addStretch(self._paramtab.widget().layout().count())
        self.set_controls_visible(True)
        return param

    def add_tool_tab(self, widget, title):
        self._tooltabs.add(widget)
        self._mainwindow.toolstab.addTab(widget, title)

    def add_main_tab(self, widget, title):
        self._maintabs.add(widget)
        self._mainwindow.maintab.addTab(widget, title)

    def remove_tool_tab(self, widget):
        self._tooltabs.discard(widget)
        self._mainwindow.toolstab.removeTab(self._mainwindow.toolstab.indexOf(widget))

    def remove_main_tab(self, widget):
        self._mainwindow.maintab.removeTab(self._mainwindow.maintab.indexOf(widget))
        self._maintabs.discard(widget)

    def get_tool_tabs(self):
        return self._tooltabs

    def get_main_tabs(self):
        return self._maintabs

    def show_status(self, text, timeout = 0):
        pass

    def release(self):
        self._paramtab.setParent(None)
        self._paramtab.deleteLater()

        while self._maintabs:
            self.remove_main_tab(self._maintabs.pop())
        while self._tooltabs:
            self.remove_tool_tab(self._tooltabs.pop())
