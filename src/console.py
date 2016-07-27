#coding: utf-8
from os.path import join as pjoin
import traceback
import re

from PyQt4.QtGui import QWidget
from PyQt4 import uic

import main
import messages
import log

class Console(QWidget):
    def __init__(self, *args, **kwargs):
        super(Console, self).__init__(*args, **kwargs)
        uic.loadUi(pjoin(main.settings['ui_dir'], 'log_widget.ui'), self)
        messages.add_message_listener(self)
        log.add_output(self)

    def write(self, text):
        try:
            self.txt_log.insertPlainText(text.replace("\\n", "\n"))
        except:
            traceback.print_exc()

    def receive_message(self, mtype, mdata, sender):
        fstr = ("Type: <font color='red' bold=true>{}</font><br>\n"
                "Data:<font color='green' bold=true>{}</font><br>\n"
                "Sender:{}<br><br>\n").format(str(mtype), str(mdata),str(sender))
        self.txt_messages.insertHtml(fstr)
