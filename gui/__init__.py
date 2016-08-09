#coding: latin-1
from PyQt4.QtCore import QCoreApplication, QString
from PyQt4.QtGui import QApplication

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig = ""):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig = ""):
        return QApplication.translate(context, text, disambig)


def tr(*args, **kwargs):
    return _translate(*args, **kwargs)
