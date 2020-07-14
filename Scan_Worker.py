#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import time, datetime, numpy, sys, RUN_gui

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot, QByteArray, Qt
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
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
		'''
		if self.inst_list.get('K2001A'):
			self.inst_list.get('K2001A').set_dc_voltage()
		if self.inst_list.get('A34972A'):
			self.inst_list.get('A34972A').set_dc_voltage()
		if self.inst_list.get('GUV'):
			self.inst_list.get('GUV').return_id()
		'''
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
				self.pass_wl=new_position
				
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
					self.set_posA()
					
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
							
							self.update_end_vals = False
							obj = self.read_signals()
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
						self.update_end_vals = True
						_ = self.read_signals(obj)
						
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
						
						self.update_end_vals = False
						obj = self.read_signals()
						
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
						self.update_end_vals = True
						_ = self.read_signals(obj)
						
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
						self.update_end_vals = True
						_ = self.read_signals()
						
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
					self.set_posB()
					
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
							
							self.update_end_vals = False
							obj = self.read_signals()
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
						self.update_end_vals = True
						_ = self.read_signals(obj)
						
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
						
						self.update_end_vals = False
						obj=self.read_signals()
							
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
						self.update_end_vals = True
						_ = self.read_signals(obj)
						
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
						self.update_end_vals = True
						_ = self.read_signals()
						
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
					self.set_posA()
					
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
							
							self.update_end_vals = False
							obj = self.read_signals()
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
						self.update_end_vals = True
						_ = self.read_signals(obj)
						
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
						
						self.update_end_vals = False
						obj=self.read_signals()
						
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
						self.update_end_vals = True
						_ = self.read_signals(obj)
						
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
						self.update_end_vals = True
						_ = self.read_signals()
						
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
					self.set_posB()
					
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
							
							self.update_end_vals = False
							obj = self.read_signals()
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
						self.update_end_vals = True
						_ = self.read_signals(obj)
						
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
						
						self.update_end_vals = False
						obj=self.read_signals()
						
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
						self.update_end_vals = True
						_ = self.read_signals(obj)
						
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
						self.update_end_vals = True
						_ = self.read_signals()
						
						self.close_shutter()
					
		# Close the shutter and prevent light from coming out
		self.close_shutter()
		
		
	def read_signals(self,*tupl):
		
		# First wait according to the specified delay for position A and position B
		if self.inst_list.get('Oriel'):
			if self.mirrorPos=="A":
				time_start_=time.time()
				while (time.time()-time_start_)<self.posA_delay and not self.abort_flag:
					time.sleep(0.01)
			elif self.mirrorPos=="B":
				time_start_=time.time()
				while (time.time()-time_start_)<self.posB_delay and not self.abort_flag:
					time.sleep(0.01)
		else:
			time_start_=time.time()
			while (time.time()-time_start_)<self.posB_delay and not self.abort_flag:
				time.sleep(0.01)
		
		self.signals.update_movie.emit('stop')
		
		# Start reading the data signals from the instruments
		if tupl:
			tupl, = tupl
		
		V_k2001a=None
		V_a34972a=None
		V_guv=None
		
		time_start_=time.time()
		# while dwelling record voltages, then get the last recoreded voltage and pass it
		while (time.time()-time_start_)<self.dwell and not self.abort_flag:
			time_elap=format(time.time()-self.time_start, '07.2f')
			
			if self.inst_list.get('K2001A'):
				V_k2001a=format(self.inst_list.get('K2001A').return_voltage(self.pass_wl),'.6e')
				self.signals.update_all_k2001a.emit([V_k2001a,time_elap])
			if self.inst_list.get('A34972A'):
				V_a34972a=format(self.inst_list.get('A34972A').return_voltage(self.pass_wl),'.6e')
				self.signals.update_all_a34972a.emit([V_a34972a,time_elap])
			if self.inst_list.get('GUV'):
				V_guv = self.inst_list.get('GUV').return_powden(self.pass_wl)
				V_guv=[float(j) for j in [format(i,'.6e') for i in V_guv]]
				self.signals.update_all_guv.emit([V_guv,time_elap])
			if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
				self.signals.update_wl_time.emit([self.step_wl,time_elap])
				if [V_k2001a,V_a34972a,V_guv]==[None,None,None]:
					time.sleep(0.1)
				
				
		if V_k2001a is not None:
			val=[]
			for i in range(self.avgpts):
				val.extend([self.inst_list.get('K2001A').return_voltage(self.pass_wl)])
				if self.abort_flag:
					self.close_shutter()
					return
			V_k2001a=float(format(numpy.mean(val),'.6e'))
			if tupl:
				if tupl.get('V_k2001a') is not None:
					dark_vals = float(tupl.get('V_k2001a'))
					V_k2001a = float(format(V_k2001a-dark_vals,'.6e'))
					
			if self.update_end_vals:
				if self.inst_list.get('MS257_in') and self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_k2001a.emit([self.ms257_in,self.ms257_out,self.step_wl,V_k2001a,time_elap,self.dateandtime(),self.my_legend])
				elif self.inst_list.get('MS257_in') and not self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_k2001a.emit([self.ms257_in, str(None), self.step_wl,V_k2001a,time_elap,self.dateandtime(),self.my_legend])
				elif not self.inst_list.get('MS257_in') and self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_k2001a.emit([str(None), self.ms257_out, self.step_wl,V_k2001a,time_elap,self.dateandtime(),self.my_legend])
					
					
		if V_a34972a is not None:
			val=[]
			for i in range(self.avgpts):
				val.extend([self.inst_list.get('A34972A').return_voltage(self.pass_wl)])
				if self.abort_flag:
					self.close_shutter()
					return
			V_a34972a=float(format(numpy.mean(val),'.6e'))
			
			if tupl:
				if tupl.get('V_a34972a') is not None:
					dark_vals = float(tupl.get('V_a34972a'))
					V_a34972a = float(format(V_a34972a-dark_vals,'.6e'))
					
			if self.update_end_vals:
				if self.inst_list.get('MS257_in') and self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_a34972a.emit([self.ms257_in,self.ms257_out,self.step_wl,V_a34972a,time_elap,self.dateandtime(),self.my_legend])
				elif self.inst_list.get('MS257_in') and not self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_a34972a.emit([self.ms257_in, str(None), self.step_wl,V_a34972a,time_elap,self.dateandtime(),self.my_legend])
				elif not self.inst_list.get('MS257_in') and self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_a34972a.emit([str(None),self.ms257_out,self.step_wl,V_a34972a,time_elap,self.dateandtime(),self.my_legend])
			
			
		if V_guv is not None:
			val=[]
			for i in range(self.avgpts):
				Vguv = self.inst_list.get('GUV').return_powden(self.pass_wl)
				val.append(Vguv)
				if self.abort_flag:
					self.close_shutter()
					return
			V_guv=[float(format(i,'.6e')) for i in numpy.mean(val,axis=0)]
			
			if tupl:
				if tupl.get('V_guv') is not None:
					dark_vals = [float(i) for i in tupl.get('V_guv')]
					V_guv = numpy.array(V_guv)-numpy.array(dark_vals)
				
			if self.update_end_vals:
				if self.inst_list.get('MS257_in') and self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_guv.emit([self.ms257_in,self.ms257_out,self.step_wl,V_guv,time_elap,self.dateandtime(),self.my_legend])
				elif self.inst_list.get('MS257_in') and not self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_guv.emit([self.ms257_in, str(None), self.step_wl,V_guv,time_elap,self.dateandtime(),self.my_legend])
				elif not self.inst_list.get('MS257_in') and self.inst_list.get('MS257_out'):
					time_elap=format(time.time()-self.time_start, '07.2f')
					self.signals.update_end_guv.emit([str(None), self.ms257_out,self.step_wl,V_guv,time_elap,self.dateandtime(),self.my_legend])
					
		tupl={'V_k2001a':V_k2001a, 'V_a34972a':V_a34972a , 'V_guv':V_guv}
		return tupl
		
		
	def close_shutter(self):
		
		if self.inst_list.get('MS257_in') and hasattr(self,'light'):
			if not self.light==False:
				self.inst_list.get('MS257_in').setSHUTTER("on")
				self.signals.update_shutter.emit("on")
				print("Shutter on - DARK")
				self.light=False
				
		elif self.inst_list.get('MS257_in'):
			self.inst_list.get('MS257_in').setSHUTTER("on")
			self.signals.update_shutter.emit("on")
			print("Shutter on - DARK")
			self.light=False
			
			
	def open_shutter(self):
		
		if self.inst_list.get('MS257_in') and hasattr(self,'light'):
			if not self.light==True:
				self.inst_list.get('MS257_in').setSHUTTER("off")
				self.signals.update_shutter.emit("off")
				print("Shutter off - LIGHT")
				self.light=True
				
		elif self.inst_list.get('MS257_in'):
			self.inst_list.get('MS257_in').setSHUTTER("off")
			self.signals.update_shutter.emit("off")
			print("Shutter off - LIGHT")
			self.light=True
			
			
	def set_posA(self):
		
		self.avgpts=self.avgpts_a
		
		if self.inst_list.get('Oriel') and hasattr(self,'mirrorPos'):
			if not self.mirrorPos=="A":
				# close the shutter before moving the mirror to position A
				self.close_shutter()
				# move the mirror to position A
				self.inst_list.get('Oriel').goto_a()
				# wait until the movement is finished
				time_start_=time.time()
				while (time.time()-time_start_)<self.posAB_delay and not self.abort_flag:
					time.sleep(0.05)
				self.signals.update_oriel.emit("A")
				print("Mirror position A")
				self.mirrorPos="A"
				
		elif self.inst_list.get('Oriel'):
			# close the shutter before moving the mirror to position A
			self.close_shutter()
			# move the mirror to position A
			self.inst_list.get('Oriel').goto_a()
			# wait until the movement is finished
			time_start_=time.time()
			while (time.time()-time_start_)<self.posAB_delay and not self.abort_flag:
				time.sleep(0.05)
			self.signals.update_oriel.emit("A")
			print("Mirror position A")
			self.mirrorPos="A"
			
			
	def set_posB(self):
		
		self.avgpts=self.avgpts_b
		
		if self.inst_list.get('Oriel') and hasattr(self,'mirrorPos'):
			if not self.mirrorPos=="B":
				# close the shutter before moving the mirror to position B
				self.close_shutter()
				# move the mirror to position B
				self.inst_list.get('Oriel').goto_b()
				# wait until the movement is finished
				time_start_=time.time()
				while (time.time()-time_start_)<self.posAB_delay and not self.abort_flag:
					time.sleep(0.05)
				self.signals.update_oriel.emit("B")
				print("Mirror position B")
				self.mirrorPos="B"
				
		elif self.inst_list.get('Oriel'):
			# close the shutter before moving the mirror to position B
			self.close_shutter()
			# move the mirror to position B
			self.inst_list.get('Oriel').goto_b()
			# wait until the movement is finished
			time_start_=time.time()
			while (time.time()-time_start_)<self.posAB_delay and not self.abort_flag:
				time.sleep(0.05)
			self.signals.update_oriel.emit("B")
			print("Mirror position B")
			self.mirrorPos="B"
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
					
