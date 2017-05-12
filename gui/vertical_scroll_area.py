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
from PyQt4.QtGui import QScrollArea
from PyQt4.QtCore import QSize, QEvent

class VerticalScrollArea(QScrollArea):
    """QScrollArea optimized for a vertical Scrolling Area."""
    def __init__(self, *args, **kwargs):
        super(VerticalScrollArea, self).__init__(*args, **kwargs)
        self.setMinimumSize(QSize(100, 100))

    def _updateWidth(self):
        total_width = self.widget().minimumSizeHint().width()
        total_width += self.frameWidth()
        total_width += self.verticalScrollBar().sizeHint().width() if self.verticalScrollBar().isVisible() else 0
        self.setMinimumWidth(total_width)
        self.setMaximumWidth(total_width)

    def setWidget(self, widget):
        if self.widget() is not None:
            self.widget().removeEventFilter(self)
        widget.installEventFilter(self)
        super(VerticalScrollArea, self).setWidget(widget)

    def eventFilter(self, obj, event):
        if obj is self.widget() and (event.type() == QEvent.Resize or
         event.type() == QEvent.ChildAdded or
          event.type() ==  QEvent.ChildRemoved):
            self._updateWidth()
        return False

    def resizeEvent(self, event):
        self._updateWidth()
        super(VerticalScrollArea, self).resizeEvent(event)
