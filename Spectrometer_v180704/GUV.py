# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 19:40:35 2018

@author: Vedran Furtula
"""

import sys, serial, argparse, time, re, socket
import numpy as np
from random import uniform
import matplotlib.pyplot as plt

class GUV:
	
	def __init__(self,my_serial):
		TCP_IP = my_serial[0]
		TCP_PORT = int(my_serial[1])
		#time.sleep(1)
		
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((TCP_IP, TCP_PORT))
		
	############################################################
	# Check input if a number, ie. digits or fractions such as 3.141
	# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
	def is_number(self,s):
		try:
			float(s)
			return True
		except ValueError:
			pass

		try:
			import unicodedata
			unicodedata.numeric(s)
			return True
		except (TypeError, ValueError):
			pass

		return False
	
	####################################################################
	# K2001A functions
	####################################################################
	
	def is_open(self):
		pass
	
	def return_id(self):
		#self.s.send("D")
		return "GUV OK"

	def set_dc_voltage(self):
		pass
		#read digitized voltage value from the analog port number (dev)
		#self.ser.write(":conf:volt[:dc]")

	def return_voltage(self):
		send_data=[]
		#data = ','.join([str(uniform(0,1)) for i in range(20)])
		self.s.send("D")
		data = s.recv(1024)
		for i in data.strip().split(','):
			if self.is_number(i):
				send_data.extend([float(i)])
		time.sleep(0.01)
		return send_data
		
	def close(self):
		self.s.close()
	
		
def main():
  
	# call the sr510 port
	model_510 = GUV(['127.0.0.1',2121])
	
	print(model_510.return_id())
	
	for i in range(10):
		print(model_510.return_voltage())
		time.sleep(1)
	
if __name__ == "__main__":
	
  main()
  


