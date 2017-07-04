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
"""Provides an Inter-Object Message dispatching system.
"""

import logging
from Queue import Queue

from PyQt4.QtCore import QTimer

LOG = logging.getLogger(__name__)

message_queue = Queue()
message_receivers = []


def post(message_type, message_data, sender=None):
    message_queue.put((message_type, message_data, sender))

def _dispatch():
    while message_queue.qsize():
        mtype, mdata, sender =  message_queue.get()
        for r in message_receivers:
            try:
                r.message_received(mtype, mdata, sender)
            except:
                LOG.error("Message Receiver raised exception.", exc_info=True)

def register(receiver):
    if receiver not in message_receivers:
        message_receivers.append(receiver)



# The timer that is responsible for dispatching the messages
_message_timer = QTimer()
_message_timer.setInterval(20)
_message_timer.timeout.connect(_dispatch)

def start_timer():
    _message_timer.start()
