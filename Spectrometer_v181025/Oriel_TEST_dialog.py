#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, sys, re, serial, time, numpy, configparser

from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout,
														 QLabel, QLineEdit, QComboBox, QVBoxLayout, QHBoxLayout, QPushButton)

import Oriel_stepper




class Oriel_TEST_dialog(QDialog):
	
	def __init__(self, parent, inst_list):
		super().__init__(parent)
		# constants
		self.inst_list = inst_list
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
			
			self.orielport_str = self.config.get('DEFAULT','orielport').strip().split(',')[0]
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
		
		self.target = " "
		
		self.setupUi()
		
		# close both MS257 serial ports if open
		if self.inst_list.get("Oriel"):
			if self.inst_list.get("Oriel").is_open():
				self.inst_list.get("Oriel").close()
		self.inst_list.pop('Oriel', None)
		
		
	def setupUi(self):
		serialport = QLabel("Serial port",self)
		self.serialportEdit = QLineEdit(self.orielport_str,self)
		
		self.upButton = QPushButton(u'\u25b2',self)
		self.set_bstyle_v1(self.upButton)
		self.downButton = QPushButton(u'\u25bc',self)
		self.set_bstyle_v1(self.downButton)
		
		pos_lbl = QLabel('Stored target position:',self)
		self.tarpos_lbl = QLabel('',self)
		self.tarpos_lbl.setStyleSheet("color: blue")
		
		self.setButton = QPushButton('Set position target',self)
		self.settarEdit = QLineEdit('',self)
		self.gotoButton = QPushButton('Move to target',self)
		
		target_lbl = QLabel("Get target ",self)
		self.combo0 = QComboBox(self)
		self.combo0.setFixedWidth(85)
		self.mylist0=["A","B", " "]
		self.combo0.addItems(self.mylist0)
		self.combo0.setCurrentIndex(self.mylist0.index(self.target))
		
		##############################################
		
		g0_1 = QGridLayout()
		g0_1.addWidget(serialport,0,0)
		g0_1.addWidget(self.serialportEdit,0,1)
		g0_1.addWidget(target_lbl,0,2)
		g0_1.addWidget(self.combo0,0,3)
		
		g0_2 = QGridLayout()
		g0_2.addWidget(self.upButton,0,0)
		g0_2.addWidget(self.downButton,1,0)
		
		g1_1 = QGridLayout()
		g1_1.addWidget(pos_lbl,0,0)
		g1_1.addWidget(self.tarpos_lbl,0,1)
		
		g2_1 = QGridLayout()
		g2_1.addWidget(self.setButton,0,0)
		g2_1.addWidget(self.settarEdit,0,1)
		g2_1.addWidget(self.gotoButton,0,2)
		
		vbox1 = QVBoxLayout()
		vbox1.addLayout(g1_1)
		vbox1.addLayout(g2_1)
		
		hbox2 = QHBoxLayout()
		hbox2.addLayout(g0_2)
		hbox2.addLayout(vbox1)
		
		vbox2 = QVBoxLayout()
		vbox2.addLayout(g0_1)
		vbox2.addLayout(hbox2)
		
		##############################################
		
		self.threadpool = QThreadPool()
		print("Multithreading in the Oriel dialog with maximum %d threads" % self.threadpool.maxThreadCount())
		
		self.setLayout(vbox2)
		self.setWindowTitle("Test Oriel stepper controller")
		
		# Initialize and set titles and axis names for both plots
		self.combo0.activated[str].connect(self.onActivated0)
		
		# run or cancel the main script
		self.gotoButton.clicked.connect(self.runstop)
		self.setButton.clicked.connect(self.runstop)
		self.upButton.clicked.connect(self.runstop)
		self.downButton.clicked.connect(self.runstop)
		
		
	def set_bstyle_v1(self,button):
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(30)
		
		
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
	
	
	def onActivated0(self, text):
		
		if not hasattr(self, 'Oriel'):
			try:
				self.Oriel = Oriel_stepper.Oriel_stepper(str(self.serialportEdit.text()), False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'Oriel stepper TEST MODE', ''.join(["Oriel stepper could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.Oriel = Oriel_stepper.Oriel_stepper(str(self.serialportEdit.text()), True)
				else:
					self.combo0.setCurrentIndex(self.mylist0.index(self.target))
					return
		
		else:
			try:
				if self.Oriel.is_open():
					self.Oriel.close()
				self.Oriel = Oriel_stepper.Oriel_stepper(str(self.serialportEdit.text()), False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'Oriel stepper TEST MODE', ''.join(["Oriel stepper could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.Oriel = Oriel_stepper.Oriel_stepper(str(self.serialportEdit.text()), True)
				else:
					self.combo0.setCurrentIndex(self.mylist0.index(self.target))
					return
			
		self.orielport_str = str(self.serialportEdit.text())
		
		self.serialportEdit.setEnabled(False)
		self.settarEdit.setEnabled(False)
		self.combo0.setEnabled(False)
		self.gotoButton.setEnabled(False)
		self.setButton.setEnabled(False)
		self.upButton.setEnabled(False)
		self.downButton.setEnabled(False)
		
		self.target = str(text)
		
		if self.target=='A':
			tal = self.Oriel.return_ta()
		elif self.target=='B':
			tal = self.Oriel.return_tb()
		else:
			QMessageBox.warning(self, 'Message',"Set the position target to A or to B")
			self.set_finished()
			return
			
		self.tarpos_lbl.setText(str(tal))
		self.set_finished()
		
	def runstop(self):
		
		if not hasattr(self, 'Oriel'):
			try:
				self.Oriel = Oriel_stepper.Oriel_stepper(str(self.serialportEdit.text()), False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'Oriel stepper TEST MODE', ''.join(["Oriel stepper could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.Oriel = Oriel_stepper.Oriel_stepper(str(self.serialportEdit.text()), True)
				else:
					self.combo0.setCurrentIndex(self.mylist0.index(self.target))
					return
		
		else:
			try:
				if self.Oriel.is_open():
					self.Oriel.close()
				self.Oriel = Oriel_stepper.Oriel_stepper(str(self.serialportEdit.text()), False)
			except Exception as e:
				reply = QMessageBox.critical(self, 'Oriel stepper TEST MODE', ''.join(["Oriel stepper could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
				if reply == QMessageBox.Yes:
					self.Oriel = Oriel_stepper.Oriel_stepper(str(self.serialportEdit.text()), True)
				else:
					self.combo0.setCurrentIndex(self.mylist0.index(self.target))
					return
		
		self.orielport_str = str(self.serialportEdit.text())
		
		self.serialportEdit.setEnabled(False)
		self.settarEdit.setEnabled(False)
		self.combo0.setEnabled(False)
		self.gotoButton.setEnabled(False)
		self.setButton.setEnabled(False)
		self.upButton.setEnabled(False)
		self.downButton.setEnabled(False)
		
		sender=self.sender()
		
		if sender.text()=="Set position target":
			if not self.is_number(str(self.settarEdit.text())):
				QMessageBox.warning(self, 'Message',"The target position should be a real number")
				return
		
			if self.target=="A":
				self.Oriel.set_ta(str(self.settarEdit.text()))
					
			elif self.target=="B":
				self.Oriel.set_tb(str(self.settarEdit.text()))
				
		elif sender.text()=="Move to target":
			if self.target=="A":
				self.Oriel.goto_a()
				tal = self.Oriel.return_ta()
				
			elif self.target=="B":
				self.Oriel.goto_b()
				tal = self.Oriel.return_tb()
			self.tarpos_lbl.setText(str(tal))
			
		elif sender.text()==u'\u25b2':
			self.Oriel.jog_up()
			
		elif sender.text()==u'\u25bc':
			self.Oriel.jog_down()
		
		self.set_finished()
			
	def set_finished(self):
		self.serialportEdit.setEnabled(True)
		self.settarEdit.setEnabled(True)
		self.combo0.setEnabled(True)
		self.gotoButton.setEnabled(True)
		self.setButton.setEnabled(True)
		self.upButton.setEnabled(True)
		self.downButton.setEnabled(True)
		
		
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message', "Quit now? Changes will not be saved!", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			if hasattr(self, 'Oriel'):
				if self.Oriel.is_open():
					self.Oriel.close()
			
			event.accept()
		else:
		  event.ignore() 
