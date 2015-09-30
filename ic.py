#Bibliotecas utilizadas
from PyQt4 import QtGui, QtCore
import numpy as np
import cv2
import sys
#Arquivos de interface grafica
import main_window 					#Janela Principal
import main_window_events			#Eventos, conexoes etc da Janela Principal		
#Modulo com as funcoes de processamento de video e deteccao de movimento
import Mov_track



if __name__ == '__main__':
	#Inicializacao do modulo principal do aplicativo
	app = QtGui.QApplication(sys.argv)
	#Na minha versao do linux Mint existe um bug com o tema gtk(Tema padrao do Qt)
	#Para resolver isso direamente pelo codigo basta mudar o tema para qualquer outro
	#No caso escolhi o cleanlooks.
	app.setStyle('cleanlooks')
	#Cria a janela principal do programa
	mainWindow = QtGui.QMainWindow()
	#Iguala a nossa classe principal, gerada pelo pyuic4
	mainWindow_ui = main_window.Ui_main_window()
	#Inicializa os componentes da janela
	mainWindow_ui.setupUi(mainWindow)
	#Cria o objeto que ira processar o video e detectar movimentos
	movTrack = Mov_track.Mov_track()
	#Cria o objeto que ira gerenciar os eventos da janela principal
	mainWindow_events = main_window_events.Events_main_window(mainWindow_ui, movTrack)
	#Exibe a janela
	mainWindow.show()
	#Inicia a aplicacao de modo a sair do interpretador quando a
	#aplicacao for encerrada
	exit_code = app.exec_()
	mainWindow_events.stopProcessing()
	sys.exit(exit_code)