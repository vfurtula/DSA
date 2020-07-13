import numpy, sys, serial, argparse, time, re, random, configparser
import matplotlib.pyplot as plt

class MS257:
	
	def __init__(self,my_serial, testmode):
		# activate the serial. CHECK the serial port name
		
		self.my_serial=my_serial
		self.config = configparser.ConfigParser()
		try:
			self.config.read('config.ini')
			self.ms257inport_str=self.config.get('DEFAULT','ms257inport').strip().split(',')[0]
			self.ms257outport_str=self.config.get('DEFAULT','ms257outport').strip().split(',')[0]
		except configparser.NoOptionError as e:
			print(''.join(["FAULT while reading the config.ini file\n",str(e)]))
			raise
		
		self.testmode = testmode
		if not self.testmode:
			self.ser=serial.Serial(my_serial,baudrate=9600,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=8)
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
			try:
				c=self.ser.read(1)
			except Exception as e:
				print(''.join(["FAULT while reading byte from MS257 port:\n",str(e)]))
				raise
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
		if self.testmode:
			pass
		elif not self.testmode:
			self.ser.timeout=val
		
	def abortSCAN(self):
		if self.testmode:
			pass
		elif not self.testmode:
			self.ser.write('!ABORT\r'.encode())
			num=self._readline()
			#print("The readout from abortSCAN is:", num)
	
	def getVersion(self):
		if self.testmode:
			return "MS257 TEST MODE: ?VER"
		elif not self.testmode:
			self.ser.write('?VER\r'.encode())
			num=self._readline()
			#print("The current software version is:", num)
			return num
	
	def getCurrentWL(self):
		if self.testmode:
			if hasattr(self, 'wavel'):
				unit = self.getUNITS()
				if "NM" in unit:
					return self.wavel*1e-9
				elif "UM" in unit:
					return self.wavel*1e-6
				else:
					return self.wavel
			else:
				return random.uniform(300*1e-9,1700*1e-9)
		elif not self.testmode:
			self.ser.write('?PW\r'.encode())
			num=self._readline()
			#print("The current wavelength is:", num)
			if self.is_number(num):
				unit = self.getUNITS()
				if "NM" in unit:
					return float(num)*1e-9
				elif "UM" in unit:
					return float(num)*1e-6
				else:
					return float(num)
		
	def getCurrentPOS(self):
		if self.testmode:
			if hasattr(self, 'pos'):
				return self.pos
			else:
				return random.uniform(0,20000)
		elif not self.testmode:
			self.ser.write('?PS\r'.encode())
			num=self._readline()
			#print("The current position is:", num)
			if self.is_number(num):
				return num
		
	def goToWL(self,wavel):
		if self.testmode:
			self.wavel=wavel
		elif not self.testmode:
			if self.is_number(wavel):
				self.ser.write(''.join(['!GW',str(wavel),'\r']).encode())
			else:
				raise ValueError
			num=self._readline()
			#print("The response from the function goToWL is:", num)
		
	def goToPOS(self,pos):
		if self.testmode:
			self.pos=pos
		elif not self.testmode:
			if self.is_number(pos):
				self.ser.write(''.join(['!GS',str(pos),'\r']).encode())
			else:
				raise ValueError
			num=self._readline()
			#print("The response from the function goToPOS is:", num)
		
	def setSHUTTER(self,onoff):
		if self.testmode:
			self.onoff=onoff
		elif not self.testmode:
			if onoff=='on':
				self.ser.write(''.join(['!SHUTTER0\r']).encode())
			elif onoff=='off':
				self.ser.write(''.join(['!SHUTTER1\r']).encode())
			else:
				raise ValueError("setSHUTTER function accepts arguments on or off!")
			num=self._readline()
			#print("The response from the function setSYSINFO is:", num)
		
	def setSYSINFO(self,onoff):
		if self.testmode:
			pass
		elif not self.testmode:
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
			num=self._readline()
			#print("The response from the function setSYSINFO is:", num)
		
	def setUNITS(self,units):
		if self.testmode:
			self.unit=units
		elif not self.testmode:
			if units in ['NM','UM','WN']:
				self.ser.write(''.join(['?UNITS','\r']).encode())
				if self._readline()!=units:
					self.ser.write(''.join(['=UNITS',units,'\r']).encode())
			else:
				raise ValueError("setUNITS function accepts arguments NM, UM or WN")
			num=self._readline()
			#print("The response from the function setUNITS is:", num)
	
	def getUNITS(self):
		if self.testmode:
			if hasattr(self, 'unit'):
				return self.unit
			else:
				return "NM"
		elif not self.testmode:
			self.ser.write(''.join(['?UNITS','\r']).encode())
			val = self._readline()
			#print("The response from the function getUNITS is:", num)
			return val
	
	def setGRATING(self,val):
		if self.testmode:
			self.grat=val
		elif not self.testmode:
			if val in ['0','1','2','3','4','home']:
				if val in ['0','1','2','3','4']:
					self.ser.write(''.join(['!GRAT ',val,'\r']).encode())
				elif val in ['home']:
					self.ser.write(''.join(['!GH\r']).encode())
			else:
				raise ValueError("setGRATING function accepts arguments 0, 1, 2, 3, 4 or home")
			num=self._readline()
			#print("The response from the function setUNITS is:", num)
	
	def getGRATING(self):
		if self.testmode:
			if hasattr(self, 'grat'):
				return self.grat
			else:
				return '0'
		elif not self.testmode:
			self.ser.write('?GRAT\r'.encode())
			val = self._readline()
			#print("The response from the function getUNITS is:", num)
			return val
		
	def is_open(self):
		if self.testmode:
			try:
				self.getVersion()
				return True
			except Exception as e:
				return False
		elif not self.testmode:
			return self.ser.isOpen()
		
	# clean up serial
	def close(self):
		if self.testmode:
			if self.ms257inport_str==self.my_serial:
				print("TEST MODE: MS257 input port flushed and closed")
			elif self.ms257outport_str==self.my_serial:
				print("TEST MODE: MS257 output port flushed and closed")
		elif not self.testmode:
			# flush and close serial
			self.ser.flush()
			self.ser.close()
			if self.ms257inport_str==self.my_serial:
				print("MS257 input port flushed and closed")
			elif self.ms257outport_str==self.my_serial:
				print("MS257 output port flushed and closed")
		
		
		
def main():
  
	# call the MS257 port
	model_510 = MS257("COM3", False)
	
	model_510.setUNITS('NM')
	model_510.setGRATING('0')
	
	'''
	print(model_510.getCurrentWL())
	model_510.goToWL(50)
	print(model_510.getCurrentWL())
	'''
	# clean up and close the MS257 port
	model_510.close()
	
if __name__ == "__main__":
	
  main()
  


