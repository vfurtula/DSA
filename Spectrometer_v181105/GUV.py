# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 19:40:35 2018

@author: Vedran Furtula
"""

import sys, serial, argparse, time, re, socket, random, os, configparser
from random import uniform
import matplotlib.pyplot as plt

class GUV:
	
	def __init__(self,my_vars,testmode):
		
		self.my_vars=my_vars
		TCP_IP = self.my_vars[0]
		TCP_PORT = self.my_vars[1]
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		## Save the data in a text file for further inspection  ######
		self.config.read('config.ini')
		self.log_guv=self.bool_(self.config.get('DEFAULT','log_guv'))
		self.time_str=self.config.get('DEFAULT','timetrace')
		if self.log_guv:
			self.my_file = ''.join(['txt/All_GUVdata_',self.time_str,'.txt'])
			head, tail = os.path.split(self.my_file)
			# Check if folder exists and if not create it
			if head:
				if not os.path.isdir(head):
					os.mkdir(head)
			with open(self.my_file, 'w'):
				pass
		
		self.testmode = testmode
		if not self.testmode:
			self.guv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.guv.connect((TCP_IP, int(TCP_PORT)))
			time.sleep(0.25)
			
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
	
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
	####################################################################
	# GUV functions
	####################################################################
	
	def return_id(self):
		
		if self.testmode:
			return "TEST MODE OPERATION: return_id"
		elif not self.testmode:
			self.guv.send("L".encode())
			data = self.guv.recv(1024)
			return data
	
	def return_units(self):
		
		if self.testmode:
			return "TEST MODE OPERATION: return_units"
		elif not self.testmode:
			self.guv.send("U".encode())
			data = self.guv.recv(1024)
			return data
	
	def return_temp(self):
		
		if self.my_vars[2]=="GUV-541":
			inds=[6]
		elif self.my_vars[2]=="GUV-2511":
			inds=[9]
		elif self.my_vars[2]=="GUV-3511":
			inds=[35]
		else:
			return None
		
		while True:
			data = []
			if not self.testmode:
				self.guv.send("D".encode())
				data = self.guv.recv(1024)
				data = data.decode().strip().split(',')
			if self.testmode:
				data = [str(random.uniform(35,45)) for i in range(range(random.randint(20,40)))]
				time.sleep(0.05)
			
			data_ = []
			if len(data)>=inds[-1]+1:
				for i in inds:
					if self.is_number(data[i]):
						data_.extend([float(data[i])])
					
			if len(data_)==len(inds):
				return data_
			
			
	def return_powden(self):
		
		if self.my_vars[2]=="GUV-541":
			#print("GUV-541")
			inds=[1,2,3,4,5]
		elif self.my_vars[2]=="GUV-2511":
			#print("GUV-2511")
			inds=[2,3,4,5,6,7,8]
		elif self.my_vars[2]=="GUV-3511":
			#print("GUV-3511")
			inds=[16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34]
		else:
			return None
		
		while True:
			data = []
			if not self.testmode:
				self.guv.send("D".encode())
				data = self.guv.recv(1024)
				data = data.decode().strip().split(',')
			if self.testmode:
				data = [format(random.uniform(-1,20),'.3e') for i in range(random.randint(20,40))]
				time.sleep(0.05)
			
			##############################################################
			## Save the data in a text file for further inspection  ######
			if self.log_guv:
				with open(self.my_file, 'a') as thefile:
					thefile.write("%s\n" %data)
			##############################################################
			
			data_ = []
			if len(data)>=inds[-1]+1:
				for i in inds:
					if self.is_number(data[i]):
						data_.extend([float(data[i])])
						#print([format(i,'.3e') for i in data_])
						
			if len(data_)==len(inds):
				return data_
			
			
	def is_open(self):
		
		try:
			self.return_id()
			return True
		except Exception as e:
			return False
	
	def close(self):
		
		if self.testmode:
			print(''.join(["TEST MODE: ",self.my_vars[2]," port flushed and closed"]))
		elif not self.testmode:
			self.guv.close()
			print(''.join([self.my_vars[2], " port flushed and closed"]))
		
	
def main():
  
	# call the sr510 port
	guv_ = GUV(['127.0.0.1',2121,"GUV-541"],True)
	
	print(guv_.return_id())
	
	for i in range(10):
		print(guv_.return_powden())
		print(guv_.return_temp())
	
if __name__ == "__main__":
	
  main()
  


