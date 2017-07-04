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

import logging
import cv2
import numpy as np

from Queue import Queue

LOG = logging.getLogger(__name__)

class Analysis(object):
    def __init__(self, filter_rack):
        self.buffer = Queue()
        self.buffer_size = 5
        self._fr = filter_rack

    def buffer_frame(self, frame_data):
        self.buffer.put(frame_data)

    def next_step(self):
        if self.buffer.qsize() < 5:
            return (None, None, self.buffer.queue[0][1])

        c1, d1, p1, ts1 = self.buffer.get()
        original = np.copy(d1)
        c1, d1, p1, ts1 = self._fr["Pre-Filter"].apply_filters((c1, d1, p1, ts1))


        i = 0
        while i < self.buffer_size - 1:
            c2, d2, p2, ts2 = self.buffer.queue[i]
            c2, d2, p2, ts2 = self._fr["Pre-Filter"].apply_filters((c2, d2, p2, ts2))

            diff = cv2.absdiff(d2, d1)
            _, diff, _, _ = self._fr["Post-Filter"].apply_filters(("GRAY", diff, p1, ts1))
            bc, binary, bpos, btsp = self._fr["Threshold"].apply_filters(("GRAY", diff, p1, ts1))

            _, contorno, h = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contorno:
                try:
                    M = cv2.moments(contorno[0])
                    x = int(M['m10']/M['m00'])
                    y = int(M['m01']/M['m00'])
                    return (int(x), int(y), original)
                except:
                    pass
            i += 1
        return (None, None, original)


    def clear_buffer(self):
        self.buffer.queue.clear()




