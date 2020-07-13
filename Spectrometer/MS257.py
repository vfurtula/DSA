import numpy, sys, serial, argparse, time, re
from random import randint
import matplotlib.pyplot as plt

class MS257:
	
	def __init__(self,my_serial):
		# activate the serial. CHECK the serial port name
		#self.ser=serial.Serial(my_serial,baudrate=9600,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=8)
		print("MS257 serial port:", my_serial, "exists")
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
		eol1=b'>'
		eol2=b'>'
		leneol=len(eol1)
		line=bytearray()
		while True:
			c=self.ser.read(1)
			if c:
				line+=c
				if line[-leneol:]==eol1 or line[-leneol:]==eol2:
					break
			else:
				break
			
		return bytes(line)[:-1].decode()
	
  ####################################################################
  # MS257 functions
  ####################################################################
  
	def set_timeout(self,val):
		pass
		
	def abortSCAN(self):
		pass
	
	def getVersion(self):
		#print("The current software version is:", num)
		return "Version 1.0"
	
	def getCurrentWL(self):
		#self.ser.write('?PW\r'.encode())
		#num=self._readline()
		num = randint(0,2500)*1e-9
		return num
		
	def getCurrentPOS(self):
		#self.ser.write('?PS\r'.encode())
		#num=self._readline()
		num = randint(0,50000)
		return num
		
	def goToWL(self,wavel):
		pass
		#print("The response from the function goToWL is:", num)
		
	def goToPOS(self,pos):
		pass
		#num=self._readline()
		#print("The response from the function goToPOS is:", num)
		
	def setSHUTTER(self,onoff):
		pass
		#print("The response from the function setSYSINFO is:", num)
		
	def setSYSINFO(self,onoff):
		pass
		#num=self._readline()
		#print("The response from the function setSYSINFO is:", num)
		
	def setUNITS(self,units):
		pass
		#num=self._readline()
		#print("The response from the function setUNITS is:", num)
	
	def getUNITS(self):
		#print("The response from the function getUNITS is:", num)
		return "nm"
	
	def setGRATING(self,val):
		pass
		#print("The response from the function setUNITS is:", num)
	
	def getGRATING(self):
		return "A:1"
	
	def is_open(self):
		num = randint(0,1)
		if num==0:
			return False
		elif num==1:
			return True
		
	# clean up serial
	def close(self):
		# flush and close serial
		print("MS257 port flushed and closed")
		
		
		
def main():
  
	# call the MS257 port
	model_510 = MS257("COM3")
	
	model_510.setUNITS('NM')
	model_510.setGRATING('0')
	
	
	print(model_510.getCurrentWL())
	model_510.goToWL(50)
	print(model_510.getCurrentWL())
	
	# clean up and close the MS257 port
	model_510.close()
	
if __name__ == "__main__":
	
  main()
  


