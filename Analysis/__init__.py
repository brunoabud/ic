#coding: utf-8
import mov_tracker
import cv2
import vinput
import numpy as np
import Queue
#Inicializa as variáveis de controle de Análise
initialized = False
input_videoCapture = cv2.VideoCapture()
currentFrame = None
currentFrameI = -1
filter_params = {}
coordsSystemPos = (0, 0)
coordsSystemAngle = 0.0
realPxRatio = 1.0

def addFilterParams(filter_title, filter_name, min_value, max_value, value, default_value):
	global filter_params
	filter_params[str(filter_name)] = {}
	filter_params[str(filter_name)]['min_value'] 		= int(min_value)
	filter_params[str(filter_name)]['max_value']		= int(max_value)
	filter_params[str(filter_name)]['value']	 		= int(value)
	filter_params[str(filter_name)]['default_value']	= int(default_value)
	filter_params[str(filter_name)]['filter_title']		= filter_title

def changeFilterParams(filter_name, param, param_value):
	global filter_params
	filter_params[str(filter_name)][str(param)] = param_value

def getFilterParam(filter_name, param):
	global filter_params
	return filter_params[str(filter_name)][str(param)]

def toDefaultFilterValue(filter_name):
	global filter_params
	filter_params[str(filter_name)]['value'] = filter_params[str(filter_name)]['default_value']
	return filter_params[str(filter_name)]['value']

def getCurrentFrame():
	global currentFrame
	if currentFrame is not None:
		return True, currentFrame
	else:
		return False, None

def getNextFrame():
	global input_videoCapture, currentFrameI, currentFrame
	if currentFrameI >= get_cap_totalFrames() - 1:
		return False, None

	ret, frame = input_videoCapture.read()
	if ret:
		currentFrameI += 1
		currentFrame = np.copy(frame)
	return ret, frame

def getVideoDimensions():
	global currentFrame, input_videoCapture

	if currentFrame is None:
		ret, frame = input_videoCapture.read()
		while not ret:
			ret, frame = input_videoCapture.read()
		shape = frame.shape
	else:
		shape = currentFrame.shape
	

	input_videoCapture.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, currentFrameI - 1)
	return shape[1], shape[0]

def clearAnalysis():
	global initialized, input_videoCapture, filter_params
	closeInput()
	filter_params = {}

def closeInput():
	global input_videoCapture
	if input_videoCapture.isOpened():
		input_videoCapture.release()

def open_input_fromFile(path = ''):
	global input_videoCapture

	if path == '':
		return False
	else:
		closeInput()
		ret = input_videoCapture.open(path)
		return ret

def get_cap_totalFrames():
	global input_videoCapture
	if input_videoCapture.isOpened():
		return input_videoCapture.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
	else:
		return 0

def get_cap_framePos():
	global currentFrameI
	return currentFrameI

def get_cap_currentFrame():
	global currentFrame
	return currentFrame

def set_cap_framePos(pos):
	global input_videoCapture, currentFrame, currentFrameI

	if pos >= get_cap_totalFrames():
		pos = get_cap_totalFrames() - 1

	if pos < 0:
		pos = 0

	if input_videoCapture.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, pos):
		currentFrameI = pos
		getNextFrame()	
	
	

def analyze(astart_frame = 0, atotal_frames = 0, afps = 240):
	global input_videoCapture, currentFrame, currentFrameI, positions, start_frame, total_frames, frame_buffer, initialized, fps
	fps = afps
	if get_cap_totalFrames() == 0:
		return False

	if astart_frame < 0 or astart_frame >= get_cap_totalFrames():
		start_frame = 0
	else:
		start_frame = astart_frame

	if start_frame + atotal_frames > get_cap_totalFrames() or atotal_frames == 0:
		total_frames = get_cap_totalFrames() - start_frame
	else:
		total_frames = atotal_frames

	set_cap_framePos(start_frame)

	#Abre o arquivo de video onde sera desenhado o trajeto da bolinha
	width, height = getVideoDimensions()

	video_out = cv2.VideoWriter('mov_track.avi', 	
			cv2.cv.CV_FOURCC('X','V','I','D'), afps, (width, height))

	track_frame = np.zeros([height, width,3], np.uint8)

	#Inicializa a array que armazenará as posições
	positions = np.zeros((2, total_frames - 1), np.float64)

	#Obter o primeiro frame
	ret1, last_frame = getNextFrame()
	last_frame_i = currentFrameI
	
	frame_buffer = Queue.Queue()

	while ret1 and currentFrameI < start_frame + total_frames:
		mov_ret = False
		frame_buffer.put(np.copy(last_frame))

		while not mov_ret and currentFrameI < start_frame + total_frames:
			#Obtem o proximo frame
			ret2, current_frame = getNextFrame()

			if not ret2:
				return False

			frame_buffer.put(np.copy(current_frame))

			#Detecta movimento entre os dois frames
			mov_ret, x, y = mov_tracker.findMovement(last_frame, current_frame)		
		if mov_ret:
			cv2.circle(track_frame, (x, y), 2, (0, 0, 255), -1)

			for i in range(last_frame_i - start_frame, currentFrameI + 1 - start_frame):
				if i >= total_frames - 1:
					break
				positions[0, i] = x
				positions[1, i] = y

				img2gray = cv2.cvtColor(track_frame, cv2.COLOR_BGR2GRAY)
				ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)

				mask = cv2.bitwise_not(mask)

				out = frame_buffer.get()

				out = cv2.bitwise_and(out, out, mask = mask)

				out = cv2.add(out, track_frame)

				video_out.write(out)

		else:
			for i in range(last_frame_i - start_frame, currentFrameI - start_frame):
				if i >= total_frames - 1:
					break
				positions[i] = positions(last_frame_i - 1)

		ret1, last_frame = getNextFrame()
		last_frame_i = currentFrameI
	video_out.release()
	initialized = True
	return True