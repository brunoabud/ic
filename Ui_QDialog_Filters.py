# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './qt4-ui_files/QDialog_Filters.ui'
#
# Created: Sun Oct 18 23:49:32 2015
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
        self.frame = QtGui.QFrame(QDialog_Filters)
        self.frame.setGeometry(QtCore.QRect(90, 20, 491, 421))
        self.frame.setObjectName(_fromUtf8("frame"))
        self.gridLayout = QtGui.QGridLayout(self.frame)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_7 = QtGui.QLabel(self.frame)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridLayout.addWidget(self.label_7, 4, 1, 1, 1)
        self.sldr_preThreshold = QtGui.QSlider(self.frame)
        self.sldr_preThreshold.setMinimum(3)
        self.sldr_preThreshold.setMaximum(500)
        self.sldr_preThreshold.setSingleStep(2)
        self.sldr_preThreshold.setPageStep(6)
        self.sldr_preThreshold.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_preThreshold.setObjectName(_fromUtf8("sldr_preThreshold"))
        self.gridLayout.addWidget(self.sldr_preThreshold, 5, 0, 1, 2)
        self.sldr_preBlur = QtGui.QSlider(self.frame)
        self.sldr_preBlur.setMinimum(1)
        self.sldr_preBlur.setMaximum(500)
        self.sldr_preBlur.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_preBlur.setObjectName(_fromUtf8("sldr_preBlur"))
        self.gridLayout.addWidget(self.sldr_preBlur, 1, 0, 1, 2)
        self.label_5 = QtGui.QLabel(self.frame)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self.frame)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.sldr_postBlur = QtGui.QSlider(self.frame)
        self.sldr_postBlur.setMinimum(1)
        self.sldr_postBlur.setMaximum(500)
        self.sldr_postBlur.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_postBlur.setObjectName(_fromUtf8("sldr_postBlur"))
        self.gridLayout.addWidget(self.sldr_postBlur, 3, 0, 1, 2)
        self.label_9 = QtGui.QLabel(self.frame)
        self.label_9.setObjectName(_fromUtf8("label_9"))
        self.gridLayout.addWidget(self.label_9, 14, 0, 1, 1)
        self.sldr_frameSkip = QtGui.QSlider(self.frame)
        self.sldr_frameSkip.setMinimum(0)
        self.sldr_frameSkip.setMaximum(50)
        self.sldr_frameSkip.setSingleStep(1)
        self.sldr_frameSkip.setPageStep(5)
        self.sldr_frameSkip.setProperty("value", 0)
        self.sldr_frameSkip.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_frameSkip.setObjectName(_fromUtf8("sldr_frameSkip"))
        self.gridLayout.addWidget(self.sldr_frameSkip, 16, 0, 1, 2)
        self.label_10 = QtGui.QLabel(self.frame)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.gridLayout.addWidget(self.label_10, 14, 1, 1, 1)
        self.label = QtGui.QLabel(self.frame)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_3 = QtGui.QLabel(self.frame)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)
        self.label_6 = QtGui.QLabel(self.frame)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 2, 1, 1, 1)
        self.sldr_dilateKernelSize = QtGui.QSlider(self.frame)
        self.sldr_dilateKernelSize.setMinimum(0)
        self.sldr_dilateKernelSize.setMaximum(50)
        self.sldr_dilateKernelSize.setSingleStep(1)
        self.sldr_dilateKernelSize.setPageStep(5)
        self.sldr_dilateKernelSize.setProperty("value", 0)
        self.sldr_dilateKernelSize.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_dilateKernelSize.setObjectName(_fromUtf8("sldr_dilateKernelSize"))
        self.gridLayout.addWidget(self.sldr_dilateKernelSize, 9, 0, 1, 2)
        self.label_11 = QtGui.QLabel(self.frame)
        self.label_11.setObjectName(_fromUtf8("label_11"))
        self.gridLayout.addWidget(self.label_11, 8, 0, 1, 1)
        self.label_4 = QtGui.QLabel(self.frame)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 6, 0, 1, 1)
        self.label_8 = QtGui.QLabel(self.frame)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.gridLayout.addWidget(self.label_8, 6, 1, 1, 1)
        self.sldr_threshC = QtGui.QSlider(self.frame)
        self.sldr_threshC.setMinimum(3)
        self.sldr_threshC.setMaximum(500)
        self.sldr_threshC.setSingleStep(2)
        self.sldr_threshC.setPageStep(6)
        self.sldr_threshC.setOrientation(QtCore.Qt.Horizontal)
        self.sldr_threshC.setObjectName(_fromUtf8("sldr_threshC"))
        self.gridLayout.addWidget(self.sldr_threshC, 7, 0, 1, 2)
        self.label_12 = QtGui.QLabel(self.frame)
        self.label_12.setObjectName(_fromUtf8("label_12"))
        self.gridLayout.addWidget(self.label_12, 8, 1, 1, 1)

        self.retranslateUi(QDialog_Filters)
        QtCore.QObject.connect(self.sldr_preBlur, QtCore.SIGNAL(_fromUtf8("valueChanged(int)")), self.label_5.setNum)
        QtCore.QObject.connect(self.sldr_postBlur, QtCore.SIGNAL(_fromUtf8("valueChanged(int)")), self.label_6.setNum)
        QtCore.QObject.connect(self.sldr_preThreshold, QtCore.SIGNAL(_fromUtf8("valueChanged(int)")), self.label_7.setNum)
        QtCore.QObject.connect(self.sldr_threshC, QtCore.SIGNAL(_fromUtf8("valueChanged(int)")), self.label_8.setNum)
        QtCore.QObject.connect(self.sldr_frameSkip, QtCore.SIGNAL(_fromUtf8("valueChanged(int)")), self.label_10.setNum)
        QtCore.QObject.connect(self.sldr_dilateKernelSize, QtCore.SIGNAL(_fromUtf8("valueChanged(int)")), self.label_12.setNum)
        QtCore.QMetaObject.connectSlotsByName(QDialog_Filters)

    def retranslateUi(self, QDialog_Filters):
        QDialog_Filters.setWindowTitle(_translate("QDialog_Filters", "Filtros", None))
        self.label_7.setText(_translate("QDialog_Filters", "3", None))
        self.label_5.setText(_translate("QDialog_Filters", "1", None))
        self.label_2.setText(_translate("QDialog_Filters", "Pós-Blur", None))
        self.label_9.setText(_translate("QDialog_Filters", "Frame Skip", None))
        self.label_10.setText(_translate("QDialog_Filters", "0", None))
        self.label.setText(_translate("QDialog_Filters", "Pré-Blur", None))
        self.label_3.setText(_translate("QDialog_Filters", "Threshold Size", None))
        self.label_6.setText(_translate("QDialog_Filters", "1", None))
        self.label_11.setText(_translate("QDialog_Filters", "Dilate Kernel Size", None))
        self.label_4.setText(_translate("QDialog_Filters", "Threshold Constant", None))
        self.label_8.setText(_translate("QDialog_Filters", "3", None))
        self.label_12.setText(_translate("QDialog_Filters", "0", None))

