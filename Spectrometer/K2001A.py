import sys, serial, argparse, time, re
import numpy as np
from random import randint
import matplotlib.pyplot as plt

class K2001A:
	
	def __init__(self,my_serial):
		pass
		# activate the serial. CHECK the serial port name!
		
		#rm = visa.ResourceManager()
		#self.ser = rm.open_resource(my_serial)
		#self.ser=serial.Serial(my_serial,baudrate=19200,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
		#print("K2001A serial port:", my_serial)
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
	
	def is_open(self):
		pass
	
	def return_id(self):
		pass
		return "K2001A"

	def set_dc_voltage(self):
		pass

	def return_voltage(self):
		time.sleep(0.001)
		return randint(0,1023)
		
	def close(self):
		pass

	
def main():
  
	# call the sr510 port
	model_510 = K2001A('GPIB0::10::INSTR')

	for i in range(10):
		print(model_510.return_voltage())
	
if __name__ == "__main__":
	
	main()
  


