#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""



import traceback, sys, os, sqlite3, configparser
import re, serial, time, datetime, numpy, random, yagmail, visa, scipy.io
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import pyqtgraph.exporters

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLCDNumber, QMessageBox, QGridLayout, QHeaderView,
														 QLabel, QLineEdit, QComboBox, QFrame, QTableWidget, QTableWidgetItem,
														 QVBoxLayout, QHBoxLayout, QApplication, QMenuBar, QPushButton)

import MS257, K2001A
import MS257_dialog, K2001A_dialog, Oriel_dialog, Agilent34972A_dialog, Message_dialog
import Email_settings_dialog, Send_email_dialog, Instruments_dialog, Write2file_dialog







class WorkerSignals(QObject):
	
	# Create signals to be used
	update1 = pyqtSignal(object)
	update2 = pyqtSignal(object)
	update3 = pyqtSignal(object)
	update4 = pyqtSignal(object)
	warning = pyqtSignal(object)
	
	error = pyqtSignal(tuple)
	finished = pyqtSignal()








class Email_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
	def __init__(self,*argv):
		super(Email_Worker, self).__init__()
		
		# constants	
		self.subject = argv[0].subject
		self.contents = argv[0].contents
		self.emailset_str = argv[0].settings
		self.emailrec_str = argv[0].receivers
		
		self.signals = WorkerSignals()
		
		
	@pyqtSlot()
	def run(self):
		'''
		Initialise the runner function with passed args, kwargs.
		'''
		# Retrieve args/kwargs here; and fire processing using them
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(to=self.emailrec_str, subject=self.subject, contents=self.contents)
		except Exception as e:
			self.signals.warning.emit(str(e))
			
		self.signals.finished.emit()
			
			
			
			
			
			
			
			
			
class TEST_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
	def __init__(self,*argv):
		super(TEST_Worker, self).__init__()
		
		# constants	
		self.abort_flag=False
		self.pause_flag=False
		
		self.inst_list=argv[0].inst_list
		self.unit = argv[0].unit
		
		shutter_list = argv[0].shutter_list
		self.shutter = shutter_list.get('shutter')
		self.shutdelay = shutter_list.get('shutdelay')/1000
		
		pos_list = argv[0].pos_list
		self.pos = pos_list.get('pos')
		self.posdelay = pos_list.get('posdelay')
		
		self.sssd = argv[0].sssd
		
		self.signals = WorkerSignals()
		
		
	def abort(self):
		
		self.abort_flag=True
		
		
	def pause(self):
		
		if self.pause_flag:
			self.pause_flag=False
		else:
			self.pause_flag=True
			
			
	def dateandtime(self):
		
		now = datetime.datetime.now()
		
		sm1 = now.strftime("%y%m%d %H:%M:")
		sm2 = format(float(str("%d.%d" %(now.second,now.microsecond))), '07.4f')
		
		return str("%s%s" %(sm1,sm2))
			
			
	@pyqtSlot()
	def run(self):
		'''
		Initialise the runner function with passed args, kwargs.
		'''
		# Retrieve args/kwargs here; and fire processing using them
		try:
			if self.inst_list.get('MS257_in') and self.inst_list.get('MS257_out') and self.inst_list.get('K2001A'):
				self.run_sc1()
				
			elif self.inst_list.get('MS257_in') and self.inst_list.get('MS257_out'):
				self.run_sc2()
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			pass
		finally:
			self.signals.finished.emit()  # Done
		
		
	def run_sc1(self):
		# set UNITS
		#self.ms257_in.setUNITS(self.unit.upper())
		#self.ms257_out.setUNITS(self.unit.upper())
		
		# set Keithely 2001A supply
		#self.k2001a.set_dc_voltage()
		
		print("The current monochromator position is:")
		time_start=time.time()
		
		wv_scanlist=numpy.arange(self.sssd[0],self.sssd[1]+self.sssd[2],self.sssd[2])
		dwell=self.sssd[3]
		
		for new_position in wv_scanlist:
			# abort the scan
			if self.abort_flag:
				return
			# pause the scan
			while self.pause_flag:
				time.sleep(0.1)
			
			# go to the START position
			#self.ms257_in.goToWL(new_position)
			#self.ms257_out.goToWL(new_position)
			
			step_wl=new_position
			#step_wl=self.ms257_out.getCurrentWL()
			step_wl=format(step_wl, '06.1f')
			print(step_wl, self.unit)
			
			# Set the MIRROR in the A position
			if self.pos=="A and B":
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
				
				# Set the MIRROR in the A position
				#self.oriel.goto_a()
				self.signals.update4.emit("A")
				time_start_=time.time()
				while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
					time.sleep(0.025)
					
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
						
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"A","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"A","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"A",self.shutter,time_elap,self.dateandtime()])
				
				###############################################
				
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
					
				# Set the MIRROR in the B position
				#self.oriel.goto_b()
				self.signals.update4.emit("B")
				time_start_=time.time()
				while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
					time.sleep(0.025)
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"B","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"B","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"B",self.shutter,time_elap,self.dateandtime()])
			
			# Set the MIRROR in the A position
			elif self.pos=="A":
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
				
				# Set the MIRROR in the A position
				#self.oriel.goto_a()
				self.signals.update4.emit("A")
				time_start_=time.time()
				while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
					time.sleep(0.025)
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"A","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"A","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"A",self.shutter,time_elap,self.dateandtime()])
			
			# Set the MIRROR in the B position
			elif self.pos=="B":
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
				
				# Set the MIRROR in the B position
				#self.oriel.goto_b()
				self.signals.update4.emit("B")
				time_start_=time.time()
				while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
					time.sleep(0.025)
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"B","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"B","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"B",self.shutter,time_elap,self.dateandtime()])
			
			# Ignore the MIRROR position
			elif self.pos=="None":
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
					
				self.signals.update4.emit("?")
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"?","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"?","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						X_val=format(random.random(), '07.4f')
						time.sleep(0.1)
						#X_val=self.k2001a.return_voltage()
						self.signals.update2.emit([step_wl,X_val,time_elap])
					
					self.signals.update1.emit([step_wl,X_val,"?",self.shutter,time_elap,self.dateandtime()])
					
					
					
					
					
					
	def run_sc2(self):
		# set UNITS
		#self.ms257_in.setUNITS(self.unit.upper())
		#self.ms257_out.setUNITS(self.unit.upper())
		
		print("The current monochromator position is:")
		time_start=time.time()
		
		wv_scanlist=numpy.arange(self.sssd[0],self.sssd[1]+self.sssd[2],self.sssd[2])
		dwell=self.sssd[3]
		
		for new_position in wv_scanlist:
			# abort the scan
			if self.abort_flag:
				return
			# pause the scan
			while self.pause_flag:
				time.sleep(0.1)
			
			# go to the START position
			#self.ms257_in.goToWL(new_position)
			#self.ms257_out.goToWL(new_position)
			
			step_wl=new_position
			#step_wl=self.ms257_out.getCurrentWL()
			step_wl=format(step_wl, '06.1f')
			print(step_wl, self.unit)
			
			# Set the MIRROR in the A and then B position
			if self.pos=="A and B":
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
				
				# Set the MIRROR in the A position
				#self.oriel.goto_a()
				self.signals.update4.emit("A")
				time_start_=time.time()
				while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
					time.sleep(0.025)
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"A","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"A","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"A",self.shutter,time_elap,self.dateandtime()])
				
				###############################################
				
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
					
				# Set the MIRROR in the B position
				#self.oriel.goto_b()
				self.signals.update4.emit("B")
				time_start_=time.time()
				while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
					time.sleep(0.025)
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"B","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"B","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"B",self.shutter,time_elap,self.dateandtime()])
			
			# Set the MIRROR in the A position
			elif self.pos=="A":
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
				
				# Set the MIRROR in the A position
				#self.oriel.goto_a()
				self.signals.update4.emit("A")
				time_start_=time.time()
				while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
					time.sleep(0.025)
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"A","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"A","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"A",self.shutter,time_elap,self.dateandtime()])
			
			# Set the MIRROR in the B position
			elif self.pos=="B":
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
				
				# Set the MIRROR in the B position
				#self.oriel.goto_b()
				self.signals.update4.emit("B")
				time_start_=time.time()
				while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
					time.sleep(0.025)
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"B","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"B","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"B",self.shutter,time_elap,self.dateandtime()])
			
			# Ignore the MIRROR position
			elif self.pos=="None":
				# abort the scan
				if self.abort_flag:
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
					
				self.signals.update4.emit("?")
				
				if self.shutter=="on and off":
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while DARK
					#self.ms257_in.setSHUTTER("on")
					self.signals.update3.emit("on")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"?","on",time_elap,self.dateandtime()])
					
					###############################################
					
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# record while LIGHT
					#self.ms257_in.setSHUTTER("off")
					self.signals.update3.emit("off")
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"?","off",time_elap,self.dateandtime()])
				
				else:
					# abort the scan
					if self.abort_flag:
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# record while DARK / LIGHT
					#self.ms257_in.setSHUTTER(self.shutter)
					self.signals.update3.emit(self.shutter)
					time_start_=time.time()
					while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
						time.sleep(0.025)
					
					time_start_=time.time()
					# while dwelling record voltages, then get the last recoreded voltage and pass it
					while (time.time()-time_start_)<dwell and not self.abort_flag:
						time_elap=format(time.time()-time_start, '07.2f')
						time.sleep(0.1)
						self.signals.update2.emit([step_wl,'0',time_elap])
					
					self.signals.update1.emit([step_wl,'0',"?",self.shutter,time_elap,self.dateandtime()])
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
class Run_TEST(QMainWindow):
	
	def __init__(self):
		super().__init__()
		
		self.load_()
		
		# Enable antialiasing for prettier plots		
		pg.setConfigOptions(antialias=True)
		self.initUI()
			
	def initUI(self):
		################### MENU BARS START ##################
		MyBar = QMenuBar(self)
		fileMenu = MyBar.addMenu("File")
		self.write2file = fileMenu.addAction("Write to file")
		self.write2file.triggered.connect(self.write2fileDialog)
		fileSavePlt = fileMenu.addAction("Save plots")
		fileSavePlt.triggered.connect(self.save_plots)
		fileSavePlt.setShortcut('Ctrl+P')
		fileSaveSet = fileMenu.addAction("Save settings")        
		fileSaveSet.triggered.connect(self.save_) # triggers closeEvent()
		fileSaveSet.setShortcut('Ctrl+S')
		fileClose = fileMenu.addAction("Close")        
		fileClose.triggered.connect(self.close) # triggers closeEvent()
		fileClose.setShortcut('Ctrl+X')
		
		instMenu = MyBar.addMenu("Instruments")
		self.conMode = instMenu.addAction("Connect instruments")
		self.conMode.triggered.connect(self.instrumentsDialog)
		#self.conMode.setEnabled(True)
		
		self.testMenu = instMenu.addMenu("Test instruments")
		self.testMS257 = self.testMenu.addAction("MS257")
		self.testMS257.triggered.connect(self.testMS257Dialog)
		self.testOriel = self.testMenu.addAction("Oriel stepper")
		self.testOriel.triggered.connect(self.testOrielDialog)
		self.testK2001A = self.testMenu.addAction("Keithley 2001A")
		self.testK2001A.triggered.connect(self.testK2001ADialog)
		self.testA34972A = self.testMenu.addAction("Agilent 34972A")
		self.testA34972A.triggered.connect(self.testA34972ADialog)
		
		self.emailMenu = MyBar.addMenu("E-mail")
		self.emailSet = self.emailMenu.addAction("E-mail settings")
		self.emailSet.triggered.connect(self.email_set_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)
				
		################### MENU BARS END ##################
		
		lbl1 = QLabel("Scan settings:", self)
		lbl1.setStyleSheet("color: blue")	
		self.start_lbl = QLabel(''.join(["Start[",self.unit_str,"]"]),self)
		self.stop_lbl = QLabel(''.join(["Stop[",self.unit_str,"]"]),self)
		self.step_lbl = QLabel(''.join(["Step[",self.unit_str,"]"]),self)
		dwelltime = QLabel("Dwell[s]",self)
		#ms257port = QLabel("MS257 serial port",self)
		#self.ms257portEdit = QLineEdit(str(self.ms257port_str),self)
		self.startEdit = QLineEdit(str(self.sssd[0]),self)
		self.startEdit.setFixedWidth(75)
		self.stopEdit = QLineEdit(str(self.sssd[1]),self)
		self.stopEdit.setFixedWidth(75)
		self.stepEdit = QLineEdit(str(self.sssd[2]),self)
		self.stepEdit.setFixedWidth(75)
		self.dwelltimeEdit = QLineEdit(str(self.sssd[3]),self) 
		
		##############################################
		
		lbl4 = QLabel("Write to file(s):", self)
		lbl4.setStyleSheet("color: blue")
		txtfile_lbl = QLabel("Text file:",self)
		dbfile_lbl = QLabel("SQL database file:",self)
		matfile_lbl = QLabel("Matlab file:",self)
		self.txtfile_ = QLabel("",self)
		self.dbfile_ = QLabel("",self)
		self.matfile_ = QLabel("",self)
		if self.write2txt_check:
			self.txtfile_.setText(''.join([self.write2txt_str,' (.txt)']))
			self.txtfile_.setStyleSheet("color: green")
		else:
			self.txtfile_.setText("NO text file")
			self.txtfile_.setStyleSheet("color: red")
			
		if self.write2db_check:
			self.dbfile_.setText(''.join([self.write2db_str,' (.db)']))
			self.dbfile_.setStyleSheet("color: green")
		else:
			self.dbfile_.setText("NO database file")
			self.dbfile_.setStyleSheet("color: red")
		
		if self.write2mat_check:
			self.matfile_.setText(''.join([self.write2mat_str,' (.mat)']))
			self.matfile_.setStyleSheet("color: green")
		else:
			self.matfile_.setText("NO matlab file")
			self.matfile_.setStyleSheet("color: red")
		
		##############################################
		
		lbl6 = QLabel("PLOT options:", self)
		lbl6.setStyleSheet("color: blue")
		schroll_lbl = QLabel("Schroll elapsed time ",self)
		self.combo2 = QComboBox(self)
		mylist2=["250 pts","500 pts","1000 pts","2000 pts","5000 pts"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(''.join([str(self.schroll)," pts"])))
		
		##############################################
		
		unit_lbl = QLabel("Unit",self)
		self.combo3 = QComboBox(self)
		self.mylist3=["nm","um","wn"]
		self.combo3.addItems(self.mylist3)
		self.combo3.setCurrentIndex(self.mylist3.index(self.unit_str))
		self.combo3.setFixedWidth(65)
		
		if self.unit_str=='nm':
			self.scale=1e-9
		elif self.unit_str=='um':
			self.scale=1e-6
		
		##############################################
		
		shutter_lbl = QLabel("Shutter modus",self)
		self.combo4 = QComboBox(self)
		self.mylist4=["on","off","on and off"]
		self.combo4.addItems(self.mylist4)
		self.combo4.setCurrentIndex(self.mylist4.index(self.shutter_str))
		
		##############################################
		
		self.shind_lbl = QLabel("Shutter on/off",self)
		self.shind_lbl.setFrameStyle(QFrame.Panel | QFrame.Raised)
		self.shind_lbl.setLineWidth(2)
		#self.shind_lbl.setStyleSheet("QWidget{background-color: red}")

		##############################################
		
		pos_lbl = QLabel("Position modus",self)
		self.combo5 = QComboBox(self)
		mylist5=["None","A","B","A and B"]
		self.combo5.addItems(mylist5)
		self.combo5.setCurrentIndex(mylist5.index(self.pos_str))
		
		##############################################
		
		posdelay_lbl = QLabel("Positioning delay[s]",self)
		self.combo6 = QComboBox(self)
		self.mylist6=["0","1","2","3","4","5"]
		self.combo6.addItems(self.mylist6)
		self.combo6.setCurrentIndex(self.mylist6.index(str(self.posdelay)))
		
		##############################################
		
		shutdelay_lbl = QLabel("Shutter delay[ms]",self)
		self.combo7 = QComboBox(self)
		self.mylist7=["0","200","400","600", "800","1000","1200"]
		self.combo7.addItems(self.mylist7)
		self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
		
		##############################################
		
		self.posind_lbl = QLabel("Position  ",self)
		self.posind_lbl.setFrameStyle(QFrame.Panel | QFrame.Raised)
		self.posind_lbl.setLineWidth(2)
		
		##############################################
		
		lbl5 = QLabel("RECORD data and save images:", self)
		lbl5.setStyleSheet("color: blue")
		
		#save_str = QLabel("Store settings", self)
		#self.saveButton = QPushButton("Save",self)
		#self.saveButton.setEnabled(True)
		
		run_str = QLabel("Scan and record", self)
		self.runButton = QPushButton("Scan",self)
		
		#saveplots_str = QLabel("Save plots as png", self)
		#self.saveplotsButton = QPushButton("Save plots",self)
		#self.saveplotsButton.setEnabled(True)
		'''
		elapsedtime_str = QLabel('Show voltage vs. time', self)
		self.elapsedtimeButton = QPushButton("Plot 2",self)
		self.elapsedtimeButton.setEnabled(False)
		'''
		abort_str = QLabel("Abort scan", self)
		self.abortButton = QPushButton("ABORT",self)
		self.abortButton.setEnabled(False)
		
		pause_str = QLabel("Pause scan", self)
		self.pauseButton = QPushButton("Pause",self)
		self.pauseButton.setEnabled(False)
		
		##############################################
		
		# status info which button has been pressed
		#self.status_str = QLabel("Edit settings and press SAVE!", self)
		#self.status_str.setStyleSheet("color: green")
		
		##############################################
		
		# status info which button has been pressed
		self.elapsedtime_str = QLabel("TIME trace for storing plots and data:", self)
		self.elapsedtime_str.setStyleSheet("color: blue")
		
		##############################################
		
		self.lcd = QLCDNumber(self)
		self.lcd.setStyleSheet("color: red")
		self.lcd.setFixedHeight(60)
		self.lcd.setSegmentStyle(QLCDNumber.Flat)
		self.lcd.setNumDigits(11)
		self.lcd.display(self.time_str)
			
		##############################################
		
		# create table
		self.tableWidget = self.createTable()
		self.GUVWidget = self.GUV_table()
		
		##############################################
		
		# Add all widgets
		h0 = QGridLayout()
		h0.addWidget(self.posind_lbl,0,0)
		h0.addWidget(self.shind_lbl,0,1)
		h0.addWidget(posdelay_lbl,1,0)
		h0.addWidget(shutdelay_lbl,1,1)
		h0.addWidget(self.combo6,2,0)
		h0.addWidget(self.combo7,2,1)
		
		g1_0 = QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_0.addWidget(lbl1,1,0)
		g1_2 = QGridLayout()
		g1_2.addWidget(self.start_lbl,0,0)
		g1_2.addWidget(self.stop_lbl,0,1)
		g1_2.addWidget(self.step_lbl,0,2)
		g1_2.addWidget(dwelltime,0,3)
		g1_2.addWidget(self.startEdit,1,0)
		g1_2.addWidget(self.stopEdit,1,1)
		g1_2.addWidget(self.stepEdit,1,2)
		g1_2.addWidget(self.dwelltimeEdit,1,3)
		g1_3 = QGridLayout()
		g1_3.addWidget(pos_lbl,0,0)
		g1_3.addWidget(self.combo5,1,0)
		g1_3.addWidget(shutter_lbl,0,1)
		g1_3.addWidget(self.combo4,1,1)
		g1_3.addWidget(unit_lbl,0,2)
		g1_3.addWidget(self.combo3,1,2)
		
		
		v1 = QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_2)
		v1.addLayout(g1_3)
		
		g4_0 = QGridLayout()
		g4_0.addWidget(lbl4,0,0)
		g4_1 = QGridLayout()
		g4_1.addWidget(txtfile_lbl,0,0)
		g4_1.addWidget(self.txtfile_,0,1)
		g4_1.addWidget(dbfile_lbl,1,0)
		g4_1.addWidget(self.dbfile_,1,1)
		g4_1.addWidget(matfile_lbl,2,0)
		g4_1.addWidget(self.matfile_,2,1)
		v4 = QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)
				
		g7_0 = QGridLayout()
		g7_0.addWidget(lbl6,0,0)
		g7_1 = QGridLayout()
		g7_1.addWidget(schroll_lbl,0,0)
		g7_1.addWidget(self.combo2,0,1)
		v7 = QVBoxLayout()
		v7.addLayout(g7_0)
		v7.addLayout(g7_1)
		
		g5_0 = QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		g5_1 = QGridLayout()
		g5_1.addWidget(run_str,0,0)
		g5_1.addWidget(abort_str,1,0)
		g5_1.addWidget(pause_str,2,0)
		g5_1.addWidget(self.runButton,0,1)
		g5_1.addWidget(self.abortButton,1,1)
		g5_1.addWidget(self.pauseButton,2,1)
		v5 = QVBoxLayout()
		v5.addLayout(g5_0)
		v5.addLayout(g5_1)
		
		v6 = QGridLayout()
		v6.addWidget(self.elapsedtime_str,0,0)
		v6.addWidget(self.lcd,1,0)
		
		# add all groups from v1 to v6 in one vertical group v7
		v8 = QVBoxLayout()
		v8.addLayout(v1)
		v8.addLayout(h0)
		v8.addLayout(v4)
		v8.addLayout(v7)
		v8.addLayout(v5)
		v8.addLayout(v6)
	
		# set GRAPHS and TOOLBARS to a new vertical group vcan
		self.win2 = pg.GraphicsWindow()

		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QHBoxLayout()
		hbox.addLayout(v8,1)
		hbox.addWidget(self.win2,3)
		
		vbox = QVBoxLayout()
		vbox.addLayout(hbox,3)
		vbox.addWidget(self.GUVWidget,1)
		
		hbox2 = QHBoxLayout()
		hbox2.addLayout(vbox,4)
		hbox2.addWidget(self.tableWidget,1)
		
		##############################################
		
		self.p0 = self.win2.addPlot()
		self.my_legend = self.p0.addLegend()
		self.curve1_Aon = self.p0.plot(pen='y', symbol='s', symbolPen='y', symbolBrush='g', symbolSize=6)
		self.curve1_Aoff = self.p0.plot(pen=pg.mkPen('y', style=QtCore.Qt.DashLine))
		self.curve1_Bon = self.p0.plot(pen='m', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.curve1_Boff = self.p0.plot(pen=pg.mkPen('m', style=QtCore.Qt.DashLine))
		self.curve1_Non = self.p0.plot(pen='c', symbol='s', symbolPen='c', symbolBrush='g', symbolSize=6)
		self.curve1_Noff = self.p0.plot(pen=pg.mkPen('c', style=QtCore.Qt.DashLine))
		#self.my_legend.hide()
		
		self.p0.enableAutoRange()
		self.p0.setTitle(''.join(["Voltage as function of wavelength"]))
		self.p0.setLabel('left', "Voltage", units='V', color='red')
		self.p0.setLabel('bottom', "Wavelength", units='m', color='white')
		
		self.win2.nextRow()
		
		self.p1 = self.win2.addPlot()
		self.curve2=self.p1.plot(pen='r')
		self.curve3=self.p1.plot(pen='w')
		# create plot and add it to the figure
		self.p2 = pg.ViewBox()
		self.curve4=pg.PlotCurveItem(pen='y')
		self.p2.addItem(self.curve4)
		# connect respective axes to the plot 
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Wavelength", units='m', color='yellow')
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis('right').linkToView(self.p2)
		self.p2.setXLink(self.p1)
		
		# Use automatic downsampling and clipping to reduce the drawing load
		self.p1.setDownsampling(mode='peak')
		self.p1.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		
		##############################################
		
		# send status info which button has been pressed
		#self.saveButton.clicked.connect(self.buttonClicked)
		#self.runButton.clicked.connect(self.buttonClicked)
		#self.abortButton.clicked.connect(self.buttonClicked)
		#self.saveplotsButton.clicked.connect(self.buttonClicked)
		#self.elapsedtimeButton.clicked.connect(self.buttonClicked)
		
		# reacts to choises picked in the menu
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		self.combo4.activated[str].connect(self.onActivated4)
		self.combo5.activated[str].connect(self.onActivated5)
		self.combo6.activated[str].connect(self.onActivated6)
		self.combo7.activated[str].connect(self.onActivated7)
		
		# save all paramter data in the config file
		#self.saveButton.clicked.connect(self.save_)
		#self.saveButton.clicked.connect(self.set_elapsedtime_text)
	
		# run the main script
		self.runButton.clicked.connect(self.set_run)
		
		# abort the script run
		self.abortButton.clicked.connect(self.set_abort)
		
		# pause the script run
		self.pauseButton.clicked.connect(self.set_pause)
		
		##############################################
		
		self.inst_list = {}
		self.allEditFields(False,"init")
		
		self.threadpool = QThreadPool()
		print("Multithreading in TEST_gui_v1 with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning = False
		
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.set_disconnect)
		self.timer.setSingleShot(True)
		
		##############################################
		
		#self.setGeometry(100, 100, 800, 450)
		self.setWindowTitle("Scan Control And Data Acqusition")
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		hbox2.setSizeConstraint(hbox2.SetFixedSize)
		
		w = QWidget()
		w.setLayout(hbox2)
		self.setCentralWidget(w)
		self.show()
		
		
	def set_bstyle_v1(self,button):
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(65)
		
		
	def onActivated2(self, text):
		my_string=str(text)
		self.schroll=int(my_string.split()[0])
		
		
	def onActivated3(self, text):
		self.unit_str=str(text)
		self.start_lbl.setText(''.join(["Start[",str(text),"]"]))
		self.stop_lbl.setText(''.join(["Stop[",str(text),"]"]))
		self.step_lbl.setText(''.join(["Step[",str(text),"]"]))
		
		if str(text)=='nm':
			self.scale=1e-9
		elif str(text)=='um':
			self.scale=1e-6
		
		
	def onActivated4(self, text):
		self.shutter_str=str(text)
		
		
	def onActivated5(self, text):
		self.pos_str=str(text)
		
		
	def onActivated6(self, text):
		self.posdelay=int(text)
		
		
	def onActivated7(self, text):
		self.shutdelay=int(text)
		
		
	def createTable(self):
		tableWidget = QTableWidget()
		tableWidget.setFixedWidth(260)
		
		# set row count
		#tableWidget.setRowCount(20)
		
		# set column count
		tableWidget.setColumnCount(5)
		# hide grid
		tableWidget.setShowGrid(False)
		# hide vertical header
		vh = tableWidget.verticalHeader()
		vh.setVisible(False)
		# set the font
		font = QFont("Courier New", 9)
		tableWidget.setFont(font)
		tableWidget.setStyleSheet("color: blue")
		
		# place content into individual table fields
		#tableWidget.setItem(0,0, QTableWidgetItem("abe"))
		
		tableWidget.setHorizontalHeaderLabels([''.join([" W[",self.unit_str,"] "])," U[V] "," Pos "," Shut "," T[s] "])
		
		# set horizontal header properties
		hh = tableWidget.horizontalHeader()
		for tal in range(5):
			if tal==4:
				hh.setSectionResizeMode(tal, QHeaderView.Stretch)
			else:
				hh.setSectionResizeMode(tal, QHeaderView.ResizeToContents)
		
		# set column width to fit contents
		tableWidget.resizeColumnsToContents()
		
		# enable sorting
		#tableWidget.setSortingEnabled(True)
		
		return tableWidget
	
	
	def GUV_table(self):
		
		tableWidget = QTableWidget()
 
		# set row count
		#tableWidget.setRowCount(20)
		
		# set column count
		tableWidget.setColumnCount(9)
		# hide grid
		tableWidget.setShowGrid(False)
		# hide vertical header
		vh = tableWidget.verticalHeader()
		vh.setVisible(False)
		# set the font
		font = QFont("Courier New", 9)
		tableWidget.setFont(font)
		tableWidget.setStyleSheet("color: blue")
		
		# place content into individual table fields
		#tableWidget.setItem(0,0, QTableWidgetItem("abe"))
		
		tableWidget.setHorizontalHeaderLabels([''.join([" Ch. ",str(i+1)," "]) for i in range(9)])
		
		# set horizontal header properties
		for tal in range(9):
			tableWidget.setColumnWidth(tal, 75)
        
		# set column width to fit contents
		#tableWidget.resizeColumnsToContents()
		
		# enable sorting
		#tableWidget.setSortingEnabled(True)
		
		return tableWidget
	
	
	def allEditFields(self,trueorfalse,*argv):
		
		if argv:
			if not trueorfalse and argv[0]=="init":
				self.write2file.setEnabled(True)
			else:
				self.write2file.setEnabled(trueorfalse)
		else:
			self.write2file.setEnabled(trueorfalse)
		
		if argv:
			if not trueorfalse and argv[0]=="run":
				self.emailSet.setEnabled(False)
				self.emailData.setEnabled(False)
			else:
				self.emailSet.setEnabled(True)
				self.emailData.setEnabled(True)
		else:
			self.emailSet.setEnabled(True)
			self.emailData.setEnabled(True)
		
		
		self.startEdit.setEnabled(trueorfalse)
		self.stopEdit.setEnabled(trueorfalse)
		self.stepEdit.setEnabled(trueorfalse)
		self.dwelltimeEdit.setEnabled(trueorfalse)
		self.runButton.setEnabled(trueorfalse)
		
		self.combo2.setEnabled(trueorfalse)
		self.combo3.setEnabled(trueorfalse)
		self.combo4.setEnabled(trueorfalse)
		
		if not self.inst_list.get("Oriel"):
			self.combo5.setEnabled(False)
		else:
			self.combo5.setEnabled(trueorfalse)
		
		self.combo6.setEnabled(trueorfalse)
		self.combo7.setEnabled(trueorfalse)
			
			
	def instrumentsDialog(self):
		
		self.Inst = Instruments_dialog.Instruments_dialog(self, self.inst_list, self.timer, self.config)
		self.Inst.exec()
		
		if not self.inst_list.get('Oriel'):
			self.pos_str="None"
		else:
			self.pos_str="A and B"
		
		if self.inst_list.get("MS257_in") and self.inst_list.get("MS257_out"):
			self.allEditFields(True)
		else:
			QMessageBox.warning(self, 'Message',"Input and output monochromators need to be connected for a scan!")
			self.allEditFields(False)
			
			
	def write2fileDialog(self):
		
		self.Write2file_dialog = Write2file_dialog.Write2file_dialog(self, self.config)
		self.Write2file_dialog.exec()
		
		self.load_()
		
		if self.write2txt_check:
			self.txtfile_.setText(''.join([self.write2txt_str,' (.txt)']))
			self.txtfile_.setStyleSheet("color: green")
		else:
			self.txtfile_.setText("NO text file")
			self.txtfile_.setStyleSheet("color: red")
		
		if self.write2db_check:
			self.dbfile_.setText(''.join([self.write2db_str,' (.db)']))
			self.dbfile_.setStyleSheet("color: green")
		else:
			self.dbfile_.setText("NO database file")
			self.dbfile_.setStyleSheet("color: red")
			
		if self.write2mat_check:
			self.matfile_.setText(''.join([self.write2mat_str,' (.mat)']))
			self.matfile_.setStyleSheet("color: green")
		else:
			self.matfile_.setText("NO matlab file")
			self.matfile_.setStyleSheet("color: red")
			
			
	def testMS257Dialog(self):
		
		self.MS257_dialog = MS257_dialog.MS257_dialog(self, self.config)
		self.MS257_dialog.exec()
		
		
	def testOrielDialog(self):
		
		self.Oriel_dialog = Oriel_dialog.Oriel_dialog(self, self.config)
		self.Oriel_dialog.exec()
		
		
	def testK2001ADialog(self):
		
		self.K2001A_dialog = K2001A_dialog.K2001A_dialog(self, self.config)
		self.K2001A_dialog.exec()
		
		
	def testA34972ADialog(self):
		
		self.Agilent34972A_dialog = Agilent34972A_dialog.Agilent34972A_dialog(self, self.config)
		self.Agilent34972A_dialog.exec()
		
		
	def email_data_dialog(self):
		
		self.Send_email_dialog = Send_email_dialog.Send_email_dialog(self, self.config)
		self.Send_email_dialog.exec()
		
		
	def email_set_dialog(self):
		
		self.Email_dialog = Email_settings_dialog.Email_dialog(self, self.lcd, self.config)
		self.Email_dialog.exec()
		
		
	def create_file(self,mystr):
		
		head, tail = os.path.split(mystr)
		# Check for possible name conflicts
		if tail:
			saveinfile=''.join([tail,self.time_str])
		else:
			saveinfile=''.join(["data_",self.time_str])
			
		if head:
			if not os.path.isdir(head):
				os.mkdir(head)
			saveinfolder=''.join([head,"/"])
		else:
			saveinfolder=""
			
		return ''.join([saveinfolder,saveinfile])
	
	
	def prepare_file(self):
		
		# Save to a textfile
		if self.write2txt_check:
			self.textfile = ''.join([self.create_file(self.write2txt_str),".txt"])
			with open(self.textfile, 'w') as thefile:
				thefile.write("Your edit line - keep this line!\n")
				thefile.write(''.join(["Wl[",self.unit_str,"]\tVolt.[V]\tPos.\tShut.\tTimetr.[s]\tAbs date and time\n"]))
		
		# Save to a MATLAB datafile
		if self.write2mat_check:
			self.matfile = ''.join([self.create_file(self.write2mat_str),".mat"])
		
		# First delete the database file if it exists
		if self.write2db_check:
			self.dbfile = ''.join([self.create_file(self.write2db_str),".db"])
			try:
				os.remove(self.dbfile)
			except OSError:
				pass
			
			# Then create it again for new inputs
			self.conn = sqlite3.connect(self.dbfile)
			self.db = self.conn.cursor()
			self.db.execute('''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, timetrace real, absolutetime text)''')
		
		
	def set_run(self):
		
		try:
			start_ = float(self.startEdit.text()) 
			stop = float(self.stopEdit.text()) 
			step = float(self.stepEdit.text()) 
			dwell = float(self.dwelltimeEdit.text())
		except Exception as e:
			QMessageBox.warning(self, 'Message',"Scan parameters must be real numbers. Empty fields are not allowed!")
			return
		
		if start_<250 or start_>2500:
			QMessageBox.warning(self, 'Message',"Minimum start wavelength is in the range from 250 nm to 2500 nm")
			return
		if stop<250 or stop>2500:
			QMessageBox.warning(self, 'Message',"Minimum stop wavelength is in the range from 250 nm to 2500 nm")
			return
		if start_>=stop:
			QMessageBox.warning(self, 'Message',"Stop wavelength must be larger than the start wavelength")
			return
		if step<0 or step>100:
			QMessageBox.warning(self, 'Message',"Minimum step is in the range from 0 units to 100 units")
			return
		if dwell<0.5 or dwell>10:
			QMessageBox.warning(self, 'Message',"Monochromator dwell time is in the range from 0.5 sec to 10 sec")
			return
		
		self.prepare_file()
		self.timer.stop()
		self.clear_vars_graphs()

		if self.pos_str=="A and B":
			if self.shutter_str=="on and off":
				self.my_legend.addItem(self.curve1_Aon, name='A - ON')
				self.my_legend.addItem(self.curve1_Aoff, name='A - OFF')
				self.my_legend.addItem(self.curve1_Bon, name='B - ON')
				self.my_legend.addItem(self.curve1_Boff, name='B - OFF')
			elif self.shutter_str=="on":
				self.shutdelay=0
				self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
				self.my_legend.addItem(self.curve1_Aon, name='A - ON')
				self.my_legend.addItem(self.curve1_Bon, name='B - ON')
			elif self.shutter_str=="off":
				self.shutdelay=0
				self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
				self.my_legend.addItem(self.curve1_Aoff, name='A - OFF')
				self.my_legend.addItem(self.curve1_Boff, name='B - OFF')
				
		elif self.pos_str=="A":
			self.posdelay=0
			self.combo6.setCurrentIndex(self.mylist6.index(str(self.posdelay)))
			if self.shutter_str=="on and off":
				self.my_legend.addItem(self.curve1_Aon, name='A - ON')
				self.my_legend.addItem(self.curve1_Aoff, name='A - OFF')
			elif self.shutter_str=="on":
				self.shutdelay=0
				self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
				self.my_legend.addItem(self.curve1_Aon, name='A - ON')
			elif self.shutter_str=="off":
				self.shutdelay=0
				self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
				self.my_legend.addItem(self.curve1_Aoff, name='A - OFF')
				
		elif self.pos_str=="B":
			self.posdelay=0
			self.combo6.setCurrentIndex(self.mylist6.index(str(self.posdelay)))
			if self.shutter_str=="on and off":
				self.my_legend.addItem(self.curve1_Bon, name='B - ON')
				self.my_legend.addItem(self.curve1_Boff, name='B - OFF')
			elif self.shutter_str=="on":
				self.shutdelay=0
				self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
				self.my_legend.addItem(self.curve1_Bon, name='B - ON')
			elif self.shutter_str=="off":
				self.shutdelay=0
				self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
				self.my_legend.addItem(self.curve1_Boff, name='B - OFF')
				
		elif self.pos_str=="None":
			self.posdelay=0
			self.combo6.setCurrentIndex(self.mylist6.index(str(self.posdelay)))
			if self.shutter_str=="on and off":
				self.my_legend.addItem(self.curve1_Non, name='? - ON')
				self.my_legend.addItem(self.curve1_Noff, name='? - OFF')
			elif self.shutter_str=="on":
				self.shutdelay=0
				self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
				self.my_legend.addItem(self.curve1_Non, name='? - ON')
			elif self.shutter_str=="off":
				self.shutdelay=0
				self.combo7.setCurrentIndex(self.mylist7.index(str(self.shutdelay)))
				self.my_legend.addItem(self.curve1_Noff, name='? - OFF')
				
		#self.my_legend.show()
		
		self.allEditFields(False,"run")
		self.conMode.setEnabled(False)
		self.testMenu.setEnabled(False)
		self.abortButton.setEnabled(True)
		self.pauseButton.setEnabled(True)
		self.runButton.setText("Scaning...")
		self.isRunning = True
		
		shutter_list={'shutter':self.shutter_str,'shutdelay':self.shutdelay}
		pos_list={'pos':self.pos_str,'posdelay':self.posdelay}
		
		self.sssd = [start_, stop, step, dwell]
		obj = type('setscan_obj',(object,),{'inst_list':self.inst_list, 'unit':self.unit_str, 'shutter_list':shutter_list, 'pos_list':pos_list, 'sssd':self.sssd})
		self.worker=TEST_Worker(obj)
		
		self.worker.signals.update1.connect(self.update1)
		self.worker.signals.update2.connect(self.update2)
		self.worker.signals.update3.connect(self.update3)
		self.worker.signals.update4.connect(self.update4)
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
		
		
	def update1(self,pyqt_object):
		
		new_position, all_data, pos, shutter, timelist, dateandtime = pyqt_object
		
		if shutter=="on":
			shut_bin=1
		elif shutter=="off":
			shut_bin=0
		
		self.new_position_.extend([new_position])
		self.all_data_.extend([all_data])
		self.pos_.extend([pos])
		self.shutter_.extend([shutter])
		self.timelist_.extend([timelist])
		self.dateandtime_.extend([dateandtime])
		
		if self.write2db_check:
			# Save to a database file
			'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, timetrace real, absolutetime text)'''
			self.db.execute(''.join(["INSERT INTO spectra VALUES (",new_position,",", all_data, ",'", pos,"',", str(shut_bin), ",", timelist, ",'", dateandtime, "')"]))
			# Save (commit) the changes
			self.conn.commit()
			
		#################################################
		
		if self.write2mat_check:
			# save to a MATLAB file
			matdata={}
			matdata['wavelength']=self.new_position_
			matdata['voltage']=self.all_data_
			matdata['position']=self.pos_
			matdata['shutter']=self.shutter_
			matdata['timetrace']=self.timelist_
			matdata['absolutetime']=self.dateandtime_
			
			scipy.io.savemat(self.matfile, matdata)
			#print(scipy.io.loadmat(self.matfile).keys()) 
			#b = scipy.io.loadmat(self.matfile)
			#print(b['wavelength'])
		
		#################################################
		
		if self.write2txt_check:
			# Save to a readable textfile
			with open(self.textfile, 'a') as thefile:
				thefile.write("%s " %new_position)
				thefile.write("\t%s" %all_data)
				thefile.write("\t\t%s" %pos)
				thefile.write("\t%s" %shut_bin)
				thefile.write("\t%s" %timelist)
				thefile.write("\t\t%s\n" %dateandtime)
			
		#################################################
		
		self.tal+=1
		
		# set row height
		self.tableWidget.setRowCount(self.tal+1)
		self.tableWidget.setRowHeight(self.tal, 12)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem(str(float(new_position))) )
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem(str(float(all_data))) )
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem(pos) )
		self.tableWidget.setItem(self.tal, 3, QTableWidgetItem(shutter) )
		self.tableWidget.setItem(self.tal, 4, QTableWidgetItem(str(float(timelist))) )
		
		# for the plots
		self.volt_ends.extend([ float(all_data) ])
		self.time_ends.extend([ float(timelist) ])
		
		self.curve3.setData(self.time_ends, self.volt_ends)
		
		if pos=="A":
			if shutter=="on":
				self.wl_ends_Aon.extend([ self.scale*float(new_position) ])
				self.volt_ends_Aon.extend([ float(all_data) ])
				self.curve1_Aon.setData(self.wl_ends_Aon, self.volt_ends_Aon)
			elif shutter=="off":
				self.wl_ends_Aoff.extend([ self.scale*float(new_position) ])
				self.volt_ends_Aoff.extend([ float(all_data) ])
				self.curve1_Aoff.setData(self.wl_ends_Aoff, self.volt_ends_Aoff)
		elif pos=="B":
			if shutter=="on":
				self.wl_ends_Bon.extend([ self.scale*float(new_position) ])
				self.volt_ends_Bon.extend([ float(all_data) ])
				self.curve1_Bon.setData(self.wl_ends_Bon, self.volt_ends_Bon)
			elif shutter=="off":
				self.wl_ends_Boff.extend([ self.scale*float(new_position) ])
				self.volt_ends_Boff.extend([ float(all_data) ])
				self.curve1_Boff.setData(self.wl_ends_Boff, self.volt_ends_Boff)
		elif pos=="?":
			if shutter=="on":
				self.wl_ends_Non.extend([ self.scale*float(new_position) ])
				self.volt_ends_Non.extend([ float(all_data) ])
				self.curve1_Non.setData(self.wl_ends_Non, self.volt_ends_Non)
			elif shutter=="off":
				self.wl_ends_Noff.extend([ self.scale*float(new_position) ])
				self.volt_ends_Noff.extend([ float(all_data) ])
				self.curve1_Noff.setData(self.wl_ends_Noff, self.volt_ends_Noff)
		
		
	def update2(self,pyqt_object):
		all_positions,all_data,timelist = pyqt_object
		
		self.all_wl_tr.extend([ self.scale*float(all_positions) ])
		#self.all_volts_tr.extend([ all_data ])
		#self.all_time_tr.extend([ timelist ])
		
		if len(self.all_wl_tr)>self.schroll:
			self.plot_wl_tr[:-1] = self.plot_wl_tr[1:]  # shift data in the array one sample left
			self.plot_wl_tr[-1] = self.scale*float(all_positions)
			self.plot_volts_tr[:-1] = self.plot_volts_tr[1:]  # shift data in the array one sample left
			self.plot_volts_tr[-1] = float(all_data)
			self.plot_time_tr[:-1] = self.plot_time_tr[1:]  # shift data in the array one sample left
			self.plot_time_tr[-1] = float(timelist)
		else:
			self.plot_wl_tr.extend([ self.scale*float(all_positions) ])
			self.plot_volts_tr.extend([ float(all_data) ])
			self.plot_time_tr.extend([ float(timelist) ])

		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())
			
			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p1.vb.sigResized.connect(updateViews)
		
		self.curve2.setData(self.plot_time_tr, self.plot_volts_tr)
		self.curve4.setData(self.plot_time_tr, self.plot_wl_tr)
		
		if len(self.time_ends)>0:
			if self.plot_time_tr[0]>self.time_ends[0]:
				self.volt_ends = self.volt_ends[1:]  # shift data in the array one sample left
				self.time_ends = self.time_ends[1:]  # shift data in the array one sample left
				
				
	def update3(self,onoff):
		
		self.shind_lbl.setText(''.join(["Shutter ", onoff.upper()]))
		if onoff=="on":
			self.shind_lbl.setStyleSheet("QWidget{background-color: green}")
		elif onoff=="off":
			self.shind_lbl.setStyleSheet("QWidget{background-color: red}")
			
			
	def update4(self,aorb):
		
		self.posind_lbl.setText(''.join(["Position ", aorb]))
		if aorb=="A":
			self.posind_lbl.setStyleSheet("QWidget{background-color: yellow}")
		elif aorb=="B":
			self.posind_lbl.setStyleSheet("QWidget{background-color: magenta}")
		elif aorb=="?":
			self.posind_lbl.setStyleSheet("QWidget{background-color: cyan}")
			
			
	def make_3Dplot(self):
		
		new_position_ = [float(i) for i in self.new_position_]
		timelist_ = [float(i) for i in self.timelist_]
		all_data_ = [float(i) for i in self.all_data_]
		
		fig=plt.figure(figsize=(8,6))
		ax= fig.add_subplot(111, projection='3d')
		
		ax.plot(new_position_, timelist_, all_data_, linewidth=1)
		#ax=fig.gca(projection='2d')
		ax.set_xlabel(''.join(['lambda[',self.unit_str,']']))
		ax.set_ylabel('Time[s]')
		ax.set_zlabel('Voltage[V]')
		
		plt.show()
		#fig.savefig(''.join(['plot_',self.time_str,'_3D.png']))
		
		
	def set_disconnect(self):
		
		if self.inst_list.get("MS257_in"):
			if self.inst_list.get("MS257_in").is_open():
				self.inst_list.get("MS257_in").close()
				
		if self.inst_list.get("MS257_out"):
			if self.inst_list.get("MS257_out").is_open():
				self.inst_list.get("MS257_out").close()
						
		if self.inst_list.get("Oriel"):
			if self.inst_list.get("Oriel").is_open():
				self.inst_list.get("Oriel").close()
				
		self.allEditFields(False)
		self.conMode.setEnabled(True)
		self.testMenu.setEnabled(True)
		
		
	def set_abort(self):
		
		self.worker.abort()
		
		
	def set_pause(self):
		
		sender=self.sender()
		self.worker.pause()
		self.allEditFields(False,"run")
		
		if sender.text()=="Continue":
			self.pauseButton.setText("Pause")
			self.runButton.setText("Scaning...")
			self.abortButton.setEnabled(True)
		elif sender.text()=="Pause":
			self.pauseButton.setText("Continue")
			self.runButton.setText("Paused")
			self.abortButton.setEnabled(False)
			
			
	def finished(self):
		
		if self.write2db_check:
			for row in self.db.execute('SELECT voltage, timetrace FROM spectra WHERE timetrace>? ORDER BY timetrace DESC', (10,)):
				print(row)
			print('\r')
			
			for row in self.db.execute('SELECT shutter, voltage, timetrace, absolutetime FROM spectra WHERE timetrace BETWEEN ? AND ? AND shutter=? ORDER BY timetrace DESC', (5,15,0)):
				print(row)
			print('\r')
			
			lis=[1450.0,1,'B']
			for row in self.db.execute('SELECT * FROM spectra WHERE wavelength=? AND shutter=? AND position=?',(lis[0],lis[1],lis[2])):
				print(row)
			
			# We can also close the connection if we are done with it.
			# Just be sure any changes have been committed or they will be lost.
			self.conn.close()
		
		self.load_()
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()
		
		#self.make_3Dplot()
		
		self.isRunning=False
		self.abortButton.setEnabled(False)
		self.pauseButton.setEnabled(False)
		self.conMode.setEnabled(True)
		self.testMenu.setEnabled(True)
		
		self.allEditFields(True)
		self.runButton.setText("Scan")
		
		self.timer.start(1000*60*5)
		
		
	def warning(self, mystr):
		
		QMessageBox.warning(self, 'Message', mystr)
	
	
	def send_notif(self):
		
		self.md1 = Message_dialog.Message_dialog(self, "Sending notification", "...please wait...")
		
		contents=["The scan is done. Please visit the experiment site and make sure that all light sources are switched off."]
		subject="The scan is done"
		
		obj = type('obj',(object,),{'subject':subject, 'contents':contents, 'settings':self.emailset_str, 'receivers':self.emailrec_str})
		worker=Email_Worker(obj)
		
		worker.signals.warning.connect(self.warning)
		worker.signals.finished.connect(self.finished1)
		
		# Execute
		self.threadpool.start(worker)
		
	def finished1(self):
		
		self.md1.close_()
		
		
	def send_data(self):
		
		self.md2 = Message_dialog.Message_dialog(self, "Sending data", "...please wait...")
		
		contents=["The scan is  done and the logged data is attached to this email. Please visit the experiment site and make sure that all light sources are switched off."]
		subject="The scan data from the latest scan!"
		
		if self.write2txt_check:
			contents.extend([self.textfile])
		if self.write2db_check:
			contents.extend([self.dbfile])
		if self.write2mat_check:
			contents.extend([self.matfile])
			
		obj = type('obj',(object,),{'subject':subject, 'contents':contents, 'settings':self.emailset_str, 'receivers':self.emailrec_str})
		worker=Email_Worker(obj)
		
		worker.signals.warning.connect(self.warning)
		worker.signals.finished.connect(self.finished2)
		
		# Execute
		self.threadpool.start(worker)
		
	def finished2(self):
		
		self.md2.close_()
		
		
	def clear_vars_graphs(self):
		# PLOT 2 initial canvas settings
		self.tal=-1
		self.all_wl_tr=[]
		#self.all_volts_tr=[]
		#self.all_time_tr=[]
		self.plot_wl_tr=[]
		self.plot_volts_tr=[]
		self.plot_time_tr=[]
		self.volt_ends=[]
		self.time_ends=[]
		self.wl_ends_Aon=[]
		self.wl_ends_Bon=[]
		self.wl_ends_Non=[]
		self.wl_ends_Aoff=[]
		self.wl_ends_Boff=[]
		self.wl_ends_Noff=[]
		self.volt_ends_Aon=[]
		self.volt_ends_Bon=[]
		self.volt_ends_Non=[]
		self.volt_ends_Aoff=[]
		self.volt_ends_Boff=[]
		self.volt_ends_Noff=[]
		self.new_position_=[]
		self.all_data_=[]
		self.pos_=[]
		self.shutter_=[]
		self.timelist_=[]
		self.dateandtime_=[]
		self.tableWidget.clearContents()
		
		self.my_legend.removeItem('A - ON')
		self.my_legend.removeItem('A - OFF')
		self.my_legend.removeItem('B - ON')
		self.my_legend.removeItem('B - OFF')
		self.my_legend.removeItem('? - ON')
		self.my_legend.removeItem('? - OFF')

		self.curve1_Aon.setData(self.wl_ends_Aon, self.volt_ends_Aon)
		self.curve1_Aoff.setData(self.wl_ends_Aoff, self.volt_ends_Aoff)
		self.curve1_Bon.setData(self.wl_ends_Bon, self.volt_ends_Bon)
		self.curve1_Boff.setData(self.wl_ends_Boff, self.volt_ends_Boff)
		self.curve1_Non.setData(self.wl_ends_Non, self.volt_ends_Non)
		self.curve1_Noff.setData(self.wl_ends_Noff, self.volt_ends_Noff)
		
		self.curve2.setData(self.plot_time_tr, self.plot_volts_tr)
		self.curve3.setData(self.time_ends, self.volt_ends)
		self.curve4.setData(self.plot_time_tr, self.plot_wl_tr)
		
		
		self.p1.enableAutoRange()
		# Labels and titels are placed here since they change dynamically
		self.p1.setTitle(''.join(["Voltage and wavelength as function of time"]))
		self.p1.setLabel('left', "Voltage", units='V', color='red')
		self.p1.setLabel('bottom', "Elapsed time", units='s', color='white')
		
		
	def load_(self):
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
			
			self.schroll = int(self.config.get('DEFAULT','schroll'))
			self.posdelay = int(self.config.get('DEFAULT','posdelay'))
			self.shutdelay = int(self.config.get('DEFAULT','shutdelay'))
			self.sssd = self.config.get('DEFAULT','sssd').strip().split(',')
			self.unit_str = self.config.get('DEFAULT','unit')
			self.shutter_str = self.config.get('DEFAULT','shutter')
			self.write2txt_str=self.config.get('DEFAULT','write2txt').strip().split(',')[0]
			self.write2txt_check=self.bool_(self.config.get('DEFAULT','write2txt').strip().split(',')[1])
			self.write2db_str=self.config.get('DEFAULT','write2db').strip().split(',')[0]
			self.write2db_check=self.bool_(self.config.get('DEFAULT','write2db').strip().split(',')[1])
			self.write2mat_str=self.config.get('DEFAULT','write2mat').strip().split(',')[0]
			self.write2mat_check=self.bool_(self.config.get('DEFAULT','write2mat').strip().split(',')[1])
			self.time_str = self.config.get('DEFAULT','timetrace')
			self.pos_str = self.config.get('DEFAULT','pos')
			
			
			self.ms257inport_str=self.config.get('DEFAULT','ms257inport').strip().split(',')[0]
			self.ms257inport_check=self.bool_(self.config.get('DEFAULT','ms257inport').strip().split(',')[1])
			self.ms257outport_str=self.config.get('DEFAULT','ms257outport').strip().split(',')[0]
			self.ms257outport_check=self.bool_(self.config.get('DEFAULT','ms257outport').strip().split(',')[1])
			self.k2001aport_str=self.config.get('DEFAULT','k2001aport').strip().split(',')[0]
			self.k2001aport_check=self.bool_(self.config.get('DEFAULT','k2001aport').strip().split(',')[1])
			self.a34972aport_str=self.config.get('DEFAULT','a34972aport').strip().split(',')[0]
			self.a34972aport_check=self.bool_(self.config.get('DEFAULT','a34972aport').strip().split(',')[1])
			self.orielport_str=self.config.get('DEFAULT','orielport').strip().split(',')[0]
			self.orielport_check=self.bool_(self.config.get('DEFAULT','orielport').strip().split(',')[1])
			
			
			self.emailrec_str = self.config.get('DEFAULT','emailrec').strip().split(',')
			self.emailset_str = self.config.get('DEFAULT','emailset').strip().split(',')
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			raise
		
		
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
		
	def save_(self):
		self.time_str=time.strftime("%y%m%d-%H%M")
		self.lcd.display(self.time_str)
		
		self.config.set('DEFAULT','schroll',str(self.schroll))
		self.config.set('DEFAULT','posdelay',str(self.posdelay))
		self.config.set('DEFAULT','shutdelay',str(self.shutdelay))
		self.config.set('DEFAULT','sssd',','.join([str(self.startEdit.text()),str(self.stopEdit.text()),str(self.stepEdit.text()),str(self.dwelltimeEdit.text())]))
		self.config.set('DEFAULT','unit',self.unit_str)
		self.config.set('DEFAULT','shutter',self.shutter_str)
		self.config.set('DEFAULT','timetrace',self.time_str)
		self.config.set('DEFAULT','pos',self.pos_str)

		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
			
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message', "Quit now? Changes will not be saved!", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			
			if self.inst_list.get("MS257_in"):
				if not hasattr(self, 'worker'):
					if self.inst_list.get("MS257_in").is_open():
						self.inst_list.get("MS257_in").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, 'Message', "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("MS257_in").is_open():
							self.inst_list.get("MS257_in").close()
							
			if self.inst_list.get("MS257_out"):
				if not hasattr(self, 'worker'):
					if self.inst_list.get("MS257_out").is_open():
						self.inst_list.get("MS257_out").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, 'Message', "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("MS257_out").is_open():
							self.inst_list.get("MS257_out").close()
							
			if self.inst_list.get("Oriel"):
				if not hasattr(self, 'worker'):
					if self.inst_list.get("Oriel").is_open():
						self.inst_list.get("Oriel").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, 'Message', "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("Oriel").is_open():
							self.inst_list.get("Oriel").close()
							
			if self.inst_list.get("K2001A"):
				if hasattr(self, 'worker'):
					if self.isRunning:
						QMessageBox.warning(self, 'Message', "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					
			if self.inst_list.get("Agilent34972A"):
				if hasattr(self, 'worker'):
					if self.isRunning:
						QMessageBox.warning(self, 'Message', "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					
			if hasattr(self, 'timer'):
				if self.timer.isActive():
					self.timer.stop()
			
			event.accept()
		else:
		  event.ignore() 
		  
		  
	def save_plots(self):
		
		if self.write2txt_check:
			save_to_file=''.join([self.create_file(self.write2txt_str),'.png'])
		elif self.write2db_check:
			save_to_file=''.join([self.create_file(self.write2db_str),'.png'])	
		elif self.write2mat_check:
			save_to_file=''.join([self.create_file(self.write2mat_str),'.png'])	
		else:
			save_to_file=''.join([self.create_file('data_plot_'),'.png'])	
			
		# create an exporter instance, as an argument give it
		# the item you wish to export
		
		exporter = pg.exporters.ImageExporter(self.p0)
		# Correction of the BUG in ImageExporter 
		# https://github.com/pyqtgraph/pyqtgraph/issues/538
		#I use the following contruct to circumvent the problem:
		exporter.params.param('width').setValue(1920, blockSignal=exporter.widthChanged)
		exporter.params.param('height').setValue(1080, blockSignal=exporter.heightChanged)
		#This way I don't have to modify internal code. Beware, if you set the values to the default values (640, 480) the variables will not update their type to int!

		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		exporter.export(save_to_file)
		
		
#########################################
#########################################
#########################################
	
	
def main():
	
	app = QApplication(sys.argv)
	ex = Run_TEST()
	#sys.exit(app.exec())

	# avoid message 'Segmentation fault (core dumped)' with app.deleteLater()
	app.exec()
	app.deleteLater()
	sys.exit()
	
	
if __name__ == '__main__':
		
	main()
	
	
