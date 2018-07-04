#!/usr/bin/python3

import serial
import time
import sys
import threading

import asyncio
import datetime
import random
import websockets
import datetime

IMU_PORT = '/dev/ttyUSB1'
VOICE_PORT = '/dev/ttyUSB0'

voice="null"
sensor=0

async def time(websocket, path):

	global voice, sensor

	def readVoiceModule():
		try:
			ser = serial.Serial(VOICE_PORT, 9600, timeout=1)
		except:
			return

		if not ser.is_open:
			print("error: serial port not opended")
			return
		

		print(ser.name)
		print("Read Voice Module data")

		global voice

		while True:
			try:
				data = ser.read(size=2)

				if len(data) == 2 and data[0] == 0xf0:
					# if data[1] == 1:
					# 	 voice = str(data[1])
					# elif data[1] == 2:
					# 	 voice = str(data[1])
					# elif data[1] == 3:
					# 	 voice = str(data[1])
					# elif data[1] == 4:
					# 	 voice = str(data[1])
					# elif data[1] == 5:
					# 	 voice = str(data[1])
					# elif data[1] == 6:
					# 	 voice = str(data[1])				
					# else:
					# 	continue
					voice = str(data[1])
					print(voice)

			except KeyboardInterrupt:
				ser.close()
				print('Close serial')


	def readIMUData():

		global sensor

		try:
			ser = serial.Serial(IMU_PORT, 9600, timeout=1)
		except:
			return

		if not ser.is_open:
			print("error: serial port not opended")
			return 

		print(ser.name)

		while True:
			data = ser.read(size=1)
			if data == b'\x55':
				print("success!")
				ser.read(size=10)
				break;

		print("Read IMU data")

		while 1:
			try:
				data = ser.read(size=11)
				if not len(data) == 11:
					print('read serial error')
					# break 

				if data[0] != 85:
					print("error for start bit: ",data[0])
					# break

				if data[1] ==80:
					pass
					
				# if data[1] == 83: #Angle
				# 	roll = int(int.from_bytes(data[2:4], byteorder='little')/32768*180)
				# 	pitch = int(int.from_bytes(data[4:6], byteorder='little')/32768*180)
				# 	yaw = int(int.from_bytes(data[6:8], byteorder='little')/32768*180)
					#angle = "angle,"+str(roll)+","+str(pitch)+","+str(yaw)

				if data[1] == 81: #Acceleration
					ax = int(int.from_bytes(data[2:4], byteorder='little')/32768*16)
					ay = int(int.from_bytes(data[4:6], byteorder='little')/32768*16)
					az = int(int.from_bytes(data[6:8], byteorder='little')/32768*16)
					acc = "acc,"+str(ax)+","+str(ay)+","+str(az)
					#print(acc)

					sensor = ax +ay +az

					#if ax+ay+az >0:
				else:
					#print(data)
					continue
					
			except KeyboardInterrupt:
				ser.close()
				print('Close serial')


	th_IMU = threading.Thread(target = readIMUData)
	th_IMU.start()

	th_VOICE = threading.Thread(target = readVoiceModule)
	th_VOICE.start()

	e = threading.Event()
	while not e.wait(0.1):
		#print(str(voice)+","+str(sensor))
		await websocket.send(str(voice)+","+str(sensor))
		if voice!="null":
			voice = "null"

	th_IMU.join()
	th_VOICE.join()


start_server = websockets.serve(time, "127.0.0.10", 5679)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
