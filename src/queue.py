from Queue import Queue, Empty, Full

class ICQueue(Queue):
    def clear(self):
        self.mutex.acquire()
        try:
            self.queue.clear()
            self.not_full.notify()
        finally:
            self.mutex.release()
