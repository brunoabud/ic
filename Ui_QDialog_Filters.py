# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './qt4-ui_files/QDialog_Filters.ui'
#
# Created: Sun Oct 25 00:50:58 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_QDialog_Filters(object):
    def setupUi(self, QDialog_Filters):
        QDialog_Filters.setObjectName(_fromUtf8("QDialog_Filters"))
        QDialog_Filters.resize(640, 480)
        self.buttonBox = QtGui.QDialogButtonBox(QDialog_Filters)
        self.buttonBox.setGeometry(QtCore.QRect(10, 440, 621, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.scrlA_filters = QtGui.QScrollArea(QDialog_Filters)
        self.scrlA_filters.setGeometry(QtCore.QRect(10, 10, 621, 421))
        self.scrlA_filters.setWidgetResizable(True)
        self.scrlA_filters.setObjectName(_fromUtf8("scrlA_filters"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 617, 417))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.scrlA_filters.setWidget(self.scrollAreaWidgetContents)

        self.retranslateUi(QDialog_Filters)
        QtCore.QMetaObject.connectSlotsByName(QDialog_Filters)

    def retranslateUi(self, QDialog_Filters):
        QDialog_Filters.setWindowTitle(_translate("QDialog_Filters", "Filtros", None))

