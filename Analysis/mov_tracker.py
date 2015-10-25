#Bibliotecas utilizadas
from PyQt4 import QtGui, QtCore
import numpy as np
import cv2
import sys
import datetime
import Queue
import Analysis


def findMovement(frame1, frame2):
	#Agora se da inicio as rotinas de processamento/deteccao de movimento/desenho do trajeto/etc
		

		blur = int(Analysis.getFilterParam('preBlur', 'value'))

		frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
		frame1 = cv2.blur(frame1, (blur, blur))

		frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
		frame2 = cv2.blur(frame2, (blur, blur))

		processed = cv2.absdiff(frame2, frame1)
		processed = cv2.blur(processed, (blur, blur))


		thresh = int(Analysis.getFilterParam('preThreshold', 'value')) | 0x1
		threshC = int(Analysis.getFilterParam('threshC', 'value'))
		if thresh < 3:
			thresh = 3

		processed = cv2.adaptiveThreshold(processed, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
			cv2.THRESH_BINARY_INV, thresh, threshC)
		
		kernel_size = int(Analysis.getFilterParam('dilateKernelSize', 'value'))
		kernel  = np.ones((kernel_size, kernel_size), np.uint8)

		processed = cv2.dilate(processed, kernel, iterations = 4)

		contorno, h = cv2.findContours(processed, cv2.RETR_EXTERNAL, 
		cv2.CHAIN_APPROX_SIMPLE)		

		if contorno:					
			M = cv2.moments(contorno[0])
			x = int(M['m10']/M['m00'])
			y = int(M['m01']/M['m00'])
			return True, x, y		
		else:
			return False, -1, -1


