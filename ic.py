#coding: latin-1
#Bibliotecas
from PyQt4 import QtGui, QtCore
import Analysis
import sys

#Interface Gráficas
import QMainWindow_Analysis

#Inicialização da janela principal
app = QtGui.QApplication(sys.argv)

mwnd_windowAnalysis = QMainWindow_Analysis.QMainWindow_Analysis()
mwnd_windowAnalysis.show()

sys.exit(app.exec_())

