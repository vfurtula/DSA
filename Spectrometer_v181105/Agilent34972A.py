# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 19:40:35 2018

@author: Vedran Furtula
"""

import sys, serial, argparse, time, re, random, visa
import numpy as np
import matplotlib.pyplot as plt

class Agilent34972A:
	
	def __init__(self,my_serial,testmode):
		# activate the serial. CHECK the serial port name!
		
		self.testmode = testmode
		if not self.testmode:
			rm = visa.ResourceManager()
			self.ser = rm.open_resource(my_serial)
			time.sleep(0.25)
		#self.ser=serial.Serial(my_serial,baudrate=19200,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
		#print("Agilent 34972A serial port:", my_serial))
		#time.sleep(1)

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
	
	def return_id(self):
		if self.testmode:
			return "TEST MODE Agilent 34972A: return_id"
		elif not self.testmode:
			val = self.ser.query("*idn?")
			return val
	
	def set_dc_voltage(self):
		if self.testmode:
			return "TEST MODE Agilent 34972A: set_dc_voltage"
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			self.ser.write(":conf:volt[:dc]")
	
	def return_voltage(self):
		if self.testmode:
			time.sleep(0.01)
			return random.uniform(-1,20)
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			val = self.ser.query("meas:volt:dc? 1,0.003,(@101)")
			if self.is_number(val):
				#print("return_reffreq: ", val)
				return float(val)
			else:
				print("Bad value returned from Agilent 34972A (read command):", val)
				return ValueError
	
	def is_open(self):
		try:
			return True
		except Exception as e:
			return False
		
	def close(self):
		if self.testmode:
			print("TEST MODE: Agilent 34972A: port flushed and closed")
		elif not self.testmode:
			#self.ser.close()
			print("Agilent 34972A port flushed and closed")
		
		
def main():
  
	# call the sr510 port
	model_510 = Agilent34972A('USB0::0x0957::0x2007::MY49017249::0::INSTR',False)
	
	print(model_510.return_id())
	
	for i in range(10):
		print(model_510.return_voltage())
		time.sleep(1)
	
if __name__ == "__main__":
	
  main()
  


