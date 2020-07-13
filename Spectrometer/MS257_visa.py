import numpy, sys, visa, argparse, time, re
import matplotlib.pyplot as plt

class MS257:
	
	def __init__(self,my_serial):
		# activate the serial. CHECK the serial port name
		#self.ser=serial.Serial(my_serial,baudrate=9600,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=8)
		rm = visa.ResourceManager()
		self.ser = rm.open_resource(my_serial)
		print("MS257 serial port:", my_serial, "exists")
		time.sleep(1)
		
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
		eol2=b':'
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
		self.ser.timeout=val
		
	def abortSCAN(self):
		self.ser.write('!ABORT\r'.encode())
		num=self._readline()
		#print("The readout from abortSCAN is:", num)
	
	def getVersion(self):
		self.ser.write('?VER\r'.encode())
		num=self._readline()
		#print("The current software version is:", num)
		return num
	
	def getCurrentWL(self):
		self.ser.read_termination='\r\n>'
		num = self.ser.query_ascii_values('?PW\r')
		print("The current wavelength is:", num)
		if self.is_number(num):
			return float(num)
		
	def getCurrentPOS(self):
		self.ser.write('?PS\r'.encode())
		num=self._readline()
		print("The current position is:", num)
		if self.is_number(num):
			return num
		
	def goToWL(self,wavel):
		if self.is_number(wavel):
			self.ser.write(''.join(['!GW',str(wavel),'\r']))
		else:
			raise ValueError
		#num=self._readline()
		#print("The response from the function goToWL is:", num)
		
	def goToPOS(self,pos):
		if self.is_number(pos):
			self.ser.write(''.join(['!GS',str(pos),'\r']).encode())
		else:
			raise ValueError
		#num=self._readline()
		#print("The response from the function goToPOS is:", num)
		
	def setSHUTTER(self,onoff):
		if onoff=='on':
			self.ser.write(''.join(['!SHUTTER0\r']).encode())
		elif onoff=='off':
			self.ser.write(''.join(['!SHUTTER1\r']).encode())
		else:
			raise ValueError("setSHUTTER function accepts arguments on or off!")
		#num=self._readline()
		#print("The response from the function setSYSINFO is:", num)
		
	def setSYSINFO(self,onoff):
		if onoff=='on':
			val=self.ser.write(''.join(['?SYSINFO','\r']).encode())
			if self._readline()==0:
				self.ser.write(''.join(['!SYSINFO',1,'\r']).encode())
		elif onoff=='off':
			val=self.ser.write(''.join(['?SYSINFO','\r']).encode())
			if self._readline()==1:
				self.ser.write(''.join(['!SYSINFO',0,'\r']).encode())
		else:
			raise ValueError("setSYSINFO function accepts arguments on or off")
		#num=self._readline()
		#print("The response from the function setSYSINFO is:", num)
		
	def setUNITS(self,units):
		self.ser.read_termination='\r\n>'
		if units in ['NM','UM','WN']:
			val = self.ser.query(''.join(['?UNITS\r']))
			if val!=units:
				self.ser.write(''.join(['=UNITS',units,'\r']))
		else:
			raise ValueError("setUNITS function accepts arguments NM, UM or WN")
			
			#num=self._readline()
		print("The response from the function setUNITS is:", val)
		
	def is_open(self):
		
		return self.ser.isOpen()
		
	# clean up serial
	def close(self):
		# flush and close serial
		self.ser.close()
		print("MS257 port flushed and closed")
		
		
		
def main():
  
	# call the MS257 port
	model_510 = MS257("COM4")
	model_510.set_timeout(1)
	
	model_510.setUNITS('NM')
	
	print(model_510.getCurrentWL())
	model_510.goToWL(100)
	print(model_510.getCurrentWL())
	
	# clean up and close the MS257 port
	model_510.close()
	
if __name__ == "__main__":
	
  main()
  


