from Queue import Queue
import traceback

from PyQt4.QtCore import QObject, QMetaObject, QTimer, SIGNAL, SLOT, Qt
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QMutex, QThread

import messages

class ICWorker(QObject):
    '''Generic Worker that uses a timer.
    '''
    def __init__(self, worker_id):
        super(ICWorker, self).__init__()
        self._thread      = QThread()
        self._timer       = QTimer()
        self._tasks_to_do = 0
        self._commands    = Queue()
        self._working     = False
        self._worker_id   = worker_id

        QObject.connect(self._thread, SIGNAL('started()'), self._timer,
        SLOT('start()'), Qt.DirectConnection)

        QObject.connect(self._timer, SIGNAL('timeout()'), self,
        SLOT('_main()'), Qt.DirectConnection)

        QObject.connect(self._thread, SIGNAL('finished()'), self, SLOT('_thread_finished()'), Qt.DirectConnection)

        messages.add_message_listener(self)
        self._timer.start()
        self._thread.start()
        self._timer.moveToThread(self._thread)


    @pyqtSlot()
    def _main(self):
        self._process_next_command()
        if self._tasks_to_do:
            try:
                done =  self._do_work()
                self._tasks_to_do += 0 if (not done or not self._working) else 1
                self._tasks_to_do -= 0 if (not done) else 1

            except:
                traceback.print_exc()
                self._commands.put(('stop', {}))
            finally:
                pass
    @pyqtSlot()
    def _thread_finished(self):
        messages.post_message('worker_thread_finished', None, self)

    def wait(self):
        self._thread.wait()

    def exit_and_wait(self):
        self._commands.put(('exit', ''))
        self._thread.wait()

    def receive_message(self, message_type, message_data, sender):
        try:
            if not (message_data and 'id' in message_data and message_data['id'] == self._worker_id):
                return
            if message_type == 'start_worker':
                self._commands.put(('start', {'single_shot' : message_data and 'single_shot' in message_data and message_data['single_shot']}))
            elif message_type == 'stop_worker':
                self._commands.put(('stop', {}))
            elif message_type == 'exit_worker':
                self._commands.put(('exit', {}))
        except:
            pass

    def pull_command(self):
        try:
            command, kwargs = self._commands.get(False)
            return command, kwargs
        except:
            return None, None

    def push_command(self, command, kwargs):
        self._commands.put((command, kwargs))

    def process_command(self, command, kwargs):
        if command == 'start':
            try:
                self._start_work()
                self._tasks_to_do += 1
                self._working      = not kwargs['single_shot']
                messages.post_message('worker_started', {'single_shot' : not self._working, 'id': self._worker_id}, self)
            finally:
                pass
        elif command == 'stop':
            try:
                self._stop_work()
            finally:
                self._tasks_to_do = 0
                self._working     = False
                messages.post_message('worker_stopped', {'id': self._worker_id}, self)
        elif command == 'exit':
            try:
                self._stop_work()
            finally:
                self._tasks_to_do = 0
                self._working     = False
                self._thread.exit(0)


    def _process_next_command(self):
        command, kwargs = self.pull_command()
        if command:
            self.process_command(command, kwargs)

    #Override these functions!!
    @pyqtSlot()
    def _do_work(self):
        pass

    @pyqtSlot()
    def _stop_work(self):
        pass

    @pyqtSlot()
    def _start_work(self):
        pass
