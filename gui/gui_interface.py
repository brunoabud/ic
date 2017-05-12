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

from PyQt4.QtGui import QScrollArea, QDial, QSlider, QScrollBar, QBoxLayout
from PyQt4.QtGui import QWidget, QLabel
from PyQt4.QtCore import Qt

from application import get_app
from gui import tr

LOG = logging.getLogger(__name__)

SLDR_TYPE_HSlider    = 0x1
SLDR_TYPE_VSlider    = 0x2
SLDR_TYPE_Dial       = 0x3
SLDR_TYPE_HScrollbar = 0x4
SLDR_TYPE_VScrollbar = 0x5

def create_slider(slider_type, slider_range,  slider_default):
    """Create a QSlider of the given type, with the given range and value.
    """
    # Horizontal Slider
    if slider_type == SLDR_TYPE_HSlider:
        slider = QSlider(Qt.Horizontal)
    # Vertical Slider
    elif slider_type == SLDR_TYPE_VSlider:
        slider = QSlider(Qt.Vertical)
    # Dial
    elif slider_type == SLDR_TYPE_Dial:
        slider = QDial()
    # Horizontal Scrollbar
    elif slider_type == SLDR_TYPE_HScrollbar:
        slider = QScrollBar(Qt.Horizontal)
    # Vertical Scrollbar
    elif slider_type == SLDR_TYPE_VScrollbar:
        slider = QScrollbar(Qt.Vertical)
    else:
        raise TypeError("Invalid slider type")

    slider.setRange(slider_range[0], slider_range[1])
    slider.setValue(slider_default)

    return slider

class IntParam(object):
    """Class that represents an integer that can be changed by the user.

    This class will create a widget that can interact to the user in order to
    retrieve a int value. The widget is fully managed by the class and it expo
    ses it value through the `value` member.

    """
    def __init__(self, show_title, value_range,  default_value, slider_type, adjust_function):
        # The parent widget
        widget = QWidget()
        slider = create_slider(slider_type, value_range, default_value)
        title  = QLabel(str(show_title))
        value  = QLabel(str(default_value))
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        title.setWordWrap(True)
        value.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        widget.setLayout(QBoxLayout(QBoxLayout.TopToBottom))
        widget.layout().addWidget(title , 1)
        widget.layout().addWidget(slider, 2)
        widget.layout().addWidget(value , 1)
        widget.layout().setSpacing(0)

        def clip(v):
            v = max(v, value_range[0])
            v = min(v, value_range[1])
            return v

        # No adjust_function is given, uses only the clip
        if adjust_function is None:
            adjust_func = clip
        # If adjust_func is given, use it and the clip
        else:
            def adjust_func(v):
                v = adjust_function(v)
                v = clip(v)
                return v
        # This function will receive the sliderMoved signal from the slider.
        # It should pass it to the adjust_func and show the returned value to
        # the user through the `value` label, so the value that user sees is
        # always correct. It also changes the _value member to the value return'
        def slider_moved(v):
            self._value = int(adjust_func(v))
            value.setText(str(self._value))

        slider.sliderMoved.connect(slider_moved)

        self._widget  = widget
        self._slider  = slider
        self._title   = title
        self._range   = value_range
        self._default = int(default_value)
        self._value   = int(default_value)
        self._adjust  = adjust_func
        self._native_title = show_title

    def get_default(self):
        return self._default

    def set_default(self, value):
        self._default = value

    def get_title(self):
        return str(self._title.text())

    def set_title(self, title):
        self._title.setText(str(title))

    def get_value(self):
        return self._value

    def set_value(self, value):
        v = self._adjust(value)
        self._value = v
        self._slider.setValue(v)

    def get_range(self):
        return self._range

    def set_range(self, value_range):
        self._range = value_range
        self._slider.setRange(value_range[0], value_range[1])

    def to_default(self):
        self._value = self._default
        self._slider.setValue(self._default)
        return self._value

    value              = property(get_value, set_value)
    value_range        = property(get_range, set_range)
    title              = property(get_title, set_title)
    default            = property(get_default, set_default)

class GUI_Interface(object):
    """Provide utlity and methods to manipulate the main application GUI.

    """
    def __init__(self, plugin_id):
        # The widget that will hold all the parameters created with the
        # *_parameter methods.
        widget_parameters       = QScrollArea()
        self._widget_parameters = widget_parameters
        # Qt stuff to make the scroll area resizable, and initialize it.
        widget_parameters.setWidgetResizable(True)
        widget_parameters.setWidget(QWidget())
        widget_parameters.widget().setLayout(QBoxLayout(QBoxLayout.TopToBottom))
        widget_parameters.widget().layout().setSpacing(2)
        # These sets hold the name of the ui files that are inserted in the
        # tools tab or in the main tab
        self.maintab_names = set()
        self.tooltab_names = set()
        # List that holds the created parameters to make easy to translate it
        self.parameters = []

        self._plugin_id = plugin_id

    def show_parameters(self):
        """Make sure that the widget_parameters is visible.

        """
        mainwindow = get_app().get_ui("main_window")
        # If the widget_parameters is not in the tools tab, add it
        i = mainwindow.toolstab.indexOf(self._widget_parameters)
        if i == -1:
            mainwindow.toolstab.addTab(self._widget_parameters, "Parameters")

    def int_parameter(self, default_value, value_range, title, slider_type = SLDR_TYPE_HSlider, adjust_func = None):
        """Create an return IntParameter object and add to the GUI.
        Args:
          title (str): title that will be showed to the user
          value_range (int, int): a tuple containing (min, max) values
          default_value (int): the default value of the parameter
          adjust_func (function): if provided, the adjust_func will be called to adjust
            the value choosen by the user. this may be necessary
            for parameters that need to have some specific values.
            the adjust_func will be called with the users value as
            its argument and it should return the adjusted value.
          slider_type (int): the type of the widget that will be used. should be
            an item from the GUIInterface.SliderType Enum
        """

        param = IntParam(title, value_range, default_value, slider_type, adjust_func)

        self._widget_parameters.widget().layout().addWidget(param._widget)
        self._widget_parameters.widget().layout().addStretch(
        self._widget_parameters.widget().layout().count())

        self.show_parameters()
        self.parameters.append(param)
        return param

    def add_tool_tab(self, name, title):
        app = get_app()
        pid = self._plugin_id
        mainwindow = app.get_ui("main_window")

        if name not in self.tooltab_names:
            ui = app.get_plugin_ui(pid, name)
            mainwindow.toolstab.addTab(ui, title)
            self.tooltab_names.add(name)

    def add_main_tab(self, name, title):
        app = get_app()
        pid = self._plugin_id
        mainwindow = app.get_ui("main_window")

        if name not in self.maintab_names:
            ui = app.get_plugin_ui(pid, name)
            mainwindow.maintab.addTab(ui, title)
            self.maintab_names.add(name)

    def remove_tool_tab(self, name):
        app = get_app()
        pid = self._plugin_id
        mainwindow = app.get_ui("main_window")

        ui = app.get_plugin_ui(pid, name)

        self.tooltab_names.discard(name)
        mainwindow.toolstab.removeTab(mainwindow.toolstab.indexOf(ui))


    def remove_main_tab(self, name):
        app = get_app()
        pid = self._plugin_id
        mainwindow = app.get_ui("main_window")

        ui = app.get_plugin_ui(pid, name)

        self.maintab_names.discard(name)
        mainwindow.maintab.removeTab(mainwindow.maintab.indexOf(ui))

    def show_status(self, text, timeout = 0):
        pass

    def release(self):
        self._widget_parameters.setParent(None)
        self._widget_parameters.deleteLater()

        while self.maintab_names:
            self.remove_main_tab(self.maintab_names.pop())
        while self.maintab_names:
            self.remove_tool_tab(self.maintab_names.pop())

    def load_ui(self, name, ui_file, base_instance = None):
        return get_app().load_plugin_ui(self._plugin_id, name, ui_file, base_instance)

    def retranslateUi(self):
        for param in self.parameters:
            try:
                param._title.setText(tr("GUI_Interface", param._native_title))
            except:
                LOG.error("", exc_info=True)
