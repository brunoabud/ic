from PyQt4.QtCore import QElapsedTimer
class TicCounter(object):
    """Class that can count a number of tics per interval and calculate the rate.

        Constructor:
        __init__(interval = 1000): the interval to count the tics
    """
    def __init__(self, interval = 1000):
        self._timer = QElapsedTimer()
        self.counter = 0
        self.total = 0
        self.interval = interval
        self.average = 0
        self.last = 0
        self._counter = 0
        self._total = 0

    def tic(self):
        """Count one tic.

            Count one tic and set the 'last' attribute to the time elapsed
        from the first tic before 'interval' has passed. Automatically calculate
        the average and total members.
        """
        self._counter += 1
        self.last = self._timer.elapsed()
        self._total += self.last
        self._timer.start()
        if self._total >= self.interval:
            if self._counter != 0:
                self.average = self._total / self._counter
                self.total = self._total
                self.counter = self._counter
            self.restart()

    def restart(self):
        """restart the counter, average and total members to 0.
        """
        self._total = 0
        self._counter = 0
        self._timer.start()
