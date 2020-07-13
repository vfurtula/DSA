#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""



import os, re, serial, time, yagmail, configparser

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QCheckBox, QLabel, QLineEdit, QComboBox, QFrame, QVBoxLayout, QHBoxLayout, QMenuBar, QPushButton)

import MS257, K2001A, Agilent34972A, Oriel_stepper, GUV






class Instruments_dialog(QDialog):
	
	def __init__(self, parent, inst_list, timer):
		super().__init__(parent)
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
			
			self.ms257inport_str=self.config.get('DEFAULT','ms257inport').strip().split(',')[0]
			self.ms257inport_check=self.bool_(self.config.get('DEFAULT','ms257inport').strip().split(',')[1])
			self.ms257outport_str=self.config.get('DEFAULT','ms257outport').strip().split(',')[0]
			self.ms257outport_check=self.bool_(self.config.get('DEFAULT','ms257outport').strip().split(',')[1])
			self.k2001aport_str=self.config.get('DEFAULT','k2001aport').strip().split(',')[0]
			self.k2001aport_check=self.bool_(self.config.get('DEFAULT','k2001aport').strip().split(',')[1])
			self.a34972aport_str=self.config.get('DEFAULT','a34972aport').strip().split(',')[0]
			self.a34972aport_check=self.bool_(self.config.get('DEFAULT','a34972aport').strip().split(',')[1])
			self.testmode_check=self.bool_(self.config.get('DEFAULT','testmode'))
			self.guvip_str=self.config.get('DEFAULT','guvport').strip().split(',')[0]
			self.guvport_str=self.config.get('DEFAULT','guvport').strip().split(',')[1]
			self.guvport_check=self.bool_(self.config.get('DEFAULT','guvport').strip().split(',')[2])
			self.guvtype_str=self.config.get('DEFAULT','guvtype')
			self.orielport_str=self.config.get('DEFAULT','orielport').strip().split(',')[0]
			self.orielport_check=self.bool_(self.config.get('DEFAULT','orielport').strip().split(',')[1])
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
			
		
		# Enable antialiasing for prettier plots
		self.inst_list = inst_list
		self.timer = timer
		self.initUI()
		
		
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
		
	def initUI(self):
		
		empty_string = QLabel("",self)
		
		ims257_lbl = QLabel("Input MS257 serial port",self)
		ims257_lbl.setStyleSheet("color: blue")
		self.ims257Edit = QLineEdit(self.ms257inport_str,self)
		self.ims257Edit.textChanged.connect(self.on_text_changed)
		self.ims257Edit.setEnabled(self.ms257inport_check)
		self.ims257Edit.setFixedWidth(325)
		self.cb_ims257 = QCheckBox('',self)
		self.cb_ims257.toggle()
		self.cb_ims257.setChecked(self.ms257inport_check)
		self.ims257_status = QLabel("",self)
		
		oms257_lbl = QLabel("Output MS257 serial port",self)
		oms257_lbl.setStyleSheet("color: blue")
		self.oms257Edit = QLineEdit(self.ms257outport_str,self)
		self.oms257Edit.textChanged.connect(self.on_text_changed)
		self.oms257Edit.setEnabled(self.ms257outport_check)
		self.oms257Edit.setFixedWidth(325)
		self.cb_oms257 = QCheckBox('',self)
		self.cb_oms257.toggle()
		self.cb_oms257.setChecked(self.ms257outport_check)
		self.oms257_status = QLabel("",self)
		
		oriel_lbl = QLabel("Oriel stepper seriel port",self)
		oriel_lbl.setStyleSheet("color: blue")
		self.orielEdit = QLineEdit(self.orielport_str,self)
		self.orielEdit.textChanged.connect(self.on_text_changed)
		self.orielEdit.setEnabled(self.orielport_check)
		self.orielEdit.setFixedWidth(325)
		self.cb_oriel = QCheckBox('',self)
		self.cb_oriel.toggle()
		self.cb_oriel.setChecked(self.orielport_check)
		self.oriel_status = QLabel("",self)
		
		k2001a_lbl = QLabel("Keythley K2001A GPIB port",self)
		k2001a_lbl.setStyleSheet("color: blue")
		self.k2001aEdit = QLineEdit(self.k2001aport_str,self)
		self.k2001aEdit.textChanged.connect(self.on_text_changed)
		self.k2001aEdit.setEnabled(self.k2001aport_check)
		self.k2001aEdit.setFixedWidth(325)
		self.cb_k2001a = QCheckBox('',self)
		self.cb_k2001a.toggle()
		self.cb_k2001a.setChecked(self.k2001aport_check)
		self.k2001a_status = QLabel("",self)
		
		a34972a_lbl = QLabel("Agilent 34972A USB port",self)
		a34972a_lbl.setStyleSheet("color: blue")
		self.a34972aEdit = QLineEdit(self.a34972aport_str,self)
		self.a34972aEdit.textChanged.connect(self.on_text_changed)
		self.a34972aEdit.setEnabled(self.a34972aport_check)
		self.a34972aEdit.setFixedWidth(325)
		self.cb_a34972a = QCheckBox('',self)
		self.cb_a34972a.toggle()
		self.cb_a34972a.setChecked(self.a34972aport_check)
		self.a34972a_status = QLabel("",self)
		
		guvip_lbl = QLabel("GUV TCP/IP",self)
		guvip_lbl.setStyleSheet("color: blue")
		self.guvipEdit = QLineEdit(self.guvip_str,self)
		self.guvipEdit.textChanged.connect(self.on_text_changed)
		self.guvipEdit.setEnabled(self.guvport_check)
		self.guvipEdit.setFixedWidth(125)
		guvport_lbl = QLabel("GUV TCP port",self)
		guvport_lbl.setStyleSheet("color: blue")
		self.guvportEdit = QLineEdit(self.guvport_str,self)
		self.guvportEdit.textChanged.connect(self.on_text_changed)
		self.guvportEdit.setEnabled(self.guvport_check)
		self.guvportEdit.setFixedWidth(100)
		self.cb_guv = QCheckBox('',self)
		self.cb_guv.toggle()
		self.cb_guv.setChecked(self.guvport_check)
		guvtype_lbl = QLabel("GUV type",self)
		guvtype_lbl.setStyleSheet("color: blue")
		self.guvtype_cb = QComboBox(self)
		mylist=["GUV-541","GUV-2511","GUV-3511"]
		self.guvtype_cb.addItems(mylist)
		self.guvtype_cb.setCurrentIndex(mylist.index(self.guvtype_str))
		self.guvtype_cb.setEnabled(self.guvport_check)
		self.guvtype_cb.setFixedWidth(100)
		self.guv_status = QLabel("",self)
		
		testmode_lbl = QLabel("Connect instruments in the TEST mode",self)
		testmode_lbl.setStyleSheet("color: magenta")
		self.cb_testmode = QCheckBox('',self)
		self.cb_testmode.toggle()
		self.cb_testmode.setChecked(self.testmode_check)
		
		self.connButton = QPushButton("Connect to selected ports",self)
		#self.connButton.setFixedWidth(150)
		
		self.saveButton = QPushButton("Save settings",self)
		self.saveButton.setEnabled(False)
		#self.saveButton.setFixedWidth(150)
		
		self.closeButton = QPushButton("CLOSE",self)
		self.closeButton.setEnabled(True)
		
		##############################################
		
		# Add all widgets
		g0_0 = QGridLayout()
		
		g0_0.addWidget(ims257_lbl,0,0)
		g0_0.addWidget(self.cb_ims257,0,1)
		g0_0.addWidget(self.ims257Edit,1,0)
		g0_0.addWidget(self.ims257_status,2,0)
		g0_0.addWidget(empty_string,3,0)
		
		g0_0.addWidget(oms257_lbl,4,0)
		g0_0.addWidget(self.cb_oms257,4,1)
		g0_0.addWidget(self.oms257Edit,5,0)
		g0_0.addWidget(self.oms257_status,6,0)
		g0_0.addWidget(empty_string,7,0)
		
		g0_0.addWidget(oriel_lbl,8,0)
		g0_0.addWidget(self.cb_oriel,8,1)
		g0_0.addWidget(self.orielEdit,9,0)
		g0_0.addWidget(self.oriel_status,10,0)
		g0_0.addWidget(empty_string,11,0)
		
		g0_0.addWidget(k2001a_lbl,12,0)
		g0_0.addWidget(self.cb_k2001a,12,1)
		g0_0.addWidget(self.k2001aEdit,13,0)
		g0_0.addWidget(self.k2001a_status,14,0)
		g0_0.addWidget(empty_string,15,0)
		
		g0_0.addWidget(a34972a_lbl,16,0)
		g0_0.addWidget(self.cb_a34972a,16,1)
		g0_0.addWidget(self.a34972aEdit,17,0)
		g0_0.addWidget(self.a34972a_status,18,0)
		g0_0.addWidget(empty_string,19,0)
		
		g0_1 = QGridLayout()
		g0_1.addWidget(guvip_lbl,0,0)
		g0_1.addWidget(guvport_lbl,0,1)
		g0_1.addWidget(guvtype_lbl,0,2)
		g0_1.addWidget(self.guvipEdit,1,0)
		g0_1.addWidget(self.guvportEdit,1,1)
		g0_1.addWidget(self.guvtype_cb,1,2)
		
		g0_0.addLayout(g0_1,20,0)
		g0_0.addWidget(self.cb_guv,20,1)
		g0_0.addWidget(self.guv_status,22,0)
		g0_0.addWidget(empty_string,23,0)
		
		g0_0.addWidget(testmode_lbl,24,0)
		g0_0.addWidget(self.cb_testmode,24,1)
		
		g1_0 = QGridLayout()
		g1_0.addWidget(self.connButton,0,0)
		g1_0.addWidget(self.saveButton,0,1)
		
		g2_0 = QGridLayout()
		g2_0.addWidget(self.closeButton,0,0)
		
		v0 = QVBoxLayout()
		v0.addLayout(g0_0)
		v0.addLayout(g1_0)
		v0.addLayout(g2_0)
		
		self.setLayout(v0) 
    
    ##############################################
	
		# run the main script
		self.connButton.clicked.connect(self.set_connect)
		self.saveButton.clicked.connect(self.save_)
		self.closeButton.clicked.connect(self.close_)
		
		self.cb_ims257.stateChanged.connect(self.ims257_stch)
		self.cb_oms257.stateChanged.connect(self.oms257_stch)
		self.cb_k2001a.stateChanged.connect(self.k2001a_stch)
		self.cb_oriel.stateChanged.connect(self.oriel_stch)
		self.cb_a34972a.stateChanged.connect(self.a34972a_stch)
		self.cb_guv.stateChanged.connect(self.guv_stch)
		self.guvtype_cb.activated[str].connect(self.onActivatedGUV)
		
		##############################################
		
		# Connection warnings
		if self.inst_list.get("MS257_in") and not self.inst_list.get("MS257_in_tm"):
			self.ims257_status.setText("Status: CONNECTED")
			self.ims257_status.setStyleSheet("color: green")
		elif self.inst_list.get("MS257_in") and self.inst_list.get("MS257_in_tm"):
			self.ims257_status.setText("Status: CONNECTED in TESTMODE")
			self.ims257_status.setStyleSheet("color: magenta")
		else:
			self.ims257_status.setText("Status: unknown")
			self.ims257_status.setStyleSheet("color: black")
			
		if self.inst_list.get("MS257_out") and not self.inst_list.get("MS257_out_tm"):
			self.oms257_status.setText("Status: CONNECTED")
			self.oms257_status.setStyleSheet("color: green")
		elif self.inst_list.get("MS257_out") and self.inst_list.get("MS257_out_tm"):
			self.oms257_status.setText("Status: CONNECTED in TESTMODE")
			self.oms257_status.setStyleSheet("color: magenta")
		else:
			self.oms257_status.setText("Status: unknown")
			self.oms257_status.setStyleSheet("color: black")
		
		if self.inst_list.get("Oriel") and not self.inst_list.get("Oriel_tm"):
			self.oriel_status.setText("Status: CONNECTED")
			self.oriel_status.setStyleSheet("color: green")
		elif self.inst_list.get("Oriel") and self.inst_list.get("Oriel_tm"):
			self.oriel_status.setText("Status: CONNECTED in TESTMODE")
			self.oriel_status.setStyleSheet("color: magenta")
		else:
			self.oriel_status.setText("Status: unknown")
			self.oriel_status.setStyleSheet("color: black")
		
		if self.inst_list.get("K2001A") and not self.inst_list.get("K2001A_tm"):
			self.k2001a_status.setText("Status: CONNECTED")
			self.k2001a_status.setStyleSheet("color: green")
		elif self.inst_list.get("K2001A") and self.inst_list.get("K2001A_tm"):
			self.k2001a_status.setText("Status: CONNECTED in TESTMODE")
			self.k2001a_status.setStyleSheet("color: magenta")
		else:
			self.k2001a_status.setText("Status: unknown")
			self.k2001a_status.setStyleSheet("color: black")
		
		if self.inst_list.get("Agilent34972A") and not self.inst_list.get("Agilent34972A_tm"):
			self.a34972a_status.setText("Status: CONNECTED")
			self.a34972a_status.setStyleSheet("color: green")
		elif self.inst_list.get("Agilent34972A") and self.inst_list.get("Agilent34972A_tm"):
			self.a34972a_status.setText("Status: CONNECTED in TESTMODE")
			self.a34972a_status.setStyleSheet("color: magenta")
		else:
			self.a34972a_status.setText("Status: unknown")
			self.a34972a_status.setStyleSheet("color: black")
		
		if self.inst_list.get("GUV") and not self.inst_list.get("GUV_tm"):
			self.guv_status.setText("Status: CONNECTED")
			self.guv_status.setStyleSheet("color: green")
		elif self.inst_list.get("GUV") and self.inst_list.get("GUV_tm"):
			self.guv_status.setText("Status: CONNECTED in TESTMODE")
			self.guv_status.setStyleSheet("color: magenta")
		else:
			self.guv_status.setText("Status: unknown")
			self.guv_status.setStyleSheet("color: black")
			
		##############################################
		
		# Check boxes
		'''
		if not self.checked_list.get("MS257_in"):
			self.cb_ims257.setChecked(False)
		
		if not self.checked_list.get("MS257_out"):
			self.cb_oms257.setChecked(False)
		
		if not self.checked_list.get("Oriel"):
			self.cb_oriel.setChecked(False)
		
		if not self.checked_list.get("K2001A"):
			self.cb_k2001a.setChecked(False)
		
		if not self.checked_list.get("Agilent34972A"):
			self.cb_a34972a.setChecked(False)
		
		if not self.checked_list.get("GUV"):
			self.cb_guv.setChecked(False)
		'''
		
		self.setWindowTitle("Pick-up instruments and connect")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
	def onActivatedGUV(self, text):
		
		if str(text)!=self.guvtype_str:
			self.on_text_changed()
			
		self.guvtype_str = str(text)
	
	def ims257_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.ims257Edit.setEnabled(True)
		else:
			self.ims257Edit.setEnabled(False)
		
		
	def oms257_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.oms257Edit.setEnabled(True)
		else:
			self.oms257Edit.setEnabled(False)
		
		
	def k2001a_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.k2001aEdit.setEnabled(True)
		else:
			self.k2001aEdit.setEnabled(False)
			
			
	def oriel_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.orielEdit.setEnabled(True)
		else:
			self.orielEdit.setEnabled(False)
			
			
	def a34972a_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.a34972aEdit.setEnabled(True)
		else:
			self.a34972aEdit.setEnabled(False)
			
	def guv_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.guvportEdit.setEnabled(True)
			self.guvipEdit.setEnabled(True)
			self.guvtype_cb.setEnabled(True)
		else:
			self.guvportEdit.setEnabled(False)
			self.guvipEdit.setEnabled(False)
			self.guvtype_cb.setEnabled(False)
			
	def on_text_changed(self):
		
		self.saveButton.setText("*Save settings*")
		self.saveButton.setEnabled(True)
		
		
	def set_connect(self):
		
		##########################################
		
		if self.cb_testmode.isChecked():
			
			if self.cb_ims257.isChecked():
				self.MS257_in = MS257.MS257(self.ms257inport_str, True)
				self.ims257_status.setText("Status: TEST MODE activated.")
				self.ims257_status.setStyleSheet("color: magenta")
				self.inst_list.update({'MS257_in':self.MS257_in})
				self.inst_list.update({'MS257_in_tm':True})
			else:
				self.inst_list.pop('MS257_in', None)
				self.ims257_status.setText("Status: No device connected!")
				self.ims257_status.setStyleSheet("color: red")
					
			##########################################
			
			if self.cb_oms257.isChecked():
				self.MS257_out = MS257.MS257(self.ms257outport_str, True)
				self.oms257_status.setText("Status: TEST MODE activated.")
				self.oms257_status.setStyleSheet("color: magenta")
				self.inst_list.update({'MS257_out':self.MS257_out})
				self.inst_list.update({'MS257_out_tm':True})
			else:
				self.inst_list.pop('MS257_out', None)
				self.oms257_status.setText("Status: No device connected!")
				self.oms257_status.setStyleSheet("color: red")
					
			##########################################
			
			if self.cb_oriel.isChecked():
				self.Oriel = Oriel_stepper.Oriel_stepper(self.orielport_str, True)
				self.oriel_status.setText("Status: TEST MODE activated.")
				self.oriel_status.setStyleSheet("color: magenta")
				self.inst_list.update({'Oriel':self.Oriel})
				self.inst_list.update({'Oriel_tm':True})
			else:
				self.inst_list.pop('Oriel', None)
				self.oriel_status.setText("Status: No device connected!")
				self.oriel_status.setStyleSheet("color: red")
			
			##########################################
			
			if self.cb_k2001a.isChecked():
				self.K2001A = K2001A.K2001A(self.k2001aport_str, True)
				self.k2001a_status.setText("Status: TEST MODE activated.")
				self.k2001a_status.setStyleSheet("color: magenta")
				self.inst_list.update({'K2001A':self.K2001A})
				self.inst_list.update({'K2001A_tm':True})
			else:
				self.inst_list.pop('K2001A', None)
				self.k2001a_status.setText("Status: No device connected!")
				self.k2001a_status.setStyleSheet("color: red")
			
			##########################################
			
			if self.cb_a34972a.isChecked():
				self.Agilent34972A = Agilent34972A.Agilent34972A(self.a34972aport_str, True)
				self.a34972a_status.setText("Status: TEST MODE activated.")
				self.a34972a_status.setStyleSheet("color: magenta")
				self.inst_list.update({'Agilent34972A':self.Agilent34972A})
				self.inst_list.update({'Agilent34972A_tm':True})
			else:
				self.inst_list.pop('Agilent34972A', None)
				self.a34972a_status.setText("Status: No device connected!")
				self.a34972a_status.setStyleSheet("color: red")
				
			##########################################
			
			if self.cb_guv.isChecked():
				self.GUV = GUV.GUV([self.guvip_str,self.guvport_str,self.guvtype_str],True)
				self.guv_status.setText("Status: TEST MODE activated.")
				self.guv_status.setStyleSheet("color: magenta")
				self.inst_list.update({'GUV':self.GUV})
				self.inst_list.update({'GUV_tm':True})
			else:
				self.inst_list.pop('GUV', None)
				self.guv_status.setText("Status: No device connected!")
				self.guv_status.setStyleSheet("color: red")
					
			##########################################
			
			if not bool(self.inst_list):
				QMessageBox.critical(self, 'Message',"No instruments connected. At least 1 instrument is required.")
			else:
				self.save_()
				
		else:
			
			if self.cb_ims257.isChecked():
				try:
					self.MS257_in = MS257.MS257(self.ms257inport_str, False)
					self.MS257_in.set_timeout(1)
					
					print("MS257 input monochromator version number ", self.MS257_in.getVersion())
					self.MS257_in.set_timeout(60)
					self.ims257_status.setText("Status: CONNECTED")
					self.ims257_status.setStyleSheet("color: green")
					self.inst_list.update({'MS257_in':self.MS257_in})
					self.inst_list.update({'MS257_in_tm':False})
				except Exception as e:
					reply = QMessageBox.critical(self, 'MS257 input TEST MODE', ''.join(["MS257 input monochromator could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nProceed into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
					if reply == QMessageBox.Yes:
						self.MS257_in = MS257.MS257(self.ms257inport_str, True)
						self.ims257_status.setText("Status: No device detected! TEST MODE activated.")
						self.ims257_status.setStyleSheet("color: magenta")
						self.inst_list.update({'MS257_in':self.MS257_in})
						self.inst_list.update({'MS257_in_tm':True})
					else:
						if self.inst_list.get("MS257_in"):
							if self.inst_list.get("MS257_in").is_open():
								self.inst_list.get("MS257_in").close()
							self.inst_list.pop('MS257_in', None)
							self.ims257_status.setText("Status: No device connected!")
							self.ims257_status.setStyleSheet("color: red")
			else:
				if self.inst_list.get("MS257_in"):
					if self.inst_list.get("MS257_in").is_open():
						self.inst_list.get("MS257_in").close()
					self.inst_list.pop('MS257_in', None)
					self.ims257_status.setText("Status: No device connected!")
					self.ims257_status.setStyleSheet("color: red")
					
			##########################################
			
			if self.cb_oms257.isChecked():
				try:
					self.MS257_out = MS257.MS257(self.ms257outport_str, False)
					self.MS257_out.set_timeout(1)
					
					print("MS257 output monochromator version number ", self.MS257_out.getVersion())
					self.MS257_out.set_timeout(60)
					self.oms257_status.setText("Status: CONNECTED")
					self.oms257_status.setStyleSheet("color: green")
					self.inst_list.update({'MS257_out':self.MS257_out})
					self.inst_list.update({'MS257_out_tm':False})
				except Exception as e:
					reply = QMessageBox.critical(self, 'MS257 output TEST MODE', ''.join(["MS257 output monochromator could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nProceed into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
					if reply == QMessageBox.Yes:
						self.MS257_out = MS257.MS257(self.ms257outport_str, True)
						self.oms257_status.setText("Status: No device detected! TEST MODE activated.")
						self.oms257_status.setStyleSheet("color: magenta")
						self.inst_list.update({'MS257_out':self.MS257_out})
						self.inst_list.update({'MS257_out_tm':True})
					else:
						if self.inst_list.get("MS257_out"):
							if self.inst_list.get("MS257_out").is_open():
								self.inst_list.get("MS257_out").close()
							self.inst_list.pop('MS257_out', None)
							self.oms257_status.setText("Status: No device connected!")
							self.oms257_status.setStyleSheet("color: red")
			else:
				if self.inst_list.get("MS257_out"):
					if self.inst_list.get("MS257_out").is_open():
						self.inst_list.get("MS257_out").close()
					self.inst_list.pop('MS257_out', None)
					self.oms257_status.setText("Status: No device connected!")
					self.oms257_status.setStyleSheet("color: red")
					
			##########################################
			
			if self.cb_oriel.isChecked():
				try:
					self.Oriel = Oriel_stepper.Oriel_stepper(self.orielport_str, False)
					self.Oriel.set_timeout(1)
					
					print("Oriel position A: ", self.Oriel.return_ta())
					print("Oriel position B: ", self.Oriel.return_tb())
					self.Oriel.set_timeout(60)
					self.oriel_status.setText("Status: CONNECTED")
					self.oriel_status.setStyleSheet("color: green")
					self.inst_list.update({'Oriel':self.Oriel})
					self.inst_list.update({'Oriel_tm':False})
				except Exception as e:
					reply = QMessageBox.critical(self, 'Oriel stepper TEST MODE', ''.join(["Oriel stepper could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nProceed into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
					if reply == QMessageBox.Yes:
						self.Oriel = Oriel_stepper.Oriel_stepper(self.orielport_str, True)
						self.oriel_status.setText("Status: No device detected! TEST MODE activated.")
						self.oriel_status.setStyleSheet("color: magenta")
						self.inst_list.update({'Oriel':self.Oriel})
						self.inst_list.update({'Oriel_tm':True})
					else:
						if self.inst_list.get("Oriel"):
							if self.inst_list.get("Oriel").is_open():
								self.inst_list.get("Oriel").close()
							self.inst_list.pop('Oriel', None)
							self.oriel_status.setText("Status: No device connected!")
							self.oriel_status.setStyleSheet("color: red")
			else:
				if self.inst_list.get("Oriel"):
					if self.inst_list.get("Oriel").is_open():
						self.inst_list.get("Oriel").close()
					self.inst_list.pop('Oriel', None)
					self.oriel_status.setText("Status: No device connected!")
					self.oriel_status.setStyleSheet("color: red")
			
			##########################################
			
			if self.cb_k2001a.isChecked():
				try:
					self.K2001A = K2001A.K2001A(self.k2001aport_str, False)
					
					print(self.K2001A.return_id())
					self.k2001a_status.setText("Status: CONNECTED")
					self.k2001a_status.setStyleSheet("color: green")
					self.inst_list.update({'K2001A':self.K2001A})
					self.inst_list.update({'K2001A_tm':False})
				except Exception as e:
					reply = QMessageBox.critical(self, 'Keithley 2001A TEST MODE', ''.join(["Keithley 2001A could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nProceed into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
					if reply == QMessageBox.Yes:
						self.K2001A = K2001A.K2001A(self.k2001aport_str, True)
						self.k2001a_status.setText("Status: No device detected! TEST MODE activated.")
						self.k2001a_status.setStyleSheet("color: magenta")
						self.inst_list.update({'K2001A':self.K2001A})
						self.inst_list.update({'K2001A_tm':True})
					else:
						if self.inst_list.get("K2001A"):
							if self.inst_list.get("K2001A").is_open():
								self.inst_list.get("K2001A").close()
							self.inst_list.pop('K2001A', None)
							self.k2001a_status.setText("Status: No device connected!")
							self.k2001a_status.setStyleSheet("color: red")
			else:
				if self.inst_list.get("K2001A"):
					if self.inst_list.get("K2001A").is_open():
						self.inst_list.get("K2001A").close()
					self.inst_list.pop('K2001A', None)
					self.k2001a_status.setText("Status: No device connected!")
					self.k2001a_status.setStyleSheet("color: red")
			
			##########################################
			
			if self.cb_a34972a.isChecked():
				try:
					self.Agilent34972A = Agilent34972A.Agilent34972A(self.a34972aport_str, False)
					
					print(self.Agilent34972A.return_id())
					self.a34972a_status.setText("Status: CONNECTED")
					self.a34972a_status.setStyleSheet("color: green")
					self.inst_list.update({'Agilent34972A':self.Agilent34972A})
					self.inst_list.update({'Agilent34972A_tm':False})
				except Exception as e:
					reply = QMessageBox.critical(self, 'Agilent 34972A TEST MODE', ''.join(["Agilent34972A could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nProceed into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
					if reply == QMessageBox.Yes:
						self.Agilent34972A = Agilent34972A.Agilent34972A(self.a34972aport_str, True)
						self.a34972a_status.setText("Status: No device detected! TEST MODE activated.")
						self.a34972a_status.setStyleSheet("color: magenta")
						self.inst_list.update({'Agilent34972A':self.Agilent34972A})
						self.inst_list.update({'Agilent34972A_tm':True})
					else:
						if self.inst_list.get("Agilent34972A"):
							if self.inst_list.get("Agilent34972A").is_open():
								self.inst_list.get("Agilent34972A").close()
							self.inst_list.pop('Agilent34972A', None)
							self.a34972a_status.setText("Status: No device connected!")
							self.a34972a_status.setStyleSheet("color: red")
			else:
				if self.inst_list.get("Agilent34972A"):
					if self.inst_list.get("Agilent34972A").is_open():
						self.inst_list.get("Agilent34972A").close()
					self.inst_list.pop('Agilent34972A', None)
					self.a34972a_status.setText("Status: No device connected!")
					self.a34972a_status.setStyleSheet("color: red")
				
			##########################################
			
			if self.cb_guv.isChecked():
				try:
					self.GUV = GUV.GUV([self.guvip_str,self.guvport_str,self.guvtype_str],False)
					
					print(self.GUV.return_id())
					self.guv_status.setText("Status: CONNECTED")
					self.guv_status.setStyleSheet("color: green")
					self.inst_list.update({'GUV':self.GUV})
					self.inst_list.update({'GUV_tm':False})
				except Exception as e:
					reply = QMessageBox.critical(self, ''.join([str(self.guvtype_str),' TEST MODE']), ''.join([self.guvtype_str," could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nProceed into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
					if reply == QMessageBox.Yes:
						self.GUV = GUV.GUV([self.guvip_str,self.guvport_str,self.guvtype_str],True)
						self.guv_status.setText("Status: No device detected! TEST MODE activated.")
						self.guv_status.setStyleSheet("color: magenta")
						self.inst_list.update({'GUV':self.GUV})
						self.inst_list.update({'GUV_tm':True})
					else:
						if self.inst_list.get("GUV"):
							if self.inst_list.get("GUV").is_open():
								self.inst_list.get("GUV").close()
							self.inst_list.pop('GUV', None)
							self.guv_status.setText("Status: No device connected!")
							self.guv_status.setStyleSheet("color: red")
			else:
				if self.inst_list.get("GUV"):
					if self.inst_list.get("GUV").is_open():
						self.inst_list.get("GUV").close()
					self.inst_list.pop('GUV', None)
					self.guv_status.setText("Status: No device connected!")
					self.guv_status.setStyleSheet("color: red")
					
			##########################################
			
			if not bool(self.inst_list):
				QMessageBox.critical(self, 'Message',"No instruments connected. At least 1 instrument is required.")
				return
			else:
				self.save_()
		
		
	def save_(self):
		
		self.config.set('DEFAULT', 'ms257inport', ','.join([str(self.ims257Edit.text()), str(self.cb_ims257.isChecked()) ]) )
		self.config.set('DEFAULT', 'ms257outport', ','.join([str(self.oms257Edit.text()), str(self.cb_oms257.isChecked())]) )
		self.config.set('DEFAULT', 'orielport', ','.join([str(self.orielEdit.text()), str(self.cb_oriel.isChecked()) ]) )
		self.config.set('DEFAULT', 'k2001aport', ','.join([str(self.k2001aEdit.text()), str(self.cb_k2001a.isChecked())]) )
		self.config.set('DEFAULT', 'a34972aport', ','.join([str(self.a34972aEdit.text()), str(self.cb_a34972a.isChecked())]) )
		self.config.set('DEFAULT', 'testmode', str(self.cb_testmode.isChecked()) )
		self.config.set('DEFAULT', 'guvport', ','.join([str(self.guvipEdit.text()), str(self.guvportEdit.text()), str(self.cb_guv.isChecked())]) )
		self.config.set('DEFAULT', 'guvtype', self.guvtype_str)
		
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
		self.saveButton.setText("Settings saved")
		self.saveButton.setEnabled(False)
			
	def close_(self):
		
		self.close()
			
			
	def closeEvent(self,event):
		
		if self.inst_list:
			self.timer.start(1000*60*5)
		event.accept()
	

