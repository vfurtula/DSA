#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import time, datetime, numpy, sys, RUN_gui

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot, QByteArray, Qt
				
				
				
				
				
class K2001A_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
	def __init__(self,*argv):
		super(K2001A_Worker, self).__init__()
		# constants	
		self.abort_flag=False
		self.pause_flag=False
		
		self.inst_list=argv[0].inst_list
		
		self.signals = RUN_gui.WorkerSignals()
		
	def abort(self):
		self.abort_flag=True
		
	def pause(self):
		if self.pause_flag:
			self.pause_flag=False
		else:
			self.pause_flag=True
			
	@pyqtSlot()
	def run(self):
		# First wait according to the specified delay for position A and position B
		time_start=time.time()
		# while dwelling record voltages, then get the last recoreded voltage and pass it
		while not self.abort_flag:
			while self.pause_flag:
				time.sleep(0.1)
				
			time_elap=format(time.time()-time_start, '07.2f')
			
			if self.inst_list.get('K2001A'):
				V_k2001a=format(self.inst_list.get('K2001A').return_voltage(),'.6e')
				self.signals.update_k2001a.emit([V_k2001a,time_elap])
				
				
				
				
class A34972A_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
	def __init__(self,*argv):
		super(A34972A_Worker, self).__init__()
		# constants	
		self.abort_flag=False
		self.pause_flag=False
		
		self.inst_list=argv[0].inst_list
		
		self.signals = RUN_gui.WorkerSignals()
		
	def abort(self):
		self.abort_flag=True
		
	def pause(self):
		if self.pause_flag:
			self.pause_flag=False
		else:
			self.pause_flag=True
			
	@pyqtSlot()
	def run(self):
		# First wait according to the specified delay for position A and position B
		time_start=time.time()
		# while dwelling record voltages, then get the last recoreded voltage and pass it
		while not self.abort_flag:
			while self.pause_flag:
				time.sleep(0.1)
				
			time_elap=format(time.time()-time_start, '07.2f')
			
			if self.inst_list.get('A34972A'):
				V_a34972a=format(self.inst_list.get('A34972A').return_voltage(),'.6e')
				self.signals.update_a34972a.emit([V_a34972a,time_elap])
				
				
				
class GUV_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
	def __init__(self,*argv):
		super(GUV_Worker, self).__init__()
		# constants	
		self.abort_flag=False
		self.pause_flag=False
		
		self.inst_list=argv[0].inst_list
		
		self.signals = RUN_gui.WorkerSignals()
		
	def abort(self):
		self.abort_flag=True
		
	def pause(self):
		if self.pause_flag:
			self.pause_flag=False
		else:
			self.pause_flag=True
			
	@pyqtSlot()
	def run(self):
		# First wait according to the specified delay for position A and position B
		time_start=time.time()
		# while dwelling record voltages, then get the last recoreded voltage and pass it
		while not self.abort_flag:
			while self.pause_flag:
				time.sleep(0.1)
				
			time_elap=format(time.time()-time_start, '07.2f')
			
			if self.inst_list.get('GUV'):
				V_guv = self.inst_list.get('GUV').return_powden()
				V_guv=[float(j) for j in [format(i,'.6e') for i in V_guv]]
				self.signals.update_guv.emit([V_guv,time_elap])
				
				
				
				
				
				
				
				
				
				
				
				
				
class Scan_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
	def __init__(self,*argv):
		super(Scan_Worker, self).__init__()
		
		# constants	
		self.abort_flag=False
		self.pause_flag=False
		
		self.inst_list=argv[0].inst_list
		self.unit = argv[0].unit
		self.grating = argv[0].grating
		self.avgpts_a = argv[0].avgpts[0]
		self.avgpts_b = argv[0].avgpts[1]
		
		shutter_list = argv[0].shutter_list
		self.shutset = shutter_list.get('shutset')
		
		pos_list = argv[0].pos_list
		self.posset = pos_list.get('posset')
		
		self.posA_delay = pos_list.get('posA_delay')
		self.posB_delay = pos_list.get('posB_delay')
		self.posAB_delay = pos_list.get('posAB_delay')
		
		self.sssd = argv[0].sssd
		
		self.signals = RUN_gui.WorkerSignals()
		
		
	def abort(self):
		
		self.abort_flag=True
		
		
	def pause(self):
		
		if self.pause_flag:
			self.pause_flag=False
		else:
			self.pause_flag=True
		
		
	def dateandtime(self):
		
		now = datetime.datetime.now()
		sm1 = now.strftime("%y.%m.%d - %H:%M:")
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
		# set UNITS on MS257
		
		if self.inst_list.get('MS257_in'):
			self.inst_list.get('MS257_in').setGRATING(self.grating)
			print(''.join(["MS257 input - grating set to ",self.grating]))
			
			self.inst_list.get('MS257_in').setUNITS(self.unit.upper())
			print(''.join(["MS257 input - units set to ",self.unit.upper()]))
			
		if self.inst_list.get('MS257_out'):
			self.inst_list.get('MS257_out').setGRATING(self.grating)
			print(''.join(["MS257 output - grating set to ",self.grating]))
			
			self.inst_list.get('MS257_out').setUNITS(self.unit.upper())
			print(''.join(["MS257 output - units set to ",self.unit.upper()]))
		
		time.sleep(3)
		
		if not self.inst_list.get('MS257_in'):
			self.signals.update_shutter.emit("?")
			self.shutset = '?'
			
		if not self.inst_list.get('Oriel'):
			self.signals.update_oriel.emit("?")
			self.posset = '?'
		
		# set Keithely 2001A supply
		# set Agilent 34972A supply
		
		if self.inst_list.get('K2001A'):
			self.inst_list.get('K2001A').set_dc_voltage()
			
		if self.inst_list.get('A34972A'):
			self.inst_list.get('A34972A').set_dc_voltage()
		
		if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
			print("The current monochromator position is:")
			
		self.time_start=time.time()
		taeller_posA=0
		taeller_posB=0
		
		for i,j,k,l in zip(self.sssd[0],self.sssd[1],self.sssd[2],self.sssd[3]):
			wv_scanlist=numpy.arange(i,j+k,k)
			self.dwell=l
			
			for new_position in wv_scanlist:
				# abort the scan
				
				if self.abort_flag:
					self.close_shutter()
					return
				# pause the scan
				while self.pause_flag:
					time.sleep(0.1)
				
				# go to the START position
				if self.inst_list.get('MS257_in'):
					self.inst_list.get('MS257_in').goToWL(new_position)
					
				if self.inst_list.get('MS257_out'):
					self.inst_list.get('MS257_out').goToWL(new_position)
					
				# read the actual START position
				if self.inst_list.get('MS257_in'):
					ms257_in=self.inst_list.get('MS257_in').getCurrentWL()
					self.ms257_in=format(ms257_in, '.5e')
					self.step_wl=float(format(new_position,'.5f'))
					print('MS257_in',self.step_wl, self.unit)
					
				if self.inst_list.get('MS257_out'):
					ms257_out=self.inst_list.get('MS257_out').getCurrentWL()
					self.ms257_out=format(ms257_out, '.5e')
					self.step_wl=float(format(new_position,'.5f'))
					print('MS257_out',self.step_wl, self.unit)
					
				# A and B positions
				if self.posset=="A<->B":
					# abort the scan
					if self.abort_flag:
						self.close_shutter()
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					##################################
					# Set the MIRROR in the A position
					self.set_pos("A")
					
					if self.shutset=="on->off":
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
							
						###############################################
						
						# Record dark light only once at the beginning
						if taeller_posA==0:
							# record while DARK
							self.close_shutter()
							taeller_posA+=1
							
						###############################################
						
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while LIGHT
						self.open_shutter()
						self.my_legend = ''.join(["A-",u'\u0394'])
						self.close_shutter()
						
						###############################################
						
					elif self.shutset=="on<->off":
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while DARK
						self.close_shutter()
						
						###############################################
						
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while LIGHT
						self.open_shutter()
						self.my_legend = ''.join(["A-",u'\u0394'])
						self.close_shutter()
						
						###############################################
						
					else:
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK / LIGHT
						if self.shutset=="on":
							self.close_shutter()
						elif self.shutset=="off":
							self.open_shutter()
						
						self.my_legend = ''.join(["A-",self.shutset.upper()])
						self.close_shutter()
						
						###############################################
					
					# abort the scan
					if self.abort_flag:
						self.close_shutter()
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					##################################
					# Set the MIRROR in the B position
					self.set_pos("B")
					
					if self.shutset=="on->off":
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# Record dark light only once at the beginning
						if taeller_posB==0:
							# record while DARK
							self.close_shutter()
							taeller_posB+=1
						
						###############################################
						
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while LIGHT
						self.open_shutter()
						self.my_legend = ''.join(["B-",u'\u0394'])
						self.close_shutter()
						
						###############################################
						
					elif self.shutset=="on<->off":
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK
						self.close_shutter()
						
						###############################################
						
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while LIGHT
						self.open_shutter()
						self.my_legend = ''.join(["B-",u'\u0394'])
						self.close_shutter()
						
						###############################################
						
					else:
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						# record while DARK / LIGHT
						if self.shutset=="on":
							self.close_shutter()
						elif self.shutset=="off":
							self.open_shutter()
						
						self.my_legend = ''.join(["B-",self.shutset.upper()])
						
						self.close_shutter()
						###############################################
				
				# Set the MIRROR in the A position
				elif self.posset=="A":
					# abort the scan
					if self.abort_flag:
						self.close_shutter()
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					##################################
					# Set the MIRROR in the A position
					self.set_pos("A")
					
					if self.shutset=="on->off":
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# Record dark light only once at the beginning
						if taeller_posA==0:
							# record while DARK
							self.close_shutter()
							taeller_posA+=1
						
						###############################################
						
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while LIGHT
						self.open_shutter()
						self.my_legend = ''.join(["A-",u'\u0394'])
						self.close_shutter()
						
						###############################################
						
					elif self.shutset=="on<->off":
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while DARK
						self.close_shutter()
						
						###############################################
						
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while LIGHT
						self.open_shutter()
						self.my_legend = ''.join(["A-",u'\u0394'])
						self.close_shutter()
						
						###############################################
						
					else:
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while DARK / LIGHT
						if self.shutset=="on":
							self.close_shutter()
						elif self.shutset=="off":
							self.open_shutter()
						
						self.my_legend = ''.join(["A-",self.shutset.upper()])
						self.close_shutter()
						
						###############################################
				
				# Set the MIRROR in the B position
				elif self.posset in ["B","?"]:
					# abort the scan
					if self.abort_flag:
						self.close_shutter()
						return
					# pause the scan
					while self.pause_flag:
						time.sleep(0.1)
					
					##################################
					# Set the MIRROR in the B position
					self.set_pos("B")
					
					if self.shutset=="on->off":
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# Record dark light only once at the beginning
						if taeller_posB==0:
							# record while DARK
							self.close_shutter()
							taeller_posB+=1
						
						###############################################
						
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while LIGHT
						self.open_shutter()
						self.my_legend = ''.join([self.posset,"-",u'\u0394'])
						self.close_shutter()
						
						###############################################
					
					elif self.shutset=="on<->off":
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
							
						###############################################
						
						# record while DARK
						self.close_shutter()
						
						###############################################
						
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while LIGHT
						self.open_shutter()
						self.my_legend = ''.join([self.posset,"-",u'\u0394'])
						self.close_shutter()
						
						###############################################
					
					else:
						# abort the scan
						if self.abort_flag:
							self.close_shutter()
							return
						# pause the scan
						while self.pause_flag:
							time.sleep(0.1)
						
						###############################################
						
						# record while DARK / LIGHT
						if self.shutset=="on":
							self.close_shutter()
						elif self.shutset=="off":
							self.open_shutter()
						
						self.my_legend = ''.join([self.posset,"-",self.shutset.upper()])
						self.close_shutter()
					
		# Close the shutter and prevent light from coming out
		self.close_shutter()
		
		
	def close_shutter(self):
		if self.inst_list.get('MS257_in'):
			self.inst_list.get('MS257_in').setSHUTTER("on")
			self.signals.update_shutter.emit("on")
			self.shutset = "on"
			print("Shutter on - DARK")
			
			
	def open_shutter(self):
		if self.inst_list.get('MS257_in'):
			self.inst_list.get('MS257_in').setSHUTTER("off")
			self.signals.update_shutter.emit("off")
			self.shutset = "off"
			print("Shutter off - LIGHT")
			
			
	def set_pos(self,my_str):
		
		if my_str=="A":
			self.avgpts=self.avgpts_a
		elif my_str=="B":
			self.avgpts=self.avgpts_b
			
		if self.inst_list.get('Oriel'):
			# close the shutter before moving the mirror to position A or position B
			self.close_shutter()
			# move the mirror to position A or position B
			if my_str=="A":
				self.inst_list.get('Oriel').goto_a()
			elif my_str=="B":
				self.inst_list.get('Oriel').goto_b()
			# wait until the movement is finished
			time_start_=time.time()
			while (time.time()-time_start_)<self.posAB_delay and not self.abort_flag:
				time.sleep(0.05)
			self.signals.update_oriel.emit(my_str)
			print("Mirror position",my_str)
			self.posset = my_str
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
