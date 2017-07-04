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

from PyQt4.QtGui import (QFrame, QBoxLayout, QApplication, QLabel, QPixmap,
                         QWidget)
from PyQt4.QtCore import Qt

import ic_resources_rc

LOG = logging.getLogger(__name__)

class FlowArrow(QLabel):
    ARROW_SIZE = 16
    def __init__(self):
        super(FlowArrow, self).__init__()
        self.setScaledContents(True)
        self.setPixmap(QPixmap(":icon/flow_arrow_down"))
        self.set_size(FlowArrow.ARROW_SIZE)

    def set_size(self, size):
        self.setMaximumSize(size, size)
        self.setMinimumSize(size, size)

class FlowWidget(QFrame):
    """A widget that contains a header, footer and children separated by arrows.

    This widgets acts like a list, but it only adds new widgets to the layout,
    vertically, and separated them by arrows.
    The items positions are virtual and do not correspond to the real position
    inside the layout. The header and footer widgets do not count as items in
    the list.
    """
    def __init__(self, *args, **kwargs):
        super(FlowWidget, self).__init__(*args, **kwargs)
        self.setLayout(QBoxLayout(QBoxLayout.TopToBottom))
        self.layout().setAlignment(Qt.AlignHCenter)
        # Array that holds the virtual items list
        self._items = []
        # Header and Footer Widgets
        self._header, self._footer = None, None
        # Add the flow arrows for header and footer but leave them invisible
        self._insert_flow_arrow(0, False)
        # Vertical spacer to align everything to the top
        self.layout().addStretch(1)

    def _t(self, pos):
        """Return a string representing the type of the widget.

        Args:
          pos (int): Position of the widget (in the layout) to get the type.

        Returns:
          str: "arrow" if its a FlowArrow instance.
            "header" if it's the header widget.
            "footer" if it's the footer widget.
            "item" if it's a QWidget that is neither an arrow, header or footer.
            "" if it's isn't a QWidget.
        """
        try:
            widget = self.layout().itemAt(pos).widget()
            if widget is None:
                return ""
            elif isinstance(widget, FlowArrow):
                return "arrow"
            elif widget is self._header:
                return "header"
            elif widget is self._footer:
                return "footer"
            elif isinstance(widget, QWidget):
                return "item"
        except:
            return ""

    def _insert_flow_arrow(self, index, visible=True):
        """Insert an arrow at specified index in the layout."""
        arrow = FlowArrow()
        if not visible:
            arrow.setVisible(False)
        self.layout().insertWidget(index, arrow)
        self.layout().setAlignment(arrow, Qt.AlignHCenter)

    def update_flow_arrows(self):
        pass

    def __iter__(self):
        return iter(self._items)

    def swap_items(self, pos_1, pos_2):
        """Swap two items from the list."""
        real_1 = self.layout().indexOf(self._items[pos_1])
        real_2 = self.layout().indexOf(self._items[pos_2])
        real_1, real_2 = min(real_1, real_2), max(real_1, real_2)

        self.layout().insertWidget(real_1, self.layout().takeAt(real_2).widget())
        self.layout().insertWidget(real_2, self.layout().takeAt(real_1+1).widget())

        self._items[pos_1], self._items[pos_2] = self._items[pos_2], self._items[pos_1]

    def add_item(self, widget):
        """Add a new item (QWidget) to the end of the list and above the footer."""
        l = self.layout()
        # One space above the vertical spacer
        last_pos = l.count() - 1
        last_pos -= 1 if self._footer is not None else 0

        l.insertWidget(last_pos, widget)
        self._items.append(widget)

        if self._t(last_pos - 1) == "arrow":
            l.itemAt(last_pos - 1).widget().setVisible(True)

        if self._t(last_pos + 1) == "arrow":
            l.itemAt(last_pos + 1).widget().setVisible(True)
        elif self._t(last_pos + 1) in ["footer", "item"]:
            self._insert_flow_arrow(last_pos + 1)

    def set_header(self, widget):
        """Set the header widget."""
        if self._header is not None:
            self.layout().removeWidget(self._header)
        self.layout().insertWidget(0, widget)
        self._header = widget

        if self._footer is not None and self._t(1) == "arrow":
            self.layout().itemAt(1).widget().setVisible(True)

    def set_footer(self, widget):
        """Set the footer widget."""
        if self._footer is not None:
            self.layout().removeWidget(self._footer)
        self.layout().insertWidget(self.layout().count() - 1, widget)
        self._footer = widget
        if self._header is not None and self._t(self.layout().count()-3) == "arrow":
            self.layout().itemAt(self.layout().count()-3).widget().setVisible(True)

    def get_item(self, pos):
        return self._items[pos]

    def clear(self):
        """Remove all items, but keep the header and footer.
        """
        for item in self._items:
            pos = self.layout().indexOf(item)
            self.layout().takeAt(pos).widget().deleteLater()
            self.layout().takeAt(pos).widget().deleteLater()
        self._items[:] = []

    def remove_item(self, pos):
        """Remove an item at the specified position.
        """
        widget = self._items[pos]
        real_pos = self.layout().indexOf(widget)
        del self._items[pos]
        self.layout().takeAt(real_pos).widget().deleteLater()
        self.layout().takeAt(real_pos).widget().deleteLater()
