from os.path import join as pjoin

from PyQt4 import uic
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import QTimer

import main
import messages

class ExitDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(QDialog, self).__init__(*args, **kwargs)
        uic.loadUi(pjoin(main.settings['ui_dir'], "exit_dialog.ui"), self)

        self.steps = [("Releasing analysis objects", self.s1_release_analysis),
                      ("Exiting worker threads"    , self.s2_exit_workers)]

        messages.add_message_listener(self)
        self._timer = QTimer()
        self._timer.timeout.connect(self._timeout)
        self.current_step = -1
        self._waiting = False
        self._timer.setInterval(200)
        #Exit worker helper variables
        self.workers_aborted = False
        self.posted_exit_message = False

    def _timeout(self):
        if self.current_step < 0 or self.current_step >= len(self.steps):
            return
        self.steps[self.current_step][1]()

    def next_step(self):
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self._timer.stop()
            self.accept()
            self.close()
            self.deleteLater()
        else:
            self.lbl_status.setText(self.steps[self.current_step][0])
            self.pgr_total.setValue(self.current_step)

    def s1_release_analysis(self):
        main.ic.release()
        main.consolewindow.close()
        self.next_step()

    def s2_exit_workers(self):
        if not self.posted_exit_message:
            messages.post_message("abort_workers", {}, self)
            self.posted_exit_message = True

        if self.workers_aborted:
            self.next_step()

    def receive_message(self, mtype, mdata, sender):
        if mtype == "workers_aborted":
            self.workers_aborted = True

    def exec_(self):
        pass

    def start(self):
        self.setModal(True)
        self.setParent(None)
        self.showNormal()

        self.pgr_total.setMaximum(len(self.steps))
        self.pgr_total.setValue(0)

        self._timer.start()
        self.next_step()
