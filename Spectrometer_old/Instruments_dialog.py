#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""



import os, re, serial, time, yagmail

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QCheckBox, QLabel, QLineEdit, QComboBox, QFrame, QVBoxLayout, QHBoxLayout, QMenuBar, QPushButton)

import MS257, K2001A, Agilent34972A, Oriel_stepper






class Instruments_dialog(QDialog):
	
	def __init__(self, parent, inst_list, timer, config):
		super().__init__(parent)
		
		# Initial read of the config file
		self.config = config
		
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
		self.ims257_status = QLabel("Status: unknown",self)
		
		oms257_lbl = QLabel("Output MS257 serial port",self)
		oms257_lbl.setStyleSheet("color: blue")
		self.oms257Edit = QLineEdit(self.ms257outport_str,self)
		self.oms257Edit.textChanged.connect(self.on_text_changed)
		self.oms257Edit.setEnabled(self.ms257outport_check)
		self.oms257Edit.setFixedWidth(325)
		self.cb_oms257 = QCheckBox('',self)
		self.cb_oms257.toggle()
		self.cb_oms257.setChecked(self.ms257outport_check)
		self.oms257_status = QLabel("Status: unknown",self)
		
		oriel_lbl = QLabel("Oriel stepper seriel port",self)
		oriel_lbl.setStyleSheet("color: blue")
		self.orielEdit = QLineEdit(self.orielport_str,self)
		self.orielEdit.textChanged.connect(self.on_text_changed)
		self.orielEdit.setEnabled(self.orielport_check)
		self.orielEdit.setFixedWidth(325)
		self.cb_oriel = QCheckBox('',self)
		self.cb_oriel.toggle()
		self.cb_oriel.setChecked(self.orielport_check)
		self.oriel_status = QLabel("Status: unknown",self)
		
		k2001a_lbl = QLabel("Keythley K2001A GPIB port",self)
		k2001a_lbl.setStyleSheet("color: blue")
		self.k2001aEdit = QLineEdit(self.k2001aport_str,self)
		self.k2001aEdit.textChanged.connect(self.on_text_changed)
		self.k2001aEdit.setEnabled(self.k2001aport_check)
		self.k2001aEdit.setFixedWidth(325)
		self.cb_k2001a = QCheckBox('',self)
		self.cb_k2001a.toggle()
		self.cb_k2001a.setChecked(self.k2001aport_check)
		self.k2001a_status = QLabel("Status: unknown",self)
		
		a34972a_lbl = QLabel("Agilent 34972A USB port",self)
		a34972a_lbl.setStyleSheet("color: blue")
		self.a34972aEdit = QLineEdit(self.a34972aport_str,self)
		self.a34972aEdit.textChanged.connect(self.on_text_changed)
		self.a34972aEdit.setEnabled(self.a34972aport_check)
		self.a34972aEdit.setFixedWidth(325)
		self.cb_a34972a = QCheckBox('',self)
		self.cb_a34972a.toggle()
		self.cb_a34972a.setChecked(self.a34972aport_check)
		self.a34972a_status = QLabel("Status: unknown",self)
		
		self.connButton = QPushButton("Connect to selected ports",self)
		#self.connButton.setFixedWidth(150)
		
		self.saveButton = QPushButton("Save settings",self)
		self.saveButton.setEnabled(False)
		#self.saveButton.setFixedWidth(150)
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
		
		g1_0 = QGridLayout()
		g1_0.addWidget(self.connButton,0,0)
		g1_0.addWidget(self.saveButton,0,1)
		
		v0 = QVBoxLayout()
		v0.addLayout(g0_0)
		v0.addLayout(g1_0)
		
		self.setLayout(v0) 
    
    ##############################################
	
		# run the main script
		self.connButton.clicked.connect(self.set_connect)
		self.saveButton.clicked.connect(self.save_)
		
		self.cb_ims257.stateChanged.connect(self.ims257_stch)
		self.cb_oms257.stateChanged.connect(self.oms257_stch)
		self.cb_k2001a.stateChanged.connect(self.k2001a_stch)
		self.cb_oriel.stateChanged.connect(self.oriel_stch)
		self.cb_a34972a.stateChanged.connect(self.a34972a_stch)
		
		##############################################
		
		# Connection warnings
		if self.inst_list.get("MS257_in"):
			self.ims257_status.setText("Status: CONNECTED")
			self.ims257_status.setStyleSheet("color: green")
			
		if self.inst_list.get("MS257_out"):
			self.oms257_status.setText("Status: CONNECTED")
			self.oms257_status.setStyleSheet("color: green")
		
		if self.inst_list.get("Oriel"):
			self.oriel_status.setText("Status: CONNECTED")
			self.oriel_status.setStyleSheet("color: green")
		
		if self.inst_list.get("K2001A"):
			self.k2001a_status.setText("Status: CONNECTED")
			self.k2001a_status.setStyleSheet("color: green")
		
		if self.inst_list.get("Agilent34972A"):
			self.a34972a_status.setText("Status: CONNECTED")
			self.a34972a_status.setStyleSheet("color: green")
		
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
		'''
		
		self.setWindowTitle("Pick-up instruments and connect")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
		
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
			
			
	def on_text_changed(self):
		
		self.saveButton.setText("*Save settings*")
		self.saveButton.setEnabled(True)
		
		
	def set_connect(self):
		
		#rm = visa.ResourceManager()
		##########################################
		
		if self.cb_ims257.isChecked():
			try:
				self.MS257_in = "abe"
				#self.MS257_in = MS257.MS257(self.ms257inport_str)
			except Exception as e:
				QMessageBox.warning(self, 'Message',"No response from the MS257 input monochromator serial port!")
				self.ims257_status.setText("Status: Port does not exists!")
				self.ims257_status.setStyleSheet("color: red")
				
			if hasattr(self,"MS257_in"):
				#self.MS257_in.set_timeout(1)
				try:
					#print("MS257 input monochromator version number ", self.MS257_in.getVersion())
					#self.MS257_in.set_timeout(60)
					self.ims257_status.setText("Status: CONNECTED")
					self.ims257_status.setStyleSheet("color: green")
					self.inst_list.update({'MS257_in':self.MS257_in})
				except Exception as e:
					QMessageBox.warning(self, 'Message',"MS257 could not return valid echo signal.\nCheck the port name and check the connection.")
					self.MS257_in.close()
					self.ims257_status.setText("Status: Port exists but no communication to the device!")
					self.ims257_status.setStyleSheet("color: red")
				
		else:
			if self.inst_list.get("MS257_in") or hasattr(self,"MS257_in"):
				#self.MS257_in.close()
				self.inst_list.pop('MS257_in', None)
				self.ims257_status.setText("Status: DISCONNECTED")
				self.ims257_status.setStyleSheet("color: red")
				
		##########################################
		
		if self.cb_oms257.isChecked():
			try:
				self.MS257_out = "kat"
				#self.MS257_out = MS257.MS257(self.ms257outport_str)
			except Exception as e:
				QMessageBox.warning(self, 'Message',"No response from the MS257 output monochromator serial port!")
				self.oms257_status.setText("Status: Port does not exists!")
				self.oms257_status.setStyleSheet("color: red")
			
			if hasattr(self,"MS257_out"):
				#self.MS257_out.set_timeout(1)
				try:
					#print("MS257 output monochromator version number ", self.MS257_out.getVersion())
					#self.MS257_out.set_timeout(60)
					self.oms257_status.setText("Status: CONNECTED")
					self.oms257_status.setStyleSheet("color: green")
					self.inst_list.update({'MS257_out':self.MS257_out})
				except Exception as e:
					QMessageBox.warning(self, 'Message',"MS257 could not return valid echo signal.\nCheck the port name and check the connection.")
					self.MS257_out.close()
					self.oms257_status.setText("Status: Port exists but no communication to the device!")
					self.oms257_status.setStyleSheet("color: red")
				
		else:
			if self.inst_list.get("MS257_out") or hasattr(self,"MS257_out"):
				#self.MS257_out.close()
				self.inst_list.pop('MS257_out', None)
				self.oms257_status.setText("Status: DISCONNECTED")
				self.oms257_status.setStyleSheet("color: red")
				
		##########################################
		
		if self.cb_oriel.isChecked():
			try:
				self.Oriel = "ged"
				#self.Oriel = Oriel_stepper.Oriel_stepper(self.orielport_str)
			except Exception as e:
				QMessageBox.warning(self, 'Message',"No response from the Oriel serial port! Check the serial port name and the cable connection.")
				self.oriel_status.setText("Status: Port does not exists!")
				self.oriel_status.setStyleSheet("color: red")
			
			if hasattr(self,"Oriel"):
				#self.Oriel.set_timeout(1)
				try:
					#print("Oriel version number ", self.Oriel.return_ta())
					#self.Oriel.set_timeout(60)
					self.oriel_status.setText("Status: CONNECTED")
					self.oriel_status.setStyleSheet("color: green")
					self.inst_list.update({'Oriel':self.Oriel})
				except Exception as e:
					QMessageBox.warning(self, 'Message',"Oriel stepper could not return valid echo signal.\nCheck the port name and check the connection.")
					#self.Oriel.close()
					self.oriel_status.setText("Status: Port exists but no communication to the device!")
					self.oriel_status.setStyleSheet("color: red")
					
		else:
			if self.inst_list.get("Oriel") or hasattr(self,"Oriel"):
				#self.Oriel.close()
				self.inst_list.pop('Oriel', None)
				self.oriel_status.setText("Status: DISCONNECTED")
				self.oriel_status.setStyleSheet("color: red")
		
		##########################################
		
		if self.cb_k2001a.isChecked():
			try:
				self.K2001A = "far"
				#self.K2001A = K2001A.K2001A(self.k2001aport_str)
			except Exception as e:
				QMessageBox.warning(self, 'Message',"No response from the K2001A GPIB port! Check the serial port name and the cable connection.")
				self.k2001a_status.setText("Status: Port does not exists!")
				self.k2001a_status.setStyleSheet("color: red")
			
			if hasattr(self,"K2001A"):
				try:
					#print("K2001A id number ", self.K2001A.return_id())
					self.k2001a_status.setText("Status: CONNECTED")
					self.k2001a_status.setStyleSheet("color: green")
					self.inst_list.update({'K2001A':self.K2001A})
				except Exception as e:
					QMessageBox.warning(self, 'Message',"K2001A could not return valid echo signal.\nCheck the port name and check the connection.")
					self.k2001a_status.setText("Status: Port exists but no communication to the device!")
					self.k2001a_status.setStyleSheet("color: red")
		else:
			
			if self.inst_list.get("K2001A") or hasattr(self,"K2001A"):
				self.inst_list.pop('K2001A', None)
				
				self.k2001a_status.setText("Status: DISCONNECTED")
				self.k2001a_status.setStyleSheet("color: red")
		
		##########################################
		
		if self.cb_a34972a.isChecked():
			try:
				self.Agilent34972A = Agilent34972A.Agilent34972A(self.a34972aport_str)
			except Exception as e:
				QMessageBox.warning(self, 'Message',"No response from the Agilent 34972A USB port! Check the USB port name and the cable connection.")
				self.a34972a_status.setText("Status: Port does not exists!")
				self.a34972a_status.setStyleSheet("color: red")
			
			if hasattr(self,"Agilent34972A"):
				self.a34972a_status.setText("Oriel status: CONNECTED")
				self.a34972a_status.setStyleSheet("color: green")
				self.inst_list.update({'Agilent34972A':self.Agilent34972A})
		
		else:
			if self.inst_list.get("Agilent34972A") or hasattr(self,"Agilent34972A"):
				self.inst_list.pop('Agilent34972A', None)
				self.a34972a_status.setText("Status: DISCONNECTED")
				self.a34972a_status.setStyleSheet("color: red")
			
			
	def save_(self):
		
		reply = QMessageBox.question(self, 'Message', "Save current settings?", QMessageBox.Yes | QMessageBox.No)
		
		if reply == QMessageBox.Yes:
			self.config.set('DEFAULT', 'ms257inport', ','.join([str(self.ims257Edit.text()), str(self.cb_ims257.isChecked()) ]) )
			self.config.set('DEFAULT', 'ms257outport', ','.join([str(self.oms257Edit.text()), str(self.cb_oms257.isChecked())]) )
			self.config.set('DEFAULT', 'orielport', ','.join([str(self.orielEdit.text()), str(self.cb_oriel.isChecked()) ]) )
			self.config.set('DEFAULT', 'k2001aport', ','.join([str(self.k2001aEdit.text()), str(self.cb_k2001a.isChecked())]) )
			self.config.set('DEFAULT', 'a34972aport', ','.join([str(self.a34972aEdit.text()), str(self.cb_a34972a.isChecked())]) )

			with open('config.ini', 'w') as configfile:
				self.config.write(configfile)
				
			self.saveButton.setText("Settings saved")
			self.saveButton.setEnabled(False)
			
			
	def closeEvent(self,event):
		reply = QMessageBox.question(self, 'Message', "Quit now?", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			if self.inst_list:
				self.timer.start(1000*60*5)
			event.accept()
		else:
			event.ignore()
	

