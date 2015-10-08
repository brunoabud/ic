# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './qt4-ui_files/QMainWindow_Analysis.ui'
#
# Created: Wed Oct  7 22:25:02 2015
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

class Ui_QMainWindow_Analysis(object):
    def setupUi(self, QMainWindow_Analysis):
        QMainWindow_Analysis.setObjectName(_fromUtf8("QMainWindow_Analysis"))
        QMainWindow_Analysis.resize(890, 614)
        QMainWindow_Analysis.setMinimumSize(QtCore.QSize(890, 614))
        QMainWindow_Analysis.setMaximumSize(QtCore.QSize(890, 614))
        self.centralwidget = QtGui.QWidget(QMainWindow_Analysis)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.frame = QtGui.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(0, 0, 249, 588))
        self.frame.setObjectName(_fromUtf8("frame"))
        self.gridLayout_4 = QtGui.QGridLayout(self.frame)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.tbwg_Analysis = QtGui.QTabWidget(self.centralwidget)
        self.tbwg_Analysis.setEnabled(False)
        self.tbwg_Analysis.setGeometry(QtCore.QRect(10, 10, 871, 571))
        self.tbwg_Analysis.setObjectName(_fromUtf8("tbwg_Analysis"))
        self.tb_view = QtGui.QWidget()
        self.tb_view.setObjectName(_fromUtf8("tb_view"))
        self.groupbox_previewControl = QtGui.QGroupBox(self.tb_view)
        self.groupbox_previewControl.setEnabled(False)
        self.groupbox_previewControl.setGeometry(QtCore.QRect(8, 436, 851, 101))
        self.groupbox_previewControl.setObjectName(_fromUtf8("groupbox_previewControl"))
        self.scrlbar_previewTime = QtGui.QScrollBar(self.groupbox_previewControl)
        self.scrlbar_previewTime.setEnabled(False)
        self.scrlbar_previewTime.setGeometry(QtCore.QRect(110, 50, 731, 41))
        self.scrlbar_previewTime.setMinimumSize(QtCore.QSize(0, 41))
        self.scrlbar_previewTime.setMaximumSize(QtCore.QSize(16777215, 41))
        self.scrlbar_previewTime.setTracking(True)
        self.scrlbar_previewTime.setOrientation(QtCore.Qt.Horizontal)
        self.scrlbar_previewTime.setObjectName(_fromUtf8("scrlbar_previewTime"))
        self.btn_previewPlayPause = QtGui.QPushButton(self.groupbox_previewControl)
        self.btn_previewPlayPause.setEnabled(False)
        self.btn_previewPlayPause.setGeometry(QtCore.QRect(11, 30, 91, 61))
        self.btn_previewPlayPause.setMinimumSize(QtCore.QSize(91, 61))
        self.btn_previewPlayPause.setMaximumSize(QtCore.QSize(91, 16777215))
        self.btn_previewPlayPause.setCheckable(True)
        self.btn_previewPlayPause.setChecked(False)
        self.btn_previewPlayPause.setObjectName(_fromUtf8("btn_previewPlayPause"))
        self.lbl_previewTime = QtGui.QLabel(self.groupbox_previewControl)
        self.lbl_previewTime.setEnabled(False)
        self.lbl_previewTime.setGeometry(QtCore.QRect(110, 20, 731, 17))
        self.lbl_previewTime.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_previewTime.setObjectName(_fromUtf8("lbl_previewTime"))
        self.label = QtGui.QLabel(self.tb_view)
        self.label.setGeometry(QtCore.QRect(10, 10, 851, 421))
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAutoFillBackground(False)
        self.label.setFrameShape(QtGui.QFrame.Box)
        self.label.setLineWidth(2)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.tbwg_Analysis.addTab(self.tb_view, _fromUtf8(""))
        self.tb_plots = QtGui.QWidget()
        self.tb_plots.setObjectName(_fromUtf8("tb_plots"))
        self.tbwg_Analysis.addTab(self.tb_plots, _fromUtf8(""))
        self.tb_tables = QtGui.QWidget()
        self.tb_tables.setObjectName(_fromUtf8("tb_tables"))
        self.tbwg_Analysis.addTab(self.tb_tables, _fromUtf8(""))
        QMainWindow_Analysis.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(QMainWindow_Analysis)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 890, 27))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuAn_lise = QtGui.QMenu(self.menubar)
        self.menuAn_lise.setObjectName(_fromUtf8("menuAn_lise"))
        self.menuAjuda = QtGui.QMenu(self.menubar)
        self.menuAjuda.setObjectName(_fromUtf8("menuAjuda"))
        QMainWindow_Analysis.setMenuBar(self.menubar)
        self.actn_newAnalysis = QtGui.QAction(QMainWindow_Analysis)
        self.actn_newAnalysis.setObjectName(_fromUtf8("actn_newAnalysis"))
        self.mn_Export = QtGui.QAction(QMainWindow_Analysis)
        self.mn_Export.setEnabled(False)
        self.mn_Export.setObjectName(_fromUtf8("mn_Export"))
        self.mn_userManual = QtGui.QAction(QMainWindow_Analysis)
        self.mn_userManual.setObjectName(_fromUtf8("mn_userManual"))
        self.mn_about = QtGui.QAction(QMainWindow_Analysis)
        self.mn_about.setObjectName(_fromUtf8("mn_about"))
        self.mnExit = QtGui.QAction(QMainWindow_Analysis)
        self.mnExit.setObjectName(_fromUtf8("mnExit"))
        self.menuAn_lise.addAction(self.actn_newAnalysis)
        self.menuAn_lise.addSeparator()
        self.menuAn_lise.addAction(self.mn_Export)
        self.menuAn_lise.addSeparator()
        self.menuAn_lise.addAction(self.mnExit)
        self.menuAjuda.addAction(self.mn_userManual)
        self.menuAjuda.addSeparator()
        self.menuAjuda.addAction(self.mn_about)
        self.menubar.addAction(self.menuAn_lise.menuAction())
        self.menubar.addAction(self.menuAjuda.menuAction())

        self.retranslateUi(QMainWindow_Analysis)
        self.tbwg_Analysis.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(QMainWindow_Analysis)

    def retranslateUi(self, QMainWindow_Analysis):
        QMainWindow_Analysis.setWindowTitle(_translate("QMainWindow_Analysis", "Ferramenta Visual de Análise Cinemática", None))
        self.groupbox_previewControl.setTitle(_translate("QMainWindow_Analysis", "Controle de Visualização", None))
        self.btn_previewPlayPause.setText(_translate("QMainWindow_Analysis", "Play", None))
        self.lbl_previewTime.setText(_translate("QMainWindow_Analysis", "0000000", None))
        self.label.setText(_translate("QMainWindow_Analysis", "<html><head/><body><p>Inicie uma Nova Análise no menu &quot;Análise&quot;</p></body></html>", None))
        self.tbwg_Analysis.setTabText(self.tbwg_Analysis.indexOf(self.tb_view), _translate("QMainWindow_Analysis", "Visualização", None))
        self.tbwg_Analysis.setTabText(self.tbwg_Analysis.indexOf(self.tb_plots), _translate("QMainWindow_Analysis", "Gráficos", None))
        self.tbwg_Analysis.setTabText(self.tbwg_Analysis.indexOf(self.tb_tables), _translate("QMainWindow_Analysis", "Tabelas", None))
        self.menuAn_lise.setTitle(_translate("QMainWindow_Analysis", "Análise", None))
        self.menuAjuda.setTitle(_translate("QMainWindow_Analysis", "Ajuda", None))
        self.actn_newAnalysis.setText(_translate("QMainWindow_Analysis", "Nova Análise", None))
        self.mn_Export.setText(_translate("QMainWindow_Analysis", "Exportar", None))
        self.mn_userManual.setText(_translate("QMainWindow_Analysis", "Manual do Usuário", None))
        self.mn_about.setText(_translate("QMainWindow_Analysis", "Sobre", None))
        self.mnExit.setText(_translate("QMainWindow_Analysis", "Sair", None))

