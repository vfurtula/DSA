# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 19:40:35 2018

@author: Vedran Furtula
"""

import sys, serial, argparse, time, re, socket, random
from random import uniform
import matplotlib.pyplot as plt

class GUV:
	
	def __init__(self,my_vars,testmode):
		
		self.my_vars=my_vars
		TCP_IP = self.my_vars[0]
		TCP_PORT = self.my_vars[1]
		
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
			inds=6
		elif self.my_vars[2]=="GUV-2511":
			inds=9
		elif self.my_vars[2]=="GUV-3511":
			inds=35
		else:
			return None
		
		
		if self.testmode:
			data = [random.uniform(35,45) for i in range(len(inds))]
			time.sleep(0.1)
			return data
		elif not self.testmode:
			self.guv.send("D".encode())
			data = self.guv.recv(1024)
			while len(data.decode().strip().split(','))<2:
				self.guv.send("D".encode())
				data = self.guv.recv(1024)
			
			data = data.decode().strip().split(',')[inds]
			if self.is_number(data):
				return data
	
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
			
		#data = ','.join([str(uniform(0,1)) for i in range(20)])
		if self.testmode:
			data_ = [random.uniform(-1,20) for i in range(len(inds))]
			time.sleep(0.1)
			return data_
		
		elif not self.testmode:
			self.guv.send("D".encode())
			data = self.guv.recv(1024)
			while len(data.decode().strip().split(','))<2:
				self.guv.send("D".encode())
				data = self.guv.recv(1024)
		
			data_=[]
			for i in inds:
				val = data.decode().strip().split(',')[i]
				if self.is_number(val):
					data_.extend([float(val)])
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
  


