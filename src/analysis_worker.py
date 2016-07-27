from PyQt4.QtCore import QMutex

from reader_thread import ReaderThread
from processor_thread import ProcessorThread
import messages
import log
import main


class Notifier(object):
    def __init__(self, mutex):
        self.callbacks = {}
        self.mutex = mutex

    def add_callback(self, label, function):
        self.callbacks.setdefault(label, set()).add(function)

    def remove_callback(self, function):
        for d in self.callbacks:
            d.discard(function)

    def notify(self, label, *args, **kwargs):
        self.mutex.lock()
        d = self.callbacks.get(label, set())
        for f in d:
            try:
                f(*args, **kwargs)
            except:
                log.dump_traceback()
        self.mutex.unlock()


class AnalysisWorker(object):
    def __init__(self):
        self.mutex = QMutex()
        self.reader_notifier = Notifier(self.mutex)
        self.processor_notifier = Notifier(self.mutex)
        self.reader    = ReaderThread(self.reader_notifier)
        self.processor = ProcessorThread(self.processor_notifier)
        self.processor.start()
        self.reader.start()
        messages.add_message_listener(self)

        self.working = False
        self.counter = 0
        self.abort_counter = 0
        self.reader_notifier.add_callback("work_started", self.work_started)
        self.processor_notifier.add_callback("work_started", self.work_started)

        self.reader_notifier.add_callback("work_stopped", self.work_stopped)
        self.processor_notifier.add_callback("work_stopped", self.work_stopped)

        self.reader_notifier.add_callback("stop_work", self.stop_work)
        self.processor_notifier.add_callback("stop_work", self.stop_work)

        self.reader_notifier.add_callback("aborted", self.aborted)
        self.processor_notifier.add_callback("aborted", self.aborted)

        self.waiting_for_seek = False
        self.seek_pos = None

    def aborted(self):
        self.abort_counter += 1
        if self.abort_counter == 2:
            messages.post_message("workers_aborted", {}, self)

    def stop_work(self):
        self.reader.put_command("stop", {})
        self.processor.put_command("stop", {})

    def work_started(self, *args, **kwargs):
        self.counter += 1
        if self.counter == 2:
            if self.waiting_for_seek:
                self.waiting_for_seek = False
            else:
                messages.post_message("workers_started", {"tasks": kwargs["tasks"]}, self)
                self.working = True

    def work_stopped(self):
        self.counter -= 1
        if self.counter == 0:
            if self.waiting_for_seek:
                main.rawqueue.clear()
                main.previewqueue.clear()
                try:
                    if main.ic.media.seek(self.seek_pos):
                        messages.post_message("media_sought", {"pos": self.seek_pos}, self)
                        self.seek_pos = None
                except:
                    log.dump_traceback()
                self.reader.put_command("start", {})
                self.processor.put_command("start", {})
            else:
                messages.post_message("workers_stopped", {}, self)
                self.working = False

    def media_seeked(self, pos):
        messages.post_message("media_sought", {"pos": pos}, self)

    def receive_message(self, mtype, mdata, sender):
        if mtype == "start_workers":
            self.reader.put_command("start", {"tasks": mdata["tasks"]})
            self.processor.put_command("start", {"tasks": mdata["tasks"]})
        elif mtype == "stop_workers":
            self.reader.put_command("stop", {})
            self.processor.put_command("stop", {})
        elif mtype == "abort_workers":
            self.reader.put_command("abort", {})
            self.processor.put_command("abort", {})
        elif mtype == "media_seek":
            self.mutex.lock()
            if self.working:
                self.reader.put_command("stop", {})
                self.processor.put_command("stop", {})
                self.waiting_for_seek = True
                self.seek_pos = mdata["pos"]
            else:
                print "   Seeking..."
                main.rawqueue.clear()
                main.previewqueue.clear()
                try:
                    if main.ic.media.seek(mdata["pos"]):
                        self.reader.put_command("start", {"tasks": 1})
                        self.processor.put_command("start", {"tasks": 1})
                        messages.post_message("media_sought", {"pos": mdata["pos"]}, self)
                except:
                    log.dump_traceback()
            self.mutex.unlock()
