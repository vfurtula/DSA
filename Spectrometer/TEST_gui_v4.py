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
import MS257_dialog, K2001A_dialog, Oriel_dialog, Agilent34972A_dialog, GUV_dialog, Message_dialog
import Email_settings_dialog, Send_email_dialog, Instruments_dialog, Write2file_dialog







class WorkerSignals(QObject):
	
	# Create signals to be used
	
	update_all_k2001a = pyqtSignal(object)
	update_all_a34972a = pyqtSignal(object)
	update_all_guv = pyqtSignal(object)
	
	update_end_k2001a = pyqtSignal(object)
	update_end_a34972a = pyqtSignal(object)
	update_end_guv = pyqtSignal(object)
	
	update_wl_time = pyqtSignal(object)
	
	update_oriel = pyqtSignal(object)
	update_shutter = pyqtSignal(object)
	
	update_ms257_in = pyqtSignal(object)
	update_ms257_out = pyqtSignal(object)
	
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
		self.shutset = shutter_list.get('shutset')
		self.shutdelay = shutter_list.get('shutdelay')/1000
		
		pos_list = argv[0].pos_list
		self.pos = pos_list.get('posset')
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
			self.run_sc()
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			pass
		finally:
			self.signals.finished.emit()  # Done
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
	def run_sc(self):
		# set UNITS
		if self.inst_list.get('MS257_in'):
			self.inst_list.get('MS257_in').setUNITS(self.unit.upper())
		if self.inst_list.get('MS257_out'):
			self.inst_list.get('MS257_out').setUNITS(self.unit.upper())
		
		# set Keithely 2001A supply
		# set Agilent 34972A supply
		if self.inst_list.get('K2001A'):
			self.inst_list.get('K2001A').set_dc_voltage()
		if self.inst_list.get('Agilent34972A'):
			self.inst_list.get('Agilent34972A').set_dc_voltage()
		if self.inst_list.get('GUV'):
			self.inst_list.get('GUV').set_dc_voltage()
			
		print("The current monochromator position is:")
		time_start=time.time()
		
		for i,j,k,l in zip(self.sssd[0],self.sssd[1],self.sssd[2],self.sssd[3]):
			wv_scanlist=numpy.arange(i,j+k,k)
			dwell=l
			
			for new_position in wv_scanlist:
				# abort the scan
				if self.abort_flag:
					if self.inst_list.get('MS257_in'):
						self.inst_list.get('MS257_in').setSHUTTER("on")
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
				
				# go to the START position
				if self.inst_list.get('MS257_in'):
					self.inst_list.get('MS257_in').goToWL(new_position)
				if self.inst_list.get('MS257_out'):
					self.inst_list.get('MS257_out').goToWL(new_position)
				
				if self.inst_list.get('MS257_in'):
					ms257_in=self.inst_list.get('MS257_in').getCurrentWL()
					ms257_in=format(ms257_in, '.6e')
				else:
					ms257_in=0
					
				if self.inst_list.get('MS257_out'):
					ms257_out=self.inst_list.get('MS257_out').getCurrentWL()
					ms257_out=format(ms257_out, '.6e')
				else:
					ms257_out=0
				
				step_wl=new_position*1e-9
				print(format(float(step_wl)*1e9, '.2f'), 'nm')
				
				# Set the MIRROR in the A position
				if self.pos=="A and B":
					# abort the scan
					if self.abort_flag:
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("on")
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# Set the MIRROR in the A position
					if self.inst_list.get('Oriel'):
						self.inst_list.get('Oriel').goto_a()
						self.signals.update_oriel.emit("A")
						
					time_start_=time.time()
					while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
						time.sleep(0.025)
						
					if self.shutset=="on and off":
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("on")
							self.signals.update_shutter.emit("on")
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
							
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
						
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while LIGHT
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("off")
							self.signals.update_shutter.emit("off")
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
					else:
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK / LIGHT
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER(self.shutset)
							self.signals.update_shutter.emit(self.shutset)
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
					
					# abort the scan
					if self.abort_flag:
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("on")
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
						
					# Set the MIRROR in the B position
					if self.inst_list.get('Oriel'):
						self.inst_list.get('Oriel').goto_b()
						self.signals.update_oriel.emit("B")
						
					time_start_=time.time()
					while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
						time.sleep(0.025)
					
					if self.shutset=="on and off":
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("on")
							self.signals.update_shutter.emit("on")
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
						
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while LIGHT
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("off")
							self.signals.update_shutter.emit("off")
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
					else:
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK / LIGHT
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER(self.shutset)
							self.signals.update_shutter.emit(self.shutset)
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
				
				# Set the MIRROR in the A position
				elif self.pos=="A":
					# abort the scan
					if self.abort_flag:
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("on")
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# Set the MIRROR in the A position
					if self.inst_list.get('Oriel'):
						self.inst_list.get('Oriel').goto_a()
						self.signals.update_oriel.emit("A")
						
					time_start_=time.time()
					while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
						time.sleep(0.025)
					
					if self.shutset=="on and off":
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("on")
							self.signals.update_shutter.emit("on")
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
						
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
							
						# record while LIGHT
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("off")
							self.signals.update_shutter.emit("off")
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
					else:
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK / LIGHT
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER(self.shutset)
							self.signals.update_shutter.emit(self.shutset)
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
				
				# Set the MIRROR in the B position
				elif self.pos=="B":
					# abort the scan
					if self.abort_flag:
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("on")
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					# Set the MIRROR in the B position
					if self.inst_list.get('Oriel'):
						self.inst_list.get('Oriel').goto_b()
						self.signals.update_oriel.emit("B")
						
					time_start_=time.time()
					while (time.time()-time_start_)<self.posdelay and not self.abort_flag:
						time.sleep(0.025)
					
					if self.shutset=="on and off":
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
							
						# record while DARK
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("on")
							self.signals.update_shutter.emit("on")
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
						
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
							
						# record while LIGHT
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER("off")
							self.signals.update_shutter.emit("off")
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
					else:
						# abort the scan
						if self.abort_flag:
							if self.inst_list.get('MS257_in'):
								self.inst_list.get('MS257_in').setSHUTTER("on")
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK / LIGHT
						if self.inst_list.get('MS257_in'):
							self.inst_list.get('MS257_in').setSHUTTER(self.shutset)
							self.signals.update_shutter.emit(self.shutset)
							
						time_start_=time.time()
						while (time.time()-time_start_)<self.shutdelay and not self.abort_flag:
							time.sleep(0.025)
						
						time_start_=time.time()
						# while dwelling record voltages, then get the last recoreded voltage and pass it
						while (time.time()-time_start_)<dwell and not self.abort_flag:
							time_elap=format(time.time()-time_start, '07.2f')
							#X_val=format(random.random(), '07.4f')
							#time.sleep(0.1)
							if self.inst_list.get('K2001A'):
								V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
								self.signals.update_all_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
							if self.inst_list.get('Agilent34972A'):
								V_a34972a=format(self.inst_list.get('Agilent34972A').return_voltage(),'.6e')
								self.signals.update_all_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
							if self.inst_list.get('GUV'):
								V_guv=[float(j) for j in [format(i,'.6e') for i in self.inst_list.get('GUV').return_voltage()]]
								self.signals.update_all_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
								self.signals.update_wl_time.emit([ms257_in,ms257_out,step_wl,time_elap,self.dateandtime()])
								
						if 'V_k2001a' in locals():
							self.signals.update_end_k2001a.emit([ms257_in,ms257_out,step_wl,V_k2001a,time_elap,self.dateandtime()])
						if 'V_a34972a' in locals():
							self.signals.update_end_a34972a.emit([ms257_in,ms257_out,step_wl,V_a34972a,time_elap,self.dateandtime()])
						if 'V_guv' in locals():
							self.signals.update_end_guv.emit([ms257_in,ms257_out,step_wl,V_guv,time_elap,self.dateandtime()])
							
						###############################################
				
		if self.inst_list.get('MS257_in'):
			self.inst_list.get('MS257_in').setSHUTTER("on")
		
		
		
		
		
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
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
		self.conMode = instMenu.addAction("Load instrument(s)")
		self.conMode.triggered.connect(self.instrumentsDialog)
		
		self.testMenu = instMenu.addMenu("Test instruments")
		self.testMS257 = self.testMenu.addAction("MS257")
		self.testMS257.triggered.connect(self.testMS257Dialog)
		self.testOriel = self.testMenu.addAction("Oriel stepper")
		self.testOriel.triggered.connect(self.testOrielDialog)
		self.testK2001A = self.testMenu.addAction("Keithley 2001A")
		self.testK2001A.triggered.connect(self.testK2001ADialog)
		self.testA34972A = self.testMenu.addAction("Agilent 34972A")
		self.testA34972A.triggered.connect(self.testA34972ADialog)
		self.testGUV = self.testMenu.addAction("GUV")
		self.testGUV.triggered.connect(self.testGUVDialog)
		
		self.emailMenu = MyBar.addMenu("E-mail")
		self.emailSet = self.emailMenu.addAction("E-mail settings")
		self.emailSet.triggered.connect(self.email_set_dialog)
		self.emailData = self.emailMenu.addAction("E-mail data")
		self.emailData.triggered.connect(self.email_data_dialog)
				
		################### MENU BARS END ##################
		
		lbl1 = QLabel("Scan settings colon(;) separated:", self)
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
		
		unit_lbl = QLabel("Unit",self)
		self.combo3 = QComboBox(self)
		self.mylist3=["nm","um","wn"]
		self.combo3.addItems(self.mylist3)
		self.combo3.setCurrentIndex(self.mylist3.index(self.unit_str))
		self.combo3.setFixedWidth(65)
		
		##############################################
		
		shutter_lbl = QLabel("Shutter modus",self)
		self.combo4 = QComboBox(self)
		self.mylist4=["on","off","on and off"]
		self.combo4.addItems(self.mylist4)
		self.combo4.setCurrentIndex(self.mylist4.index(self.shutset))
		
		##############################################
		
		self.shind_lbl = QLabel(''.join(["Shutter ", self.shutnow.upper()]),self)
		self.shind_lbl.setFrameStyle(QFrame.Panel | QFrame.Raised)
		self.shind_lbl.setLineWidth(2)

		if self.shutnow=="on":
			self.shind_lbl.setStyleSheet("QWidget{background-color: green}")
		elif self.shutnow=="off":
			self.shind_lbl.setStyleSheet("QWidget{background-color: red}")

		##############################################
		
		pos_lbl = QLabel("Position modus",self)
		self.combo5 = QComboBox(self)
		self.mylist5=["A","B","A and B"]
		self.combo5.addItems(self.mylist5)
		self.combo5.setCurrentIndex(self.mylist5.index(self.posset))
		
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
		
		self.posind_lbl = QLabel(''.join(["Position ", self.posnow]),self)
		self.posind_lbl.setFrameStyle(QFrame.Panel | QFrame.Raised)
		self.posind_lbl.setLineWidth(2)
		
		if self.posnow=="A":
			self.posind_lbl.setStyleSheet("QWidget{background-color: yellow}")
		elif self.posnow=="B":
			self.posind_lbl.setStyleSheet("QWidget{background-color: magenta}")
		
		##############################################
		
		lbl5 = QLabel("Start scan and record data:", self)
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
		
		# add all groups from v1 to v6 in one vertical group v8
		v8 = QVBoxLayout()
		v8.addLayout(v1)
		v8.addLayout(h0)
		v8.addLayout(v4)
		v8.addLayout(v5)
		v8.addLayout(v6)
		
		##############################################
		
		# set GRAPHS and TOOLBARS to a new vertical group vcan
		self.win = pg.GraphicsWindow()
		
		self.p0 = self.win.addPlot()
		self.my_legend = self.p0.addLegend()
		self.c_k2001a_end_Aon = self.p0.plot(pen='m', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_k2001a_end_Aoff = self.p0.plot(pen='m')
		self.c_k2001a_end_Bon = self.p0.plot(pen='y', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_k2001a_end_Boff = self.p0.plot(pen='y')
		
		self.c_a34972a_end_Aon = self.p0.plot(pen='b', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_a34972a_end_Aoff = self.p0.plot(pen='b')
		self.c_a34972a_end_Bon = self.p0.plot(pen='g', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_a34972a_end_Boff = self.p0.plot(pen='g')
		
		self.c_guv_end_Aon = self.p0.plot(pen=None, symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_guv_end_Aoff = self.p0.plot(pen=None, symbol='d', symbolPen='m', symbolBrush='y', symbolSize=6)
		self.c_guv_end_Bon = self.p0.plot(pen=None, symbol='s', symbolPen='w', symbolBrush='g', symbolSize=6)
		self.c_guv_end_Boff = self.p0.plot(pen=None, symbol='d', symbolPen='w', symbolBrush='y', symbolSize=6)
		#self.my_legend.hide()
		
		self.p0.enableAutoRange()
		self.p0.setLabel('left', "Voltage", units='V', color='green')
		self.p0.setLabel('bottom', "Wavelength", units='m', color='white')
		
		self.win.nextRow()
		
		self.p1 = self.win.addPlot()
		self.c_k2001a_all_Aon = self.p1.plot(pen='m', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_k2001a_all_Aoff = self.p1.plot(pen='m')
		self.c_k2001a_all_Bon = self.p1.plot(pen='y', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_k2001a_all_Boff = self.p1.plot(pen='y')
		
		self.c_a34972a_all_Aon = self.p1.plot(pen='b', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_a34972a_all_Aoff = self.p1.plot(pen='b')
		self.c_a34972a_all_Bon = self.p1.plot(pen='g', symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_a34972a_all_Boff = self.p1.plot(pen='g')
		
		self.c_guv_all_Aon = self.p1.plot(pen=None, symbol='s', symbolPen='m', symbolBrush='g', symbolSize=6)
		self.c_guv_all_Aoff = self.p1.plot(pen=None, symbol='d', symbolPen='m', symbolBrush='y', symbolSize=6)
		self.c_guv_all_Bon = self.p1.plot(pen=None, symbol='s', symbolPen='w', symbolBrush='g', symbolSize=6)
		self.c_guv_all_Boff = self.p1.plot(pen=None, symbol='d', symbolPen='w', symbolBrush='y', symbolSize=6)
		
		# create plot and add it to the figure
		self.p2 = pg.ViewBox()
		self.c_time_wl=pg.PlotCurveItem(pen=pg.mkPen('y', width=3))
		self.p2.addItem(self.c_time_wl)
		# connect respective axes to the plot 
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Wavelength", units='m', color='yellow')
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis('right').linkToView(self.p2)
		self.p2.setXLink(self.p1)
		
		# Use automatic downsampling and clipping to reduce the drawing load
		self.p1.enableAutoRange()
		self.p1.setDownsampling(mode='peak')
		self.p1.setClipToView(True)
		
		# Labels and titels are placed here since they change dynamically
		self.p1.setLabel('left', "Voltage", units='V', color='red')
		self.p1.setLabel('bottom', "Elapsed time", units='s', color='white')
		
		##############################################
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QHBoxLayout()
		hbox.addLayout(v8,1)
		hbox.addWidget(self.win,3)
		
		vbox = QVBoxLayout()
		vbox.addLayout(hbox,3)
		vbox.addWidget(self.tableWidget,1)
		
		##############################################
		
		# send status info which button has been pressed
		#self.saveButton.clicked.connect(self.buttonClicked)
		#self.runButton.clicked.connect(self.buttonClicked)
		#self.abortButton.clicked.connect(self.buttonClicked)
		#self.saveplotsButton.clicked.connect(self.buttonClicked)
		#self.elapsedtimeButton.clicked.connect(self.buttonClicked)
		
		# reacts to choises picked in the menu
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
		
		self.threadpool = QThreadPool()
		print("Multithreading in TEST_gui_v1 with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning = False
		
		self.abortButton.setEnabled(False)
		self.pauseButton.setEnabled(False)
		
		self.write2file.setEnabled(True)
		self.conMode.setEnabled(True)
		self.testMenu.setEnabled(True)
		self.startEdit.setEnabled(False)
		self.stopEdit.setEnabled(False)
		self.stepEdit.setEnabled(False)
		self.dwelltimeEdit.setEnabled(False)
		self.runButton.setEnabled(False)
		self.combo3.setEnabled(False)
		self.combo4.setEnabled(False)
		self.combo5.setEnabled(False)
		self.combo6.setEnabled(False)
		self.combo7.setEnabled(False)
		
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.set_disconnect)
		self.timer.setSingleShot(True)
		
		##############################################
		
		self.setGeometry(100, 100, 900, 450)
		self.setWindowTitle("Scan Control And Data Acqusition")
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		vbox.setSizeConstraint(vbox.SetFixedSize)
		
		w = QWidget()
		w.setLayout(vbox)
		self.setCentralWidget(w)
		self.show()
		
		
	def set_bstyle_v1(self,button):
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(65)
		
		
	def onActivated3(self, text):
		self.unit_str=str(text)
		self.start_lbl.setText(''.join(["Start[",str(text),"]"]))
		self.stop_lbl.setText(''.join(["Stop[",str(text),"]"]))
		self.step_lbl.setText(''.join(["Step[",str(text),"]"]))
		
		
	def onActivated4(self, text):
		self.shutset = str(text)
		
		if self.shutset=="on and off":
			self.combo7.setEnabled(True)
		else:
			self.combo7.setEnabled(False)
			
			
	def onActivated5(self, text):
		self.posset = str(text)
		
		if self.posset=="A and B":
			self.combo6.setEnabled(True)
		else:
			self.combo6.setEnabled(False)
			
		
	def onActivated6(self, text):
		self.posdelay=int(text)
		
		
	def onActivated7(self, text):
		self.shutdelay=int(text)
		
		
	def createTable(self):
		tableWidget = QTableWidget()
		#tableWidget.setFixedWidth(260)
		
		# set row count
		#tableWidget.setRowCount(20)
		
		# set column count
		tableWidget.setColumnCount(6)
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
		
		tableWidget.setHorizontalHeaderLabels(["Detector","Wavel.[nm]","Channel voltages U[V]","Pos","Shut","T[s]"])
		
		# set horizontal header properties
		hh = tableWidget.horizontalHeader()
		for tal in range(5):
			if tal==2:
				hh.setSectionResizeMode(tal, QHeaderView.Stretch)
			else:
				hh.setSectionResizeMode(tal, QHeaderView.ResizeToContents)
		
		# set column width to fit contents
		tableWidget.resizeColumnsToContents()
		#tableWidget.setFixedWidth(250)
		
		# enable sorting
		#tableWidget.setSortingEnabled(True)
		
		return tableWidget
			
			
	def instrumentsDialog(self):
		
		self.Inst = Instruments_dialog.Instruments_dialog(self, self.inst_list, self.timer, self.config)
		self.Inst.exec()
		
		self.abortButton.setEnabled(False)
		self.pauseButton.setEnabled(False)
		
		self.write2file.setEnabled(True)
		self.conMode.setEnabled(True)
		self.testMenu.setEnabled(True)
		self.startEdit.setEnabled(True)
		self.stopEdit.setEnabled(True)
		self.stepEdit.setEnabled(True)
		self.dwelltimeEdit.setEnabled(True)
		
		if bool(self.inst_list):
			self.runButton.setText("Scan")
			self.runButton.setEnabled(True)
		else:
			self.runButton.setText("Load instrument!")
			self.runButton.setEnabled(False)
		
		if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
			self.combo3.setEnabled(True)
		else:
			self.combo3.setEnabled(False)
		
		if self.inst_list.get('Oriel'):
			self.combo5.setEnabled(True)
			if self.posset=="A and B":
				self.combo6.setEnabled(True)
			else:
				self.combo6.setEnabled(False)
		else:
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
		
		if self.inst_list.get('MS257_in'):
			self.combo4.setEnabled(True)
			if self.shutset=="on and off":
				self.combo7.setEnabled(True)
			else:
				self.combo7.setEnabled(False)
		else:
			self.combo4.setEnabled(False)
			self.combo7.setEnabled(False)
			
			
	def write2fileDialog(self):
		
		self.Write2file_dialog = Write2file_dialog.Write2file_dialog(self, self.config)
		self.Write2file_dialog.exec()
		
		try:
			self.config.read('config.ini')
			
			self.write2txt_str=self.config.get('DEFAULT','write2txt').strip().split(',')[0]
			self.write2txt_check=self.bool_(self.config.get('DEFAULT','write2txt').strip().split(',')[1])
			self.write2db_str=self.config.get('DEFAULT','write2db').strip().split(',')[0]
			self.write2db_check=self.bool_(self.config.get('DEFAULT','write2db').strip().split(',')[1])
			self.write2mat_str=self.config.get('DEFAULT','write2mat').strip().split(',')[0]
			self.write2mat_check=self.bool_(self.config.get('DEFAULT','write2mat').strip().split(',')[1])
			
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			raise
		
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
		
		self.MS257_dialog = MS257_dialog.MS257_dialog(self, self.config, self.inst_list)
		self.MS257_dialog.exec()
		
		
	def testOrielDialog(self):
		
		self.Oriel_dialog = Oriel_dialog.Oriel_dialog(self, self.config, self.inst_list)
		self.Oriel_dialog.exec()
		
		
	def testK2001ADialog(self):
		
		self.K2001A_dialog = K2001A_dialog.K2001A_dialog(self, self.config)
		self.K2001A_dialog.exec()
		
		
	def testA34972ADialog(self):
		
		self.Agilent34972A_dialog = Agilent34972A_dialog.Agilent34972A_dialog(self, self.config)
		self.Agilent34972A_dialog.exec()
		
	def testGUVDialog(self):
		
		self.GUV_dialog = GUV_dialog.GUV_dialog(self, self.config)
		self.GUV_dialog.exec()
		
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
		
		if self.inst_list.get('K2001A') or self.inst_list.get('Agilent34972A') or self.inst_list.get('GUV'):
			
			if self.write2txt_check:
				self.textfile = ''.join([self.create_file(self.write2txt_str),".txt"])
				with open(self.textfile, 'w') as thefile:
					thefile.write(''.join(["Detector type\tMS257_IN [nm]\tMS257_OUT [nm]\tVolt.[V]\tPos.\tShut.\tTimetr.[s]\tAbs date and time\n"]))
			
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
				self.db.execute('''CREATE TABLE spectra (detector text, ms257_in text, ms257_out text, voltage text, position text, shutter text, timetrace real, absolutetime text)''')
			
			
			
	def set_run(self):
		
		if not bool(self.inst_list):
			QMessageBox.warning(self, 'Message',"No instruments connected. At least 1 instrument is required.")
			return
		
		try:
			start_ = [float(i) for i in self.startEdit.text().split(';')]
			stop = [float(i) for i in self.stopEdit.text().split(';')]
			step = [float(i) for i in self.stepEdit.text().split(';')] 
			dwell = [float(i) for i in self.dwelltimeEdit.text().split(';')]
		except Exception as e:
			QMessageBox.warning(self, 'Message',"Scan parameters must be real numbers. Empty fields are not allowed!")
			return
		
		for i,j,k,l in zip(start_,stop,step,dwell):
			if i<0 or i>2500:
				QMessageBox.warning(self, 'Message',"Minimum start wavelength is in the range from 0 nm to 2500 nm")
				return
			if j<0 or j>2500:
				QMessageBox.warning(self, 'Message',"Minimum stop wavelength is in the range from 0 nm to 2500 nm")
				return
			if i>=j:
				QMessageBox.warning(self, 'Message',"Stop wavelength must be larger than the start wavelength")
				return
			if k<0 or k>100:
				QMessageBox.warning(self, 'Message',"Minimum step is in the range from 0 units to 100 units")
				return
			if l<0.1 or l>10:
				QMessageBox.warning(self, 'Message',"Monochromator dwell time is in the range from 0.1 sec to 10 sec")
				return
			
		self.prepare_file()
		self.timer.stop()
		self.clear_vars_graphs()
		
		self.abortButton.setEnabled(True)
		self.pauseButton.setEnabled(True)
		
		self.write2file.setEnabled(False)
		self.conMode.setEnabled(False)
		self.testMenu.setEnabled(False)
		self.startEdit.setEnabled(False)
		self.stopEdit.setEnabled(False)
		self.stepEdit.setEnabled(False)
		self.dwelltimeEdit.setEnabled(False)
		self.runButton.setEnabled(False)
		self.combo3.setEnabled(False)
		self.combo4.setEnabled(False)
		self.combo5.setEnabled(False)
		self.combo6.setEnabled(False)
		self.combo7.setEnabled(False)
		
		self.runButton.setText("Scaning...")
		self.isRunning = True
		
		shutter_list={'shutset':self.shutset,'shutdelay':self.shutdelay}
		pos_list={'posset':self.posset,'posdelay':self.posdelay}
		self.sssd = [start_, stop, step, dwell]
		obj = type('setscan_obj',(object,),{'inst_list':self.inst_list, 'unit':self.unit_str, 'shutter_list':shutter_list, 'pos_list':pos_list, 'sssd':self.sssd})
		self.worker=TEST_Worker(obj)
		
		self.worker.signals.update_all_k2001a.connect(self.update_all_k2001a)
		self.worker.signals.update_all_a34972a.connect(self.update_all_a34972a)
		self.worker.signals.update_all_guv.connect(self.update_all_guv)
		
		self.worker.signals.update_end_k2001a.connect(self.update_end_k2001a)
		self.worker.signals.update_end_a34972a.connect(self.update_end_a34972a)
		self.worker.signals.update_end_guv.connect(self.update_end_guv)
		
		self.worker.signals.update_wl_time.connect(self.update_wl_time)
		self.worker.signals.update_shutter.connect(self.update_shutter)
		self.worker.signals.update_oriel.connect(self.update_oriel)
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
		
		
		
		
		
		
	def update_end_k2001a(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime = pyqt_object
		
		ms257_in = format(float(ms257_in)*1e9, '.5f')
		ms257_out = format(float(ms257_out)*1e9, '.5f')
		wl = format(float(wl)*1e9, '.2f')
			
		#################################################
			
		if self.posnow=="A":
			if self.shutnow=="on":
				self.wl_k2001a_end_Aon.extend([ float(wl) ])
				self.volt_k2001a_end_Aon.extend([ float(volt) ])
				self.c_k2001a_end_Aon.setData(self.wl_k2001a_end_Aon, self.volt_k2001a_end_Aon)
				if len(self.wl_k2001a_end_Aon)==1:
					self.my_legend.addItem(self.c_k2001a_end_Aon, name='Keithley,A-ON')
					
			if self.shutnow=="off":
				self.wl_k2001a_end_Aoff.extend([ float(wl) ])
				self.volt_k2001a_end_Aoff.extend([ float(volt) ])
				self.c_k2001a_end_Aoff.setData(self.wl_k2001a_end_Aoff, self.volt_k2001a_end_Aoff)
				if len(self.wl_k2001a_end_Aoff)==1:
					self.my_legend.addItem(self.c_k2001a_end_Aoff, name='Keithley,A-OFF')
					
		if self.posnow=="B":
			if self.shutnow=="on":
				self.wl_k2001a_end_Bon.extend([ float(wl) ])
				self.volt_k2001a_end_Bon.extend([ float(volt) ])
				self.c_k2001a_end_Bon.setData(self.wl_k2001a_end_Bon, self.volt_k2001a_end_Bon)
				if len(self.wl_k2001a_end_Bon)==1:
					self.my_legend.addItem(self.c_k2001a_end_Bon, name='Keithley,B-ON')
					
			if self.shutnow=="off":
				self.wl_k2001a_end_Boff.extend([ float(wl) ])
				self.volt_k2001a_end_Boff.extend([ float(volt) ])
				self.c_k2001a_end_Boff.setData(self.wl_k2001a_end_Boff, self.volt_k2001a_end_Boff)
				if len(self.wl_k2001a_end_Boff)==1:
					self.my_legend.addItem(self.c_k2001a_end_Boff, name='Keithley,B-OFF')
					
		#################################################
		
		self.detector_.extend(["Keithley"])
		self.ms257_in_.extend([ms257_in])
		self.ms257_out_.extend([ms257_out])
		self.wl_.extend([wl])
		self.volt_.extend([volt])
		self.pos_.extend([self.posnow])
		self.shutter_.extend([self.shutnow])
		self.time_.extend([time])
		self.dateandtime_.extend([dateandtime])
		
		#################################################
		
		if self.write2db_check:
			# Save to a database file
			'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, timetrace real, absolutetime text)'''
			self.db.execute(''.join(["INSERT INTO spectra VALUES ('", "Keithley" ,"','", ms257_in,"','", ms257_out,"','", str(volt), "','", self.posnow,"','", self.shutnow, "',", time, ",'", dateandtime, "')"]))
			# Save (commit) the changes
			self.conn.commit()
			
		#################################################
		
		if self.write2mat_check:
			# save to a MATLAB file
			matdata={}
			matdata['detector']=self.detector_
			matdata['ms257_in']=self.ms257_in_
			matdata['ms257_out']=self.ms257_out_
			matdata['voltage']=self.volt_
			matdata['position']=self.pos_
			matdata['shutter']=self.shutter_
			matdata['timetrace']=self.time_
			matdata['absolutetime']=self.dateandtime_
			
			scipy.io.savemat(self.matfile, matdata)
			#print(scipy.io.loadmat(self.matfile).keys()) 
			#b = scipy.io.loadmat(self.matfile)
			#print(b['wavelength'])
		
		#################################################
		
		if self.write2txt_check:
			# Save to a readable textfile
			with open(self.textfile, 'a') as thefile:
				thefile.write("%s " %"Keithley")
				thefile.write("\t%s " %ms257_in)
				thefile.write("\t%s " %ms257_out)
				thefile.write("\t%s" %volt)
				thefile.write("\t%s" %self.posnow)
				thefile.write("\t%s" %self.shutnow)
				thefile.write("\t%s" %time)
				thefile.write("\t\t%s\n" %dateandtime)
			
		#################################################
		
		self.tal+=1
		
		# set row height
		self.tableWidget.setRowCount(self.tal+1)
		self.tableWidget.setRowHeight(self.tal, 12)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem("Keithley"))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem( wl ))
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem(format(float(volt), '.3e' )) )
		self.tableWidget.setItem(self.tal, 3, QTableWidgetItem(self.posnow) )
		self.tableWidget.setItem(self.tal, 4, QTableWidgetItem(self.shutnow) )
		self.tableWidget.setItem(self.tal, 5, QTableWidgetItem(format(float(time),'.2f') ))
		
		
		
		
		
	def update_end_a34972a(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime = pyqt_object
		
		ms257_in = format(float(ms257_in)*1e9, '.5f')
		ms257_out = format(float(ms257_out)*1e9, '.5f')
		wl = format(float(wl)*1e9, '.2f')
			
		#################################################
			
		if self.posnow=="A":
			if self.shutnow=="on":
				self.wl_a34972a_end_Aon.extend([ float(wl) ])
				self.volt_a34972a_end_Aon.extend([ float(volt) ])
				self.c_a34972a_end_Aon.setData(self.wl_a34972a_end_Aon, self.volt_a34972a_end_Aon)
				if len(self.wl_a34972a_end_Aon)==1:
					self.my_legend.addItem(self.c_a34972a_end_Aon, name='Agilent,A-ON')
					
			if self.shutnow=="off":
				self.wl_a34972a_end_Aoff.extend([ float(wl) ])
				self.volt_a34972a_end_Aoff.extend([ float(volt) ])
				self.c_a34972a_end_Aoff.setData(self.wl_a34972a_end_Aoff, self.volt_a34972a_end_Aoff)
				if len(self.wl_a34972a_end_Aoff)==1:
					self.my_legend.addItem(self.c_a34972a_end_Aoff, name='Agilent,A-OFF')
				
		if self.posnow=="B":
			if self.shutnow=="on":
				self.wl_a34972a_end_Bon.extend([ float(wl) ])
				self.volt_a34972a_end_Bon.extend([ float(volt) ])
				self.c_a34972a_end_Bon.setData(self.wl_a34972a_end_Bon, self.volt_a34972a_end_Bon)
				if len(self.wl_a34972a_end_Bon)==1:
					self.my_legend.addItem(self.c_a34972a_end_Bon, name='Agilent,B-ON')
					
			if self.shutnow=="off":
				self.wl_a34972a_end_Boff.extend([ float(wl) ])
				self.volt_a34972a_end_Boff.extend([ float(volt) ])
				self.c_a34972a_end_Boff.setData(self.wl_a34972a_end_Boff, self.volt_a34972a_end_Boff, name='Agilent,B-OFF')
				if len(self.wl_a34972a_end_Boff)==1:
					self.my_legend.addItem(self.c_a34972a_end_Boff, name='Agilent,B-OFF')
					
		#################################################
		
		self.detector_.extend(["Agilent"])
		self.ms257_in_.extend([ms257_in])
		self.ms257_out_.extend([ms257_out])
		self.wl_.extend([ wl ])
		self.volt_.extend([volt])
		self.pos_.extend([self.posnow])
		self.shutter_.extend([self.shutnow])
		self.time_.extend([time])
		self.dateandtime_.extend([dateandtime])
		
		#################################################
		
		if self.write2db_check:
			# Save to a database file
			'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, timetrace real, absolutetime text)'''
			self.db.execute(''.join(["INSERT INTO spectra VALUES ('", "Agilent" ,"','",ms257_in,"','", ms257_out,"','", str(volt), "','", self.posnow,"','", self.shutnow, "',", time, ",'", dateandtime, "')"]))
			# Save (commit) the changes
			self.conn.commit()
			
		#################################################
		
		if self.write2mat_check:
			# save to a MATLAB file
			matdata={}
			matdata['detector']=self.detector_
			matdata['ms257_in']=self.ms257_in_
			matdata['ms257_out']=self.ms257_out_
			matdata['voltage']=self.volt_
			matdata['position']=self.pos_
			matdata['shutter']=self.shutter_
			matdata['timetrace']=self.time_
			matdata['absolutetime']=self.dateandtime_
			
			scipy.io.savemat(self.matfile, matdata)
			#print(scipy.io.loadmat(self.matfile).keys()) 
			#b = scipy.io.loadmat(self.matfile)
			#print(b['wavelength'])
		
		#################################################
		
		if self.write2txt_check:
			# Save to a readable textfile
			with open(self.textfile, 'a') as thefile:
				thefile.write("%s " %"Agilent")
				thefile.write("\t%s " %ms257_in)
				thefile.write("\t%s " %ms257_out)
				thefile.write("\t%s" %volt)
				thefile.write("\t%s" %self.posnow)
				thefile.write("\t%s" %self.shutnow)
				thefile.write("\t%s" %time)
				thefile.write("\t\t%s\n" %dateandtime)
			
		#################################################
		
		self.tal+=1
		
		# set row height
		self.tableWidget.setRowCount(self.tal+1)
		self.tableWidget.setRowHeight(self.tal, 12)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem("Agilent"))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem( wl ))
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem(format(float(volt), '.3e' )) )
		self.tableWidget.setItem(self.tal, 3, QTableWidgetItem(self.posnow) )
		self.tableWidget.setItem(self.tal, 4, QTableWidgetItem(self.shutnow) )
		self.tableWidget.setItem(self.tal, 5, QTableWidgetItem(format(float(time),'.2f') ))
				
				
				
				
				
				
				
	def update_end_guv(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime = pyqt_object
		
		ms257_in = format(float(ms257_in)*1e9, '.5f')
		ms257_out = format(float(ms257_out)*1e9, '.5f')
		wl = format(float(wl)*1e9, '.2f')
		
		#################################################
			
		if self.posnow=="A":
			if self.shutnow=="on":
				self.wl_guv_end_Aon.extend( [float(wl)]*len(volt) )
				self.volt_guv_end_Aon.extend( volt )
				self.c_guv_end_Aon.setData(self.wl_guv_end_Aon, self.volt_guv_end_Aon, name='GUV,A-ON')
				if len(self.wl_guv_end_Aon)==len(volt):
					self.my_legend.addItem(self.c_guv_end_Aon, name='GUV,A-ON')
					
			if self.shutnow=="off":
				self.wl_guv_end_Aoff.extend( [float(wl)]*len(volt) )
				self.volt_guv_end_Aoff.extend( volt )
				self.c_guv_end_Aoff.setData(self.wl_guv_end_Aoff, self.volt_guv_end_Aoff)
				if len(self.wl_guv_end_Aoff)==len(volt):
					self.my_legend.addItem(self.c_guv_end_Aoff, name='GUV,A-OFF')
					
		if self.posnow=="B":
			if self.shutnow=="on":
				self.wl_guv_end_Bon.extend( [float(wl)]*len(volt) )
				self.volt_guv_end_Bon.extend( volt )
				self.c_guv_end_Bon.setData(self.wl_guv_end_Bon, self.volt_guv_end_Bon)
				if len(self.wl_guv_end_Bon)==len(volt):
					self.my_legend.addItem(self.c_guv_end_Bon, name='GUV,B-ON')
					
			if self.shutnow=="off":
				self.wl_guv_end_Boff.extend( [float(wl)]*len(volt) )
				self.volt_guv_end_Boff.extend( volt )
				self.c_guv_end_Boff.setData(self.wl_guv_end_Boff, self.volt_guv_end_Boff)
				if len(self.wl_guv_end_Boff)==len(volt):
					self.my_legend.addItem(self.c_guv_end_Boff, name='GUV,B-OFF')
					
		#################################################
		
		self.detector_.extend(["GUV"])
		self.ms257_in_.extend([ms257_in])
		self.ms257_out_.extend([ms257_out])
		self.wl_.extend([ wl ])
		self.volt_.extend(volt)
		self.pos_.extend([self.posnow])
		self.shutter_.extend([self.shutnow])
		self.time_.extend([time])
		self.dateandtime_.extend([dateandtime])
		
		#################################################
		
		if self.write2db_check:
			# Save to a database file
			'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, timetrace real, absolutetime text)'''
			self.db.execute(''.join(["INSERT INTO spectra VALUES ('", "GUV" ,"','",ms257_in,"','", ms257_out,"','", str(volt), "','", self.posnow,"','", self.shutnow, "',", time, ",'", dateandtime, "')"]))
			# Save (commit) the changes
			self.conn.commit()
			
		#################################################
		
		if self.write2mat_check:
			# save to a MATLAB file
			matdata={}
			matdata['detector']=self.detector_
			matdata['ms257_in']=self.ms257_in_
			matdata['ms257_out']=self.ms257_out_
			matdata['voltage']=self.volt_
			matdata['position']=self.pos_
			matdata['shutter']=self.shutter_
			matdata['timetrace']=self.time_
			matdata['absolutetime']=self.dateandtime_
			
			scipy.io.savemat(self.matfile, matdata)
			#print(scipy.io.loadmat(self.matfile).keys()) 
			#b = scipy.io.loadmat(self.matfile)
			#print(b['wavelength'])
		
		#################################################
		
		if self.write2txt_check:
			# Save to a readable textfile
			with open(self.textfile, 'a') as thefile:
				thefile.write("%s " %"GUV")
				thefile.write("\t\t%s " %ms257_in)
				thefile.write("\t%s " %ms257_out)
				thefile.write("\t%s" %volt)
				thefile.write("\t%s" %self.posnow)
				thefile.write("\t%s" %self.shutnow)
				thefile.write("\t%s" %time)
				thefile.write("\t\t%s\n" %dateandtime)
			
		#################################################
		
		self.tal+=1
		
		# set row height
		self.tableWidget.setRowCount(self.tal+1)
		self.tableWidget.setRowHeight(self.tal, 12)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem("GUV"))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem( wl ))
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem( ', '.join([format(i, '.2e' ) for i in volt]) ))
		self.tableWidget.setItem(self.tal, 3, QTableWidgetItem(self.posnow) )
		self.tableWidget.setItem(self.tal, 4, QTableWidgetItem(self.shutnow) )
		self.tableWidget.setItem(self.tal, 5, QTableWidgetItem(format(float(time),'.2f') ))
				
				
				
				
				
	def update_all_k2001a(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime = pyqt_object
		
		#################################################
		
		if self.posnow=="A":
			if self.shutnow=="on":
				self.time_k2001a_all_Aon.extend([ float(time) ])
				self.volt_k2001a_all_Aon.extend([ float(volt) ])
				self.c_k2001a_all_Aon.setData(self.time_k2001a_all_Aon, self.volt_k2001a_all_Aon)
			if self.shutnow=="off":
				self.time_k2001a_all_Aoff.extend([ float(time) ])
				self.volt_k2001a_all_Aoff.extend([ float(volt) ])
				self.c_k2001a_all_Aoff.setData(self.time_k2001a_all_Aoff, self.volt_k2001a_all_Aoff)
				
		if self.posnow=="B":
			if self.shutnow=="on":
				self.time_k2001a_all_Bon.extend([ float(time) ])
				self.volt_k2001a_all_Bon.extend([ float(volt) ])
				self.c_k2001a_all_Bon.setData(self.time_k2001a_all_Bon, self.volt_k2001a_all_Bon)
			if self.shutnow=="off":
				self.time_k2001a_all_Boff.extend([ float(time) ])
				self.volt_k2001a_all_Boff.extend([ float(volt) ])
				self.c_k2001a_all_Boff.setData(self.time_k2001a_all_Boff, self.volt_k2001a_all_Boff)
				
				
				
				
	def update_all_a34972a(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime = pyqt_object
		
		#################################################
		
		if self.posnow=="A":
			if self.shutnow=="on":
				self.time_a34972a_all_Aon.extend([ float(time) ])
				self.volt_a34972a_all_Aon.extend([ float(volt) ])
				self.c_a34972a_all_Aon.setData(self.time_a34972a_all_Aon, self.volt_a34972a_all_Aon)
			if self.shutnow=="off":
				self.time_a34972a_all_Aoff.extend([ float(time) ])
				self.volt_a34972a_all_Aoff.extend([ float(volt) ])
				self.c_a34972a_all_Aoff.setData(self.time_a34972a_all_Aoff, self.volt_a34972a_all_Aoff)
				
		if self.posnow=="B":
			if self.shutnow=="on":
				self.time_a34972a_all_Bon.extend([ float(time) ])
				self.volt_a34972a_all_Bon.extend([ float(volt) ])
				self.c_a34972a_all_Bon.setData(self.time_a34972a_all_Bon, self.volt_a34972a_all_Bon)
			if self.shutnow=="off":
				self.time_a34972a_all_Boff.extend([ float(time) ])
				self.volt_a34972a_all_Boff.extend([ float(volt) ])
				self.c_a34972a_all_Boff.setData(self.time_a34972a_all_Boff, self.volt_a34972a_all_Boff)
				
				
				
	def update_all_guv(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime = pyqt_object
		
		#################################################
		
		if self.posnow=="A":
			if self.shutnow=="on":
				self.time_guv_all_Aon.extend( [float(time)]*len(volt) )
				self.volt_guv_all_Aon.extend( volt )
				self.c_guv_all_Aon.setData(self.time_guv_all_Aon, self.volt_guv_all_Aon)
			if self.shutnow=="off":
				self.time_guv_all_Aoff.extend( [float(time)]*len(volt) )
				self.volt_guv_all_Aoff.extend( volt )
				self.c_guv_all_Aoff.setData(self.time_guv_all_Aoff, self.volt_guv_all_Aoff)
				
		if self.posnow=="B":
			if self.shutnow=="on":
				self.time_guv_all_Bon.extend( [float(time)]*len(volt) )
				self.volt_guv_all_Bon.extend( volt )
				self.c_guv_all_Bon.setData(self.time_guv_all_Bon, self.volt_guv_all_Bon)
			if self.shutnow=="off":
				self.time_guv_all_Boff.extend( [float(time)]*len(volt))
				self.volt_guv_all_Boff.extend( volt )
				self.c_guv_all_Boff.setData(self.time_guv_all_Boff, self.volt_guv_all_Boff)
				
				
				
	def update_wl_time(self,pyqt_object):
		
		ms257_in, ms257_out, wl, time, dateandtime = pyqt_object
		
		wl = format(float(wl)*1e9, '.2f')
			
		#################################################
		
		if self.inst_list.get('K2001A') or self.inst_list.get('Agilent34972A') or self.inst_list.get('GUV'):
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
		
		if not self.inst_list.get('K2001A') and not self.inst_list.get('Agilent34972A') and not self.inst_list.get('GUV'):
			self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
			self.p2.enableAutoRange()
		
		self.time.extend([ float(time) ])
		self.wl.extend([ float(wl) ])
		self.c_time_wl.setData(self.time, self.wl)
				
				
				
				
				
				
				
				
				
			
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
	def update_shutter(self,onoff):
		
		self.shutnow = onoff
		
		self.config.set('DEFAULT','shutter', ','.join([self.shutset, self.shutnow, str(self.shutdelay)]) )
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
		self.shind_lbl.setText(''.join(["Shutter ", self.shutnow.upper()]))
		if self.shutnow=="on":
			self.shind_lbl.setStyleSheet("QWidget{background-color: green}")
		elif self.shutnow=="off":
			self.shind_lbl.setStyleSheet("QWidget{background-color: red}")
			
	def update_oriel(self,aorb):
		
		self.posnow = aorb
		
		self.config.set('DEFAULT','pos', ','.join([self.posset, self.posnow, str(self.posdelay)]) )
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
		self.posind_lbl.setText(''.join(["Position ", self.posnow]))
		if self.posnow=="A":
			self.posind_lbl.setStyleSheet("QWidget{background-color: yellow}")
		elif self.posnow=="B":
			self.posind_lbl.setStyleSheet("QWidget{background-color: magenta}")
			
			
	def make_3Dplot(self):
		
		try:
			wl_ = [float(i) for i in self.wl_]
			time_ = [float(i) for i in self.time_]
			volt_ = [float(i) for i in self.volt_]
		except ValueError:
			return
		
		fig=plt.figure(figsize=(8,6))
		ax= fig.add_subplot(111, projection='3d')
		
		ax.plot(wl_, time_, volt_, linewidth=1)
		#ax=fig.gca(projection='2d')
		ax.set_xlabel('lambda[nm]')
		ax.set_ylabel('Time[s]')
		ax.set_zlabel('Voltage[V]')
		
		plt.show()
		#fig.savefig(''.join(['plot_',self.time_str,'_3D.png']))
		
		
	def set_disconnect(self):
		
		##########################################
		
		if self.inst_list.get("MS257_in"):
			if self.inst_list.get("MS257_in").is_open():
				self.inst_list.get("MS257_in").close()
			self.inst_list.pop('MS257_in', None)
				
		##########################################
		
		if self.inst_list.get("MS257_out"):
			if self.inst_list.get("MS257_out").is_open():
				self.inst_list.get("MS257_out").close()
			self.inst_list.pop('MS257_out', None)
			
		##########################################
		
		if self.inst_list.get("Oriel"):
			if self.inst_list.get("Oriel").is_open():
				self.inst_list.get("Oriel").close()
			self.inst_list.pop('Oriel', None)
				
		##########################################
		
		if self.inst_list.get("K2001A"):
			if self.inst_list.get("K2001A").is_open():
				self.inst_list.get("K2001A").close()
			self.inst_list.pop('K2001A', None)
			
		##########################################
		
		if self.inst_list.get("Agilent34972A"):
			if self.inst_list.get("Agilent34972A").is_open():
				self.inst_list.get("Agilent34972A").close()
			self.inst_list.pop('Agilent34972A', None)
			
		##########################################
		
		if self.inst_list.get("GUV"):
			if self.inst_list.get("GUV").is_open():
				self.inst_list.get("GUV").close()
			self.inst_list.pop('GUV', None)
			
		##########################################
		
		if bool(self.inst_list):
			self.runButton.setText("Scan")
			self.runButton.setEnabled(True)
		else:
			self.runButton.setText("Load instrument!")
			self.runButton.setEnabled(False)
		
		print("All ports DISCONNECTED")
		
		self.conMode.setEnabled(True)
		self.testMenu.setEnabled(True)
		
		
	def set_abort(self):
		
		self.worker.abort()
		
		
	def set_pause(self):
		
		sender=self.sender()
		self.worker.pause()
		
		if sender.text()=="Continue":
			self.pauseButton.setText("Pause")
			self.runButton.setText("Scaning...")
			self.abortButton.setEnabled(True)
		elif sender.text()=="Pause":
			self.pauseButton.setText("Continue")
			self.runButton.setText("Paused")
			self.abortButton.setEnabled(False)
			
			
	def finished(self):
		'''
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
		'''
		if self.inst_list.get('K2001A') or self.inst_list.get('Agilent34972A') or self.inst_list.get('GUV'):
			#self.make_3Dplot()
			if self.write2db_check:
				self.conn.close()
				
		try:
			self.emailset_str = self.config.get('DEFAULT','emailset').strip().split(',')
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			raise
		
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()
			
		self.isRunning = False
		
		self.abortButton.setEnabled(False)
		self.pauseButton.setEnabled(False)
		
		self.write2file.setEnabled(True)
		self.conMode.setEnabled(True)
		self.testMenu.setEnabled(True)
		self.startEdit.setEnabled(True)
		self.stopEdit.setEnabled(True)
		self.stepEdit.setEnabled(True)
		self.dwelltimeEdit.setEnabled(True)
		
		if bool(self.inst_list):
			self.runButton.setText("Scan")
			self.runButton.setEnabled(True)
		else:
			self.runButton.setText("Load instrument!")
			self.runButton.setEnabled(False)
		
		if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
			self.combo3.setEnabled(True)
		else:
			self.combo3.setEnabled(False)
		
		if self.inst_list.get('Oriel'):
			self.combo5.setEnabled(True)
			if self.posset=="A and B":
				self.combo6.setEnabled(True)
			else:
				self.combo6.setEnabled(False)
		else:
			self.combo5.setEnabled(False)
			self.combo6.setEnabled(False)
		
		if self.inst_list.get('MS257_in'):
			self.combo4.setEnabled(True)
			if self.shutset=="on and off":
				self.combo7.setEnabled(True)
			else:
				self.combo7.setEnabled(False)
		else:
			self.combo4.setEnabled(False)
			self.combo7.setEnabled(False)
		
		self.timer.start(1000*300)
		
		
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
		
		self.wl_a34972a_end_Aon = []
		self.wl_a34972a_end_Aoff = []
		self.wl_a34972a_end_Bon = []
		self.wl_a34972a_end_Boff = []
		
		self.time_a34972a_all_Aon = []
		self.time_a34972a_all_Aoff = []
		self.time_a34972a_all_Bon = []
		self.time_a34972a_all_Boff = []
		
		self.volt_a34972a_end_Aon = []
		self.volt_a34972a_end_Aoff = []
		self.volt_a34972a_end_Bon = []
		self.volt_a34972a_end_Boff = []
		
		self.volt_a34972a_all_Aon = []
		self.volt_a34972a_all_Aoff = []
		self.volt_a34972a_all_Bon = []
		self.volt_a34972a_all_Boff = []
		
		
		
		self.wl_guv_end_Aon = []
		self.wl_guv_end_Aoff = []
		self.wl_guv_end_Bon = []
		self.wl_guv_end_Boff = []
		
		self.time_guv_all_Aon = []
		self.time_guv_all_Aoff = []
		self.time_guv_all_Bon = []
		self.time_guv_all_Boff = []
		
		self.volt_guv_end_Aon = []
		self.volt_guv_end_Aoff = []
		self.volt_guv_end_Bon = []
		self.volt_guv_end_Boff = []
		
		self.volt_guv_all_Aon = []
		self.volt_guv_all_Aoff = []
		self.volt_guv_all_Bon = []
		self.volt_guv_all_Boff = []
		
		
		
		self.wl_k2001a_end_Aon = []
		self.wl_k2001a_end_Aoff = []
		self.wl_k2001a_end_Bon = []
		self.wl_k2001a_end_Boff = []
		
		self.time_k2001a_all_Aon = []
		self.time_k2001a_all_Aoff = []
		self.time_k2001a_all_Bon = []
		self.time_k2001a_all_Boff = []
		
		self.volt_k2001a_end_Aon = []
		self.volt_k2001a_end_Aoff = []
		self.volt_k2001a_end_Bon = []
		self.volt_k2001a_end_Boff = []
		
		self.volt_k2001a_all_Aon = []
		self.volt_k2001a_all_Aoff = []
		self.volt_k2001a_all_Bon = []
		self.volt_k2001a_all_Boff = []
		
		self.time = []
		self.wl = []
		
		self.detector_=[]
		self.ms257_in_=[]
		self.ms257_out_=[]
		self.wl_=[]
		self.volt_=[]
		self.pos_=[]
		self.shutter_=[]
		self.time_=[]
		self.dateandtime_=[]
		
		self.tableWidget.clearContents()
		
		self.my_legend.removeItem('Keithley,A-ON')
		self.my_legend.removeItem('Keithley,A-OFF')
		self.my_legend.removeItem('Keithley,B-ON')
		self.my_legend.removeItem('Keithley,B-OFF')
	
		self.my_legend.removeItem('Agilent,A-ON')
		self.my_legend.removeItem('Agilent,A-OFF')
		self.my_legend.removeItem('Agilent,B-ON')
		self.my_legend.removeItem('Agilent,B-OFF')
		
		self.my_legend.removeItem('GUV,A-ON')
		self.my_legend.removeItem('GUV,A-OFF')
		self.my_legend.removeItem('GUV,B-ON')
		self.my_legend.removeItem('GUV,B-OFF')

		self.c_k2001a_end_Aon.clear()
		self.c_k2001a_end_Aoff.clear()
		self.c_k2001a_end_Bon.clear()
		self.c_k2001a_end_Boff.clear()
		
		self.c_k2001a_all_Aon.clear()
		self.c_k2001a_all_Aoff.clear()
		self.c_k2001a_all_Bon.clear()
		self.c_k2001a_all_Boff.clear()
		
		self.c_a34972a_end_Aon.clear()
		self.c_a34972a_end_Aoff.clear()
		self.c_a34972a_end_Bon.clear()
		self.c_a34972a_end_Boff.clear()
		
		self.c_a34972a_all_Aon.clear()
		self.c_a34972a_all_Aoff.clear()
		self.c_a34972a_all_Bon.clear()
		self.c_a34972a_all_Boff.clear()
		
		self.c_guv_end_Aon.clear()
		self.c_guv_end_Aoff.clear()
		self.c_guv_end_Bon.clear()
		self.c_guv_end_Boff.clear()
		
		self.c_guv_all_Aon.clear()
		self.c_guv_all_Aoff.clear()
		self.c_guv_all_Bon.clear()
		self.c_guv_all_Boff.clear()
		
		self.c_time_wl.clear()
		
		
	def load_(self):
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
			
			self.posset = self.config.get('DEFAULT','pos').strip().split(',')[0]
			self.posnow = self.config.get('DEFAULT','pos').strip().split(',')[1]
			self.posdelay = int(self.config.get('DEFAULT','pos').strip().split(',')[2])
			
			self.shutset = self.config.get('DEFAULT','shutter').strip().split(',')[0]
			self.shutnow = self.config.get('DEFAULT','shutter').strip().split(',')[1]
			self.shutdelay = int(self.config.get('DEFAULT','shutter').strip().split(',')[2])
			
			self.sssd = self.config.get('DEFAULT','sssd').strip().split(',')
			self.unit_str = self.config.get('DEFAULT','unit')
			self.write2txt_str=self.config.get('DEFAULT','write2txt').strip().split(',')[0]
			self.write2txt_check=self.bool_(self.config.get('DEFAULT','write2txt').strip().split(',')[1])
			self.write2db_str=self.config.get('DEFAULT','write2db').strip().split(',')[0]
			self.write2db_check=self.bool_(self.config.get('DEFAULT','write2db').strip().split(',')[1])
			self.write2mat_str=self.config.get('DEFAULT','write2mat').strip().split(',')[0]
			self.write2mat_check=self.bool_(self.config.get('DEFAULT','write2mat').strip().split(',')[1])
			self.time_str = self.config.get('DEFAULT','timetrace')
			
			self.ms257inport_str=self.config.get('DEFAULT','ms257inport').strip().split(',')[0]
			self.ms257inport_check=self.bool_(self.config.get('DEFAULT','ms257inport').strip().split(',')[1])
			self.ms257outport_str=self.config.get('DEFAULT','ms257outport').strip().split(',')[0]
			self.ms257outport_check=self.bool_(self.config.get('DEFAULT','ms257outport').strip().split(',')[1])
			self.k2001aport_str=self.config.get('DEFAULT','k2001aport').strip().split(',')[0]
			self.k2001aport_check=self.bool_(self.config.get('DEFAULT','k2001aport').strip().split(',')[1])
			self.a34972aport_str=self.config.get('DEFAULT','a34972aport').strip().split(',')[0]
			self.a34972aport_check=self.bool_(self.config.get('DEFAULT','a34972aport').strip().split(',')[1])
			self.guvport_str=self.config.get('DEFAULT','guvport').strip().split(',')[0]
			self.guvport_check=self.bool_(self.config.get('DEFAULT','guvport').strip().split(',')[1])
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
		
		self.config.set('DEFAULT','pos', ','.join([self.posset, self.posnow, str(self.posdelay)]) )
		self.config.set('DEFAULT','shutter', ','.join([self.shutset, self.shutnow, str(self.shutdelay)]) )
		self.config.set('DEFAULT','sssd',','.join([str(self.startEdit.text()),str(self.stopEdit.text()),str(self.stepEdit.text()),str(self.dwelltimeEdit.text())]))
		self.config.set('DEFAULT','unit',self.unit_str)
		self.config.set('DEFAULT','timetrace',self.time_str)

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
					
			if self.inst_list.get("GUV"):
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
	
	
