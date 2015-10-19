#coding: utf-8
from PyQt4 import QtCore, QtGui
import cv2
import numpy as np


class Analysis():
	def __init__(self, movTrack, start_frame = 1, total_frames = 0):
		#Cria todos os objetos que serao necessários na análise
		self.movTrack = movTrack 								#Objeto do tipo movTrack com o vídeo de entrada	
		self.width = self.movTrack.getWidth()
		self.height = self.movTrack.getHeight()

		self.video_output = cv2.VideoWriter('mov_track.avi', 	#Objeto do tipo VideoWriter
			cv2.cv.CV_FOURCC('X','V','I','D'), 24, (self.width, self.height))		
		if start_frame < 1 or start_frame >= self.movTrack.getTotalFrames():
			self.start_frame = 1
		else:
			self.start_frame = start_frame

		if total_frames == 0 or self.movTrack.getTotalFrames() < (total_frames + start_frame):
			self.total_frames = self.movTrack.getTotalFrames() - start_frame
		else:
			self.total_frames = total_frames

		#Cada grandeza física é representada por uma array da biblioteca numpy
		self.velocities = np.zeros([self.total_frames, 2])				#Array com as velocidades em cada frame
		self.accelerations = np.zeros([self.total_frames, 2])			#Array com as acelerações em cada frame
		self.positions =  np.zeros([self.total_frames, 2])				#Array com as posições em cada frame
		self.track_frame = np.zeros([self.height, self.width,3], np.uint8)

	def __del__(self):
		self.movTrack.stop()
		self.video_output.release()

	def analyze(self):
		self.movTrack.setFramePos(self.start_frame)

		current_frame = 0

		while self.movTrack.getFramePos() < self.start_frame + self.total_frames - 1:
			ret, frame = self.movTrack.processNextFrame()
			if ret:
				current_frame += 1
				(x,y) =  (self.movTrack.current_circle_x, self.movTrack.current_circle_y)
				self.positions[current_frame] = (x,y)

				

				if x != -1 and y != -1:
					cv2.circle(self.track_frame, (x, y), 2, (0, 0, 255), -1)


				img2gray = cv2.cvtColor(self.track_frame, cv2.COLOR_BGR2GRAY)
				ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)

				mask = cv2.bitwise_not(mask)

				out = cv2.bitwise_and(frame, frame, mask = mask)

				out = cv2.add(out, self.track_frame)

				self.video_output.write(out)

		self.video_output.release()

