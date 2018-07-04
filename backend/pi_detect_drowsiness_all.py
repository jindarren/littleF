# import the necessary packages
from imutils.video import VideoStream
from imutils import face_utils
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2

import asyncio
import datetime
import random
import websockets
import datetime

# initialize the frame counter as well as a boolean used to
# indicate if the alarm is going off
def euclidean_dist(ptA, ptB):
	# compute and return the euclidean distance between the two
	# points
	return np.linalg.norm(ptA - ptB)

def eye_aspect_ratio(eye):
	# compute the euclidean distances between the two sets of
	# vertical eye landmarks (x, y)-coordinates
	A = euclidean_dist(eye[1], eye[5])
	B = euclidean_dist(eye[2], eye[4])

	# compute the euclidean distance between the horizontal
	# eye landmark (x, y)-coordinates
	C = euclidean_dist(eye[0], eye[3])

	# compute the eye aspect ratio
	ear = (A + B) / (2.0 * C)

	# return the eye aspect ratio
	return ear
 
# construct the argument parse and parse the arguments
# ap = argparse.ArgumentParser()
# ap.add_argument("-c", "--cascade", required=True,
# 	help = "path to where the face cascade resides")
# ap.add_argument("-p", "--shape-predictor", required=True,
# 	help="path to facial landmark predictor")

# args = vars(ap.parse_args())

# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
#predictor = dlib.shape_predictor(args["shape_predictor"])

predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")


# grab the indexes of the facial landmarks for the left and
# right eye, respectively
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# start the video stream thread
print("[INFO] starting video stream thread...")
#vs = VideoStream(src=0).start()
vs = VideoStream(usePiCamera=True).start()
time.sleep(1.0)

async def time(websocket, path):
	EYE_AR_THRESH = 0.15
	EYE_AR_CONSEC_FRAMES = 3

	# define two constants, one for the eye aspect ratio to indicate
	# blink and then a second constant for the number of consecutive
	# frames the eye must be below the threshold for to set off the
	# alarm
	ONBLINK = False
	COUNTER = 0
	face_num = 0
	ITERATION = 0
	SKIP_FRAMES = 7

	# loop over frames from the video stream
	while True:
		# grab the frame from the threaded video file stream, resize
		# it, and convert it to grayscale
		# channels)
		# startTime = datetime.datetime.now()
		frame = vs.read()
		frame = imutils.resize(frame, width=200)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		# detect faces in the grayscale frame
		# frame skip

		if(ITERATION%SKIP_FRAMES == 0):
			rects = detector(gray, 0);
		
		ITERATION+= 1;

		face_num = len(rects)

		if len(rects)==0:
			await websocket.send("null")

		# loop over the face detections
		for rect in rects:
			# determine the facial landmarks for the face region, then
			# convert the facial landmark (x, y)-coordinates to a NumPy
			# array
			face_index = list(rects).index(rect);

			shape = predictor(gray, rect)
			shape = face_utils.shape_to_np(shape)

			# extract the left and right eye coordinates, then use the
			# coordinates to compute the eface_numye aspect ratio for both eyes
			leftEye = shape[lStart:lEnd]
			rightEye = shape[rStart:rEnd]
			leftEAR = eye_aspect_ratio(leftEye)
			rightEAR = eye_aspect_ratio(rightEye)

			# average the eye aspect ratio together for both eyes
			ear = (leftEAR + rightEAR) / 2.0

			# loop over the (x, y)-coordinates for the facial landmarks
			# and draw them on the image
			for (x, y) in shape:
				cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

			# # compute the convex hull for the left and right eye, then
			# # visualize each of the eyes
			# leftEyeHull = cv2.convexHull(leftEye)
			# rightEyeHull = cv2.convexHull(rightEye)
			# cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
			# cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

			# check to see if the eye aspect ratio is below the blink
			# threshold, and if so, increment the blink frame counter
			if ear < EYE_AR_THRESH:
				COUNTER += 1

				# if the eyes were closed for a sufficient number of
				# frames, then sound the alarm
				if COUNTER >= EYE_AR_CONSEC_FRAMES:
					if not ONBLINK:
						ONBLINK = True

					# # draw an alarm on the frame
					cv2.putText(frame, "Blink!", (10, 30),
						cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

			# otherwise, the eye aspect ratio is not below the blink
			# threshold, so reset the counter and alarm
			else:
				COUNTER = 0
				ONBLINK = False

			await websocket.send(
				str(shape[66][1]-shape[62][1])+","  #Y distance mouth
				+str(shape[54][0]-shape[48][0])+"," #X distance mouth
				+str(shape[33][1]-shape[19][1])+"," #Y distance eyebrow
				+str(shape[22][0]-shape[21][0])+"," #X distance eyebrow
				+str(shape[51][1]-shape[33][1])+"," #distance between lib and nose
				+str(ONBLINK)+"," #Eye blink
				+str(shape[14][0]-shape[2][0])+"," #Face width
				+str(shape[8][1]-shape[0][1])+"," #Face Height
				+str(face_num)+"," #Face numbers
				+str(face_index)+"," # face index
				+str(shape[14][0]-shape[33][0])+"," # rotate face
				+str(shape[54][1]-shape[48][1])) # lip

			# await asyncio.sleep(1/24)
			# draw the computed eye aspect ratio on the frame to help
			# with debugging and setting the correct eye aspect ratio
			# thresholds and frame counters
			# cv2.putText(frame, "EAR: {:.3f}".format(ear), (300, 30),
			# 	cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

		# show the frame
		cv2.imshow("Frame", frame)
		# endTime = datetime.datetime.now()
		# print(endTime-startTime)

		# if the `q` key was pressed, break from the loop
		key = cv2.waitKey(1) & 0xFF

		if key == ord("q"):
			break

	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()

start_server = websockets.serve(time, '127.0.0.1', 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
