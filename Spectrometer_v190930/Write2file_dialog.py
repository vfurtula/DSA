#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, re, serial, time, yagmail, configparser

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QCheckBox, QLabel, QLineEdit, QComboBox, QFrame, QVBoxLayout, QHBoxLayout, QMenuBar, QPushButton)



class Write2file_dialog(QDialog):
	
	def __init__(self, parent):
		super().__init__(parent)
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
			self.last_used_scan = self.config.get('LastScan','last_used_scan')
			
			self.w2txtFile_str=self.config.get(self.last_used_scan,'write2txt').strip().split(',')[0]
			self.w2txt_check=self.bool_(self.config.get(self.last_used_scan,'write2txt').strip().split(',')[1])
			self.w2dbFile_str=self.config.get(self.last_used_scan,'write2db').strip().split(',')[0]
			self.w2db_check=self.bool_(self.config.get(self.last_used_scan,'write2db').strip().split(',')[1])
			self.w2matFile_str=self.config.get(self.last_used_scan,'write2mat').strip().split(',')[0]
			self.w2mat_check=self.bool_(self.config.get(self.last_used_scan,'write2mat').strip().split(',')[1])
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
		
		# Enable antialiasing for prettier plots
		self.initUI()
		
		
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
		
	def initUI(self):
		
		empty_string = QLabel("",self)
		
		w2txt_lbl = QLabel("Write to a text file (.txt):",self)
		w2txt_lbl.setStyleSheet("color: blue")
		self.w2txtFileEdit = QLineEdit(self.w2txtFile_str,self)
		self.w2txtFileEdit.textChanged.connect(self.on_text_changed)
		self.w2txtFileEdit.setEnabled(self.w2txt_check)
		self.w2txtFileEdit.setFixedWidth(250)
		self.cb_w2txt = QCheckBox('',self)
		self.cb_w2txt.toggle()
		self.cb_w2txt.setChecked(self.w2txt_check)
		
		w2db_lbl = QLabel("Write to a database file (.db):",self)
		w2db_lbl.setStyleSheet("color: blue")
		self.w2dbFileEdit = QLineEdit(self.w2dbFile_str,self)
		self.w2dbFileEdit.textChanged.connect(self.on_text_changed)
		self.w2dbFileEdit.setEnabled(self.w2db_check)
		self.w2dbFileEdit.setFixedWidth(250)
		self.cb_w2db = QCheckBox('',self)
		self.cb_w2db.toggle()
		self.cb_w2db.setChecked(self.w2db_check)
		self.cb_w2db.setEnabled(False)
		
		w2mat_lbl = QLabel("Write to a matlab file (.mat):",self)
		w2mat_lbl.setStyleSheet("color: blue")
		self.w2matFileEdit = QLineEdit(self.w2matFile_str,self)
		self.w2matFileEdit.textChanged.connect(self.on_text_changed)
		self.w2matFileEdit.setEnabled(self.w2mat_check)
		self.w2matFileEdit.setFixedWidth(250)
		self.cb_w2mat = QCheckBox('',self)
		self.cb_w2mat.toggle()
		self.cb_w2mat.setChecked(self.w2mat_check)
		
		self.closeButton = QPushButton("Close",self)
		#self.closeButton.setFixedWidth(150)
		
		self.saveButton = QPushButton("Accept",self)
		self.saveButton.setEnabled(False)
		#self.saveButton.setFixedWidth(150)
		##############################################
		
		# Add all widgets
		g0_0 = QGridLayout()
		
		g0_0.addWidget(w2txt_lbl,0,0)
		g0_0.addWidget(self.cb_w2txt,0,1)
		g0_0.addWidget(self.w2txtFileEdit,1,0)
		g0_0.addWidget(empty_string,2,0)
		
		g0_0.addWidget(w2db_lbl,3,0)
		g0_0.addWidget(self.cb_w2db,3,1)
		g0_0.addWidget(self.w2dbFileEdit,4,0)
		g0_0.addWidget(empty_string,5,0)
		
		g0_0.addWidget(w2mat_lbl,6,0)
		g0_0.addWidget(self.cb_w2mat,6,1)
		g0_0.addWidget(self.w2matFileEdit,7,0)
		g0_0.addWidget(empty_string,8,0)
		
		g1_0 = QGridLayout()
		g1_0.addWidget(self.saveButton,0,0)
		g1_0.addWidget(self.closeButton,0,1)
		
		v0 = QVBoxLayout()
		v0.addLayout(g0_0)
		v0.addLayout(g1_0)
		
		self.setLayout(v0) 
    
    ##############################################
	
		# run the main script
		self.closeButton.clicked.connect(self.close_)
		self.saveButton.clicked.connect(self.save_)
		
		self.cb_w2txt.stateChanged.connect(self.w2txt_stch)
		self.cb_w2db.stateChanged.connect(self.w2db_stch)
		self.cb_w2mat.stateChanged.connect(self.w2mat_stch)
		
		##############################################
		
		self.setWindowTitle("Write data to a file")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
		
	def w2txt_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.w2txtFileEdit.setEnabled(True)
		else:
			self.w2txtFileEdit.setEnabled(False)
			
			
	def w2db_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.w2dbFileEdit.setEnabled(True)
		else:
			self.w2dbFileEdit.setEnabled(False)
			
			
	def w2mat_stch(self, state):
		
		self.on_text_changed()
		if state in [Qt.Checked,True]:
			self.w2matFileEdit.setEnabled(True)
		else:
			self.w2matFileEdit.setEnabled(False)
			
			
	def on_text_changed(self):
		
		self.saveButton.setText("*Accept*")
		self.saveButton.setEnabled(True)
		
		
	def save_(self):
		
		self.config.read('config.ini')
		self.config.set(self.last_used_scan, 'write2txt', ','.join([str(self.w2txtFileEdit.text()), str(self.cb_w2txt.isChecked()) ]) )
		self.config.set(self.last_used_scan, 'write2db', ','.join([str(self.w2dbFileEdit.text()), str(self.cb_w2db.isChecked())]) )
		self.config.set(self.last_used_scan, 'write2mat', ','.join([str(self.w2matFileEdit.text()), str(self.cb_w2mat.isChecked()) ]) )
		
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
		self.saveButton.setText("Accepted")
		self.saveButton.setEnabled(False)
			
			
	def close_(self):
		
		self.close()
		
		
	def closeEvent(self,event):
		
		event.accept()

	

