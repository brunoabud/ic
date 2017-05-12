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

from collections import deque

from PyQt4.QtCore import QMutex, QThread, QWaitCondition, QElapsedTimer

__all__ = ['Empty', 'Full', 'Queue']


class Empty(Exception):
    pass


class Full(Exception):
    pass


class Locked(Exception):
    pass

class Queue(object):
    """Create a queue object with a given maximum size.

    """
    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self.queue = deque()

        # Mutex using for accessing the deque
        self.mutex = QMutex()

        # Condition that will be held when the queue is empty and the consumer
        # needs to wait for a new item
        self.item_added = QWaitCondition()
        # Condition that will be held when the queue is full and the producer
        # needs to wait for a new place to insert the item
        self.item_removed = QWaitCondition()

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        Parameters
        ----------
        block : bool
            If True(default), the caller thread will block until the queue has
            a free space available for putting an new item. If False, the `Full`
            exception will be raised if there is no free space in the queue

        timeout : int
            The max time to wait for a new space to be avaible, in milliseconds.

        """
        self.mutex.lock()
        try:
            # Check if the queue has a limit (0 means not)
            if self.maxsize > 0:
                # Raise Full if block is False and the queue is at max cap.
                if not block:
                    if self._qsize() == self.maxsize:
                        raise Full
                # If a timeout is not provided, wait indefinitely
                elif timeout is None:
                    while self._qsize() == self.maxsize:
                        self.item_removed.wait(self.mutex)
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    timer = QElapsedTimer()
                    timer.start()
                    while self._qsize() == self.maxsize:
                        remaining = timeout - timer.elapsed()
                        if remaining <= 0.0:
                            raise Full
                        self.item_removed.wait(self.mutex, remaining)
            self._put(item)
            self.item_added.wakeOne()
        finally:
            self.mutex.unlock()

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        Parameters
        ----------
        block : bool
            If True(default), the caller thread will block until the queue has
            an item available for putting an new item. If False, the `Empty`
            exception will be raised if there is no item in the queue

        timeout : int
            The max time to wait for a new item to be avaible, in milliseconds.

        """
        self.mutex.lock()
        try:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.item_added.wait(self.mutex)
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                timer = QElapsedTimer()
                timer.start()
                while not self._qsize():
                    remaining = timeout - timer.elapsed()
                    if remaining <= 0.0:
                        raise Empty
                    self.item_added.wait(self.mutex, remaining)
            item = self._get()
            self.item_removed.wakeOne()
            return item
        finally:
            self.mutex.unlock()

    def _qsize(self, len=len):
        return len(self.queue)

    # Put a new item in the queue
    def _put(self, item):
        self.queue.append(item)

    # Get an item from the queue
    def _get(self):
        return self.queue.popleft()

    def _clear(self):
        self.queue.clear()
