import sys
import traceback as tb

from PyQt4.QtCore import QThread, QTimer, qDebug
from PyQt4.QtGui import QApplication

from queue import ICQueue, Empty
from media import MediaClosedError()

class WorkerThread(QThread):
    def __init__(self, notifier):
        super(WorkerThread, self).__init__()
        #Abort the main loop?
        self.abort = False
        #Is the thread doing work?
        self.working = False
        #Number of tasks left aka number of times do_work will be called until
        #it returns True 'x' times, where 'x' is the number of tasks to do
        self.tasks_todo = 0
        #Queue that holds the commands
        self.cmds  = ICQueue()
        self.notifier = notifier

    def run(self):
        while True:
            #Process all the commands queued
            while not self.cmds.empty():
                try:
                    cmd, data = self.pull_command()
                    self.process_command(cmd, data)
                except Empty:
                    break
                except:
                    qDebug(tb.format_exc())
            #Check for the abort flag
            if self.abort:
                break
            if self.tasks_todo > 0:
                try:
                    ret = self.do_work()
                    if ret == True:
                        #If thread is working (infinite tasks to do) do not
                        #decrement, otherwise decrements one of the tasks to do
                        self.tasks_todo -= 1 if not self.working else 0
                    else:
                        #If the do work returned false, do nothing
                        pass
                except EOFError:
                    self.notifier.notify("stop_work")
                except MediaClosedError:
                    self.notifier.notify("stop_work")
                except:
                    tb.print_exc()
                    self.notifier.notify("stop_work")

    def put_command(self, cmd, data = None):
        data = {} if data is None else data
        self.cmds.put((cmd, data))

    def pull_command(self):
        return self.cmds.get(False)

    def process_command(self, cmd, data):
        try:
            if   cmd == "start":
                tasks = 'tasks' in data and data['tasks']
                if not tasks:
                    tasks = None
                try:
                    self.work_started()
                    if tasks:
                        self.working = False
                        self.tasks_todo = tasks
                    else:
                        self.working = True
                        self.tasks_todo = 1
                    self.notifier.notify("work_started", tasks=tasks)
                except:
                    pass
            elif cmd == "stop":
                try:
                    self.working = False
                    self.tasks_todo = 0
                    self.work_stopped()
                except:
                    pass
                self.notifier.notify("work_stopped")
            elif cmd == "abort":
                self.abort = True
                self.notifier.notify("aborted")
        except:
            qDebug(tb.format_exc())

    def work_started(self):
        pass

    def work_stopped(self):
        pass

    def do_work(self):
        return True
