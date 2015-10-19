#Bibliotecas utilizadas
from PyQt4 import QtGui, QtCore
import numpy as np
import cv2
import sys
import datetime
import Queue
class Mov_track:
	def __init__(self):		
		self.config = {}							#Cria o dicionario de configuracao utilizada para guardar informacoes sobre o processamento		
		self.config['input_type'] = 'nothing'		#Modo de entrada. Pode ser 'camera', 'video_file' ou 'nothing'
		self.config['camera_id'] = 0				#Id da camera, por enquanto apenas a camera 0 e suportada.
		self.config['threshold_value'] = 13 		#Valor de threshold
		self.config['threshold_value_c'] = 8		#Valor de threshold
		self.config['blur_value'] = 3				#Valor de blur
		self.config['dilate_kernel'] = 4			#Valor do nucleo de dilatacao
		self.config['analysing'] = False			#Se algum tipo de analise e iniciada essa variavel e igual a True
		self.config['frame_skip'] = 1				#Numero de frames que devem ser pulados. Util para videos que estao em camera lenta.
													#Atencao, este e o numero de frames que devem ser PULADOS, ou seja
													#se este valor for igual a 0, o processamento se dara normalmente (Frames consecutivos)
		self.config['video_path'] = ''				#Caminho do arquivo, caso a opcao 'input_type' seja igual a 'file'
		self.config['camera_init_wait_time'] = 5	#Tempo maximo, em segundos, para se esperar uma resposta positiva da camera
													#As vezes a camera demora um pouco para ser inicializada corretamente.					
		self.config['paused'] = True 				
		self.config['frame_pos'] = 0				#Posicao atual do frame
		self.config['total_frames'] = 0				#Numero de frames. Para Camera sempre sera 0
		self.buffer = Queue.Queue()
		self.current_frame = None
	#Incializa o buffer que ira manter sempre os ultimos (frame_skip + 2) frames carregados. Isto e necessario para evitar
	#a utilizacao das funcoes do opencv para mudar a posicao dos frames que e muito lenta
	def startBuffer(self):
		while self.config['frame_pos'] <= self.config['frame_skip']:
			ret, frame = self.getNextFrame()
			if ret:
				self.buffer.put(frame)
					
	#Funcao que inicia o processamento por camera.
	#Se esta funcao retornar False, nao foi possivel iniciar uma captura pela camera.
	def startFromCamera(self):
		cap = cv2.VideoCapture(self.config['camera_id'])		#Cria um objeto de captura
		cap.open(self.config['camera_id'])						#Abre a captura com a id de camera 
		
		if cap.isOpened() == False:
			return False

		wait_time = self.config['camera_init_wait_time']
		before = datetime.datetime.now()

		while True:
			diff = datetime.datetime.now() - before
			if diff.total_seconds() > wait_time:				#Se ultrapassar o tempo maximo de espera retorna False
				cap.release()
				return False

			ret, frame = cap.read()

			if ret == True:
				self.config['input_type'] = 'camera'
				self.config['analysing'] = True
				self.config['frame_pos'] = 0
				self.config['total_frames'] = 0
				self.cap = cap
				self.startBuffer()
				return True 									#Retorna True se foi possivel ler um frame
			cv2.waitKey(25)
	#Funcao que inicia o processamento por arquivo.
	#Se esta funcao retornar False, nao foi possivel iniciar uma captura pelo arquivo.			
	def startFromFile(self, file_path):
		cap = cv2.VideoCapture(file_path)						#Cria um objeto de captura
		cap.open(file_path)										#Abre a captura com a id de camera 
		
		if not cap.isOpened():
			return False

		ret, frame = cap.read()

		if not ret:
			return False

		self.config['input_type'] = 'file'
		self.config['analysing'] = True
		self.config['frame_pos'] = 0
		self.config['video_path'] = file_path
		self.config['total_frames'] = cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
		cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, 0)
		self.cap = cap
		self.startBuffer()
		return True 										
	
	#Para todo o processamento liberando o arquivo de video, camera e o que mais estiver sendo usado.
	def stop(self):
		self.config['input_type'] = 'nothing'
					
		self.config['frame_pos'] = 0
		self.config['video_path'] = ''
		if self.config['analysing']:
			self.cap.release()
			self.config['analysing'] = False
		
	def getCapSize(self):
		width = self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
		height = self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)

		return width, height

	def getNextFrame(self):
		ret, frame = self.cap.read()
		if ret == True:
			self.config['frame_pos'] += 1
			self.current_frame = frame
		return ret, frame

	def processNextFrame(self):
		ret, frame = self.getNextFrame()
		if not ret:
			return ret, frame

		frame1 = self.buffer.get()						#Pega o primeiro frame que esta no buffer
		frame2 = np.copy(frame)							#Faz uma copia do frame lido agora para a variavel frame2

		self.buffer.put(frame)							#Insere o frame lido agora no buffer para mante-lo atualizado
														#NOTA: no buffer deve ser inserido o frame, pois o frame2 sera manipulado e sofrera
														#alteracoes que nao queremos no buffer.
		#Agora se da inicio as rotinas de processamento/deteccao de movimento/desenho do trajeto/etc
		frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
		frame1 = cv2.blur(frame1, (self.config['blur_value'], self.config['blur_value']))

		frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
		frame2 = cv2.blur(frame2, (self.config['blur_value'], self.config['blur_value']))

		processed = cv2.absdiff(frame2, frame1)
		processed = cv2.blur(processed, (self.config['blur_value'], self.config['blur_value']))


		thresh = self.config['threshold_value'] | 0x1
		if thresh < 3:
			thresh = 3

		processed = cv2.adaptiveThreshold(processed, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
			cv2.THRESH_BINARY_INV, thresh, self.config['threshold_value_c'])
		

		kernel  = np.ones((self.config['dilate_kernel'], self.config['dilate_kernel']), np.uint8)

		processed = cv2.dilate(processed, kernel, iterations = 4)

		contorno, h = cv2.findContours(processed, cv2.RETR_EXTERNAL, 
		cv2.CHAIN_APPROX_SIMPLE)


		

		if contorno:					
			M = cv2.moments(contorno[0])
			x = int(M['m10']/M['m00'])
			y = int(M['m01']/M['m00'])
			self.current_circle_x = x
			self.current_circle_y = y			
		else:
			self.current_circle_x = -1
			self.current_circle_y = -1


		return ret, frame
	def setFramePos(self, pos):
		if pos < 0 or pos >= self.config['total_frames']:
			return False
		else:
			self.config['frame_pos'] = pos
			self.cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, pos)
			return True

	def setConfig(self, config, value):
		self.config[config] = value

	def getConfig(self, config):
		return self.config[config]

	def getFramePos(self):
		return self.config['frame_pos']

	def getTotalFrames(self):
		return self.config['total_frames']

	def getWidth(self):
		while self.current_frame is None:
			self.getNextFrame()

		shape = self.current_frame.shape
		return shape[1]

	def getHeight(self):
		while self.current_frame is None:
			self.getNextFrame()
			
		shape = self.current_frame.shape
		return shape[0]