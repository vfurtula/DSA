# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 10:21:23 2018

@author: Vedran Furtula
"""

import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt



class Oriel_stepper:
	
	def __init__(self,my_serial):
		# activate the serial. CHECK the serial port name!
		
		self.ser=serial.Serial(my_serial,baudrate=9600,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
		print("Oriel stepper serial port:", my_serial)
		time.sleep(0.5)

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
  
	# Pyserial readline() function reads until '\n' is sent (other EOLs are ignored).
	# Therefore changes to readline() are required to match it with EOL character '\r'.
	# See: http://stackoverflow.com/questions/16470903/pyserial-2-6-specify-end-of-line-in-readline
	
	def _readline(self):
		eol=b'\r'
		leneol=len(eol)
		line=bytearray()
		while True:
			c=self.ser.read(1)
			if c:
				line+=c
				if line[-leneol:]==eol:
					break
			else:
				break
		
		return bytes(line)[:-1].decode()
	
  ####################################################################
  # K2001A functions
  ####################################################################
	
	def set_timeout(self,val):
		self.ser.timeout=val
	
	def set_sf(self,val):
		#read digitized voltage value from the analog port number (dev)
		if val<0.01 or val>19999999:
			print("Scale factor should be in the range from 0.01 to 19999999")
			return ValueError
		else:
			self.ser.write(''.join(['SF=',str(val),'\r']).encode())
			time.sleep(0.25)
			
	def return_sf(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('SF*\r'.encode())
		time.sleep(0.25)
		val = self._readline()
		val = val.split()[1]
		if self.is_number(val):
			#print("return_reffreq: ", val)
			return float(val)
		else:
			print("Bad value returned from Oriel stepper (scale factor):", val)
			return ValueError
	
	
	
	def set_speed(self,val):
		#read digitized voltage value from the analog port number (dev)
		if val<0.1 or val>1000:
			print("Speed should be in the range from 0.1 to 1000")
			return ValueError
		else:
			self.ser.write(''.join(['SP=',str(val),'\r']).encode())
			time.sleep(0.25)
			
	def return_speed(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('SP*\r'.encode())
		time.sleep(0.25)
		val = self._readline()
		val = val.split()[1]
		if self.is_number(val):
			#print("return_reffreq: ", val)
			return float(val)
		else:
			print("Bad value returned from Oriel stepper (speed command):", val)
			return ValueError
	
	
	
	def set_acc(self,val):
		#read digitized voltage value from the analog port number (dev)
		if val<200 or val>100000:
			print("Acceleration should be in the range from 200 to 100000")
			return ValueError
		else:
			self.ser.write(''.join(['ACC=',str(val),'\r']).encode())
			time.sleep(0.25)
	
	def return_acc(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('AC*\r'.encode())
		time.sleep(0.25)
		val = self._readline()
		val = val.split()[1]
		if self.is_number(val):
			#print("return_reffreq: ", val)
			return float(val)
		else:
			print("Bad value returned from Oriel stepper (acceleration command):", val)
			return ValueError
	
	
	def jog_up(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('JU\r'.encode())
		time.sleep(0.25)
	
	def jog_down(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('JD\r'.encode())
		time.sleep(0.25)
	
	
	def index_up(self,val):
		#read digitized voltage value from the analog port number (dev)
		if val<0 or val>999999:
			print("Index up should be in the range from 0 to 999999")
			return ValueError
		else:
			self.ser.write(''.join(['IU=',str(int(val)),'\r']).encode())
			time.sleep(0.25)
	
	def index_down(self,val):
		#read digitized voltage value from the analog port number (dev)
		if val<0 or val>999999:
			print("Index down should be in the range from 0 to 999999")
			return ValueError
		else:
			self.ser.write(''.join(['ID=',str(-int(val)),'\r']).encode())
			time.sleep(0.25)
			
	
	
	def set_ta(self,val):
		#read digitized voltage value from the analog port number (dev)
		if float(val)<-1999999 or float(val)>1999999:
			print("Target A be in the range from -1999999 to 1999999")
			return ValueError
		else:
			self.ser.write(''.join(['TA=',str(val),'\r']).encode())
			time.sleep(0.25)
			
	def return_ta(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('TA*\r'.encode())
		time.sleep(0.25)
		val = self._readline()
		val = val.split()[1]
		if self.is_number(val):
			#print("return_reffreq: ", val)
			return float(val)
		else:
			print("Bad value returned from Oriel stepper (TA command):", val)
			return ValueError
	
	
	def set_tb(self,val):
		#read digitized voltage value from the analog port number (dev)
		if float(val)<-1999999 or float(val)>1999999:
			print("Target A be in the range from -1999999 to 1999999")
			return ValueError
		else:
			self.ser.write(''.join(['TB = ',str(val),'\r']).encode())
			time.sleep(0.25)
			
	def return_tb(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('TB*\r'.encode())
		time.sleep(0.25)
		val = self._readline()
		val = val.split()[1]
		if self.is_number(val):
			#print("return_reffreq: ", val)
			return float(val)
		else:
			print("Bad value returned from Oriel stepper (TB command):", val)
			return ValueError
		
	
	
	def goto_a(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('GA\r'.encode())
		time.sleep(2)
	
	def goto_b(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('GB\r'.encode())
		time.sleep(2)
	
	
	def run_down(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('CD\r'.encode())
		time.sleep(0.25)
	
	def run_up(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('CD\r'.encode())
		time.sleep(0.25)
		
		
	def abort(self):
		#read digitized voltage value from the analog port number (dev)
		self.ser.write('AB\r'.encode())
		time.sleep(0.25)
	
	def is_open(self):
		
		return self.ser.isOpen()
		
	# clean up serial
	def close(self):
		# flush and close serial
		self.ser.flush()
		self.ser.close()
		print("Oriel stepper port flushed and closed")
				
def main():
  
	# call the sr510 port
	os = Oriel_stepper('COM7')
	
	print(os.return_sf())
	
	print(os.return_ta())
	os.set_ta(150)
	print(os.return_ta())
	
	print(os.return_tb())
	os.set_tb(600)
	print(os.return_tb())

	os.index_up(2000)
	
	'''
	print(os.return_speed())
	time.sleep(1)
	print(os.return_ta())
	time.sleep(1)
	
	os.run_down()
	time.sleep(5)
	os.abort()
	'''
	
	os.close()

	
if __name__ == "__main__":
	
  main()
  


