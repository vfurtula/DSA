#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import traceback, sys, os, sqlite3, itertools, collections, configparser, getpass, h5py
import re, serial, time, datetime, numpy, random, yagmail, visa, scipy.io
import Scan_Worker
from matplotlib import cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import pyqtgraph.exporters

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot, QByteArray, Qt
from PyQt5.QtGui import QFont, QFrame, QMovie
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLCDNumber, QMessageBox, QGridLayout, QHeaderView,
														 QLabel, QLineEdit, QComboBox, QFrame, QTableWidget, QTableWidgetItem, QDialog,
														 QVBoxLayout, QHBoxLayout, QApplication, QMenuBar, QPushButton, QAbstractScrollArea,
														 QFileSystemModel, QTreeView, QTabWidget)

from test_dialogs import MS257_TEST_dialog, K2001A_TEST_dialog, Oriel_TEST_dialog, Agilent34972A_TEST_dialog, GUV_TEST_dialog
import Email_settings_dialog, Send_email_dialog, Instruments_dialog, Write2file_dialog, Load_config_dialog, Message_dialog

from help_dialogs import Indicator_invs_dialog, Indicator_dialog
import asyncio





class WorkerSignals(QObject):
	
	# Create signals to be used
	update_movie = pyqtSignal(object)
	
	update_all_k2001a = pyqtSignal(object)
	update_all_a34972a = pyqtSignal(object)
	update_all_guv = pyqtSignal(object)
	
	update_end_k2001a = pyqtSignal(object)
	update_end_a34972a = pyqtSignal(object)
	update_end_guv = pyqtSignal(object)
	
	update_wl_time = pyqtSignal(object)
	
	update_oriel = pyqtSignal(object)
	update_shutter = pyqtSignal(object)
	
	warning = pyqtSignal(object)
	critical = pyqtSignal(object)
	
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
		asyncio.set_event_loop(asyncio.new_event_loop())
		'''
		Initialise the runner function with passed args, kwargs.
		'''
		# Retrieve args/kwargs here; and fire processing using them
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0], getpass.getpass( prompt=''.join(["Password for ",self.emailset_str[0],"@gmail.com:"]) ))
			self.yag.send(to=self.emailrec_str, subject=self.subject, contents=self.contents)
			self.signals.warning.emit(''.join(["E-mail is sent to ", ' and '.join([i for i in self.emailrec_str]) ," including ",str(len(self.contents[1:]))," attachment(s)!"]))
		except Exception as e:
			self.signals.critical.emit(''.join(["Could not send e-mail from the gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check your internet connection. \n2. Check the account username and password.\n3. Make sure that the account accepts less secure apps.\n4. Make sure that keyring.get_password(\"system\", \"username\") works in your operating system.\n\n",str(e)]))
			
		self.signals.finished.emit()
		
		
		
		
		
		
		
		
		
class Run_gui(QMainWindow):
	
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
		self.fileLoadAs = fileMenu.addAction("Config section settings")        
		self.fileLoadAs.triggered.connect(self.load_config_dialog)
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
		
		lbl6 = QLabel("Load config section:", self)
		lbl6.setStyleSheet("QWidget {color: blue}")
		self.combo13 = QComboBox(self)
		self.mylist13=self.get_scan_sections()
		self.combo13.addItems(self.mylist13)
		self.combo13.setCurrentIndex(self.mylist13.index(self.last_used_scan))
		#self.combo13.setFixedWidth(75)
		
		##############################################
		
		lbl1 = QLabel("Scan intervals, colon separated (xx;xx):", self)
		lbl1.setStyleSheet("QWidget {color: blue}")
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
		#self.dwelltimeEdit.setFixedWidth(75)
		
		##############################################
		
		lbl4 = QLabel("Write to file(s):", self)
		lbl4.setStyleSheet("QWidget {color: blue}")
		txtfile_lbl = QLabel("Text file:",self)
		dbfile_lbl = QLabel("Sqlite3 file:",self)
		matfile_lbl = QLabel("Matlab file:",self)
		hdf5file_lbl = QLabel("HDF5 file:",self)
		
		self.txtfile_ = QLabel("",self)
		self.dbfile_ = QLabel("",self)
		self.matfile_ = QLabel("",self)
		self.hdf5file_ = QLabel("",self)
		
		if self.write2txt_check:
			self.txtfile_.setText(''.join([self.write2txt_str,' (.txt)']))
			self.txtfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.txtfile_.setText("No text file")
			self.txtfile_.setStyleSheet("QWidget {color: red}")
			
		if self.write2db_check:
			self.dbfile_.setText(''.join([self.write2db_str,' (.db)']))
			self.dbfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.dbfile_.setText("No sqlite3 file")
			self.dbfile_.setStyleSheet("QWidget {color: red}")
		
		if self.write2mat_check:
			self.matfile_.setText(''.join([self.write2mat_str,' (.mat)']))
			self.matfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.matfile_.setText("No matlab file")
			self.matfile_.setStyleSheet("QWidget {color: red}")
		
		if self.write2hdf5_check:
			self.hdf5file_.setText(''.join([self.write2hdf5_str,' (.hdf5)']))
			self.hdf5file_.setStyleSheet("QWidget {color: green}")
		else:
			self.hdf5file_.setText("No hdf5 file")
			self.hdf5file_.setStyleSheet("QWidget {color: red}")
			
		##############################################
		
		self.shind_lbl = QLabel(''.join([" Shutter ", self.shutnow.upper()]),self)
		self.shind_lbl.setFrameStyle(QFrame.Panel | QFrame.Raised)
		self.shind_lbl.setLineWidth(2)

		if self.shutnow=="on":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkGreen; border-radius: 10px; background-color: green}")
		elif self.shutnow=="off":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkRed; border-radius: 10px; background-color: red}")
		elif self.shutnow=="?":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkGrey; border-radius: 10px; background-color: grey}")
			
		##############################################
		
		unit_lbl = QLabel("Unit",self)
		self.combo3 = QComboBox(self)
		self.mylist3=["nm","um","wn"]
		self.combo3.addItems(self.mylist3)
		self.combo3.setCurrentIndex(self.mylist3.index(self.unit_str))
		self.combo3.setFixedWidth(75)
		
		##############################################
		
		grating_lbl = QLabel("Grating",self)
		self.combo9 = QComboBox(self)
		self.mylist9=['0','1','2','3','4','home']
		self.combo9.addItems(self.mylist9)
		self.combo9.setCurrentIndex(self.mylist9.index(self.grating_str))
		#self.combo9.setFixedWidth(75)
		
		##############################################
		
		shutter_lbl = QLabel("Shutter",self)
		self.combo4 = QComboBox(self)
		self.mylist4=["on","off","on->off","on<->off"]
		self.combo4.addItems(self.mylist4)
		self.combo4.setCurrentIndex(self.mylist4.index(self.shutset))
		self.combo4.setFixedWidth(90)
		
		##############################################
		
		pos_lbl = QLabel("Position",self)
		self.combo5 = QComboBox(self)
		self.mylist5=["A","B","A<->B"]
		self.combo5.addItems(self.mylist5)
		self.combo5.setCurrentIndex(self.mylist5.index(self.posset))
		self.combo5.setFixedWidth(75)
		
		##############################################
		
		dwell_lbl = QLabel("Dwell time [s]:",self)
		dwell_lbl.setStyleSheet("QWidget {color: blue; background-color: lightGreen}")
		
		posA_delay_lbl = QLabel("Pos A",self)
		posA_delay_lbl.setStyleSheet("QWidget {background-color: lightGreen}")
		self.combo6 = QComboBox(self)
		self.mylist6=["0","1","5","10","15","20","25", "30"]
		self.combo6.addItems(self.mylist6)
		self.combo6.setCurrentIndex(self.mylist6.index(str(self.posA_delay)))
		
		##############################################
		
		self.posB_delay_lbl = QLabel("Pos B",self)
		self.posB_delay_lbl.setStyleSheet("QWidget {background-color: lightGreen}")
		self.combo7 = QComboBox(self)
		self.mylist7=["0","1","5","10","15","20","25", "30"]
		self.combo7.addItems(self.mylist7)
		self.combo7.setCurrentIndex(self.mylist7.index(str(self.posB_delay)))
		
		##############################################
		
		posAB_delay_lbl = QLabel("->A<->B<-",self)
		posAB_delay_lbl.setStyleSheet("QWidget {background-color: lightGreen}")
		self.combo11 = QComboBox(self)
		self.mylist11=["0.0","1.0","1.5","2.0","2.5","3.0","3.5","4.0"]
		self.combo11.addItems(self.mylist11)
		self.combo11.setCurrentIndex(self.mylist11.index(str(self.posAB_delay)))
		
		##############################################
		
		avg_lbl = QLabel("Avg. points:",self)
		avg_lbl.setStyleSheet("QWidget {color: blue; background-color: lightBlue}")
		
		avgptsA_lbl = QLabel("Pos A",self)
		avgptsA_lbl.setStyleSheet("QWidget {background-color: lightBlue}")
		self.combo8 = QComboBox(self)
		self.mylist8=["1","5","10","20","50","100","200"]
		self.combo8.addItems(self.mylist8)
		self.combo8.setCurrentIndex(self.mylist8.index(str(self.avgpts_a)))
		
		##############################################
		
		self.avgptsB_lbl = QLabel("Pos B",self)
		self.avgptsB_lbl.setStyleSheet("QWidget {background-color: lightBlue}")
		self.combo10 = QComboBox(self)
		self.mylist10=["1","5","10","20","50","100","200"]
		self.combo10.addItems(self.mylist10)
		self.combo10.setCurrentIndex(self.mylist10.index(str(self.avgpts_b)))
		
		##############################################
		
		self.posind_lbl = QLabel(''.join([" Position ", self.posnow]),self)
		self.posind_lbl.setFrameStyle(QFrame.Panel | QFrame.Raised)
		self.posind_lbl.setLineWidth(2)
		
		if self.posnow=="A":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkYellow; border-radius: 10px; background-color: yellow}")
		elif self.posnow=="B":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkMagenta; border-radius: 10px; background-color: magenta}")
		elif self.posnow=="?":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkGrey; border-radius: 10px; background-color: grey}")
			
		##############################################
		
		schroll_lbl = QLabel("Schroll elapsed time [pts]:",self)
		schroll_lbl.setStyleSheet("QWidget {color: blue}")
		self.combo12 = QComboBox(self)
		self.mylist12=["100","200","400","600","800","1000","1500","2000"]
		self.combo12.addItems(self.mylist12)
		self.combo12.setCurrentIndex(self.mylist12.index( str(self.schroll_pts) ))
		
		##############################################
		
		lbl5 = QLabel("Start scan and record data:", self)
		lbl5.setStyleSheet("QWidget {color: blue}")
		
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
		self.elapsedtime_str.setStyleSheet("QWidget {color: blue}")
		
		##############################################
		
		self.lcd = QLCDNumber(self)
		self.lcd.setStyleSheet("QWidget {color: red}")
		self.lcd.setFixedHeight(60)
		self.lcd.setSegmentStyle(QLCDNumber.Flat)
		self.lcd.setNumDigits(11)
		self.lcd.display(self.time_str)
			
		##############################################
		
		# create table
		self.tableWidget = self.createTable()
		
		##############################################
		
		self.model = QFileSystemModel()
		#self.model.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
		self.model.setRootPath("")
		#self.model.setNameFilters(list("*.db"))
		#self.model.setNameFilterDisables(False)
		
		self.tree = QTreeView()
		self.tree.setModel(self.model)
		self.tree.setRootIndex(self.model.index("data"+os.sep))
		#self.tree.setNameFilters(list("*.txt *.mat *.db"))
		
		self.tree.setAnimated(False)
		self.tree.setIndentation(20)
		self.tree.setSortingEnabled(True)
		
		#self.tree.setWindowTitle("Dir View")
		self.tree.resize(640, 480)
		
		##############################################
		
		# Add all widgets
		h0 = QGridLayout()
		h0.addWidget(self.posind_lbl,0,0)
		h0.addWidget(self.shind_lbl,0,1)
		
		h1 = QGridLayout()
		h1.addWidget(posA_delay_lbl,1,0)
		h1.addWidget(self.posB_delay_lbl,1,1)
		h1.addWidget(posAB_delay_lbl,1,2)
		h1.addWidget(self.combo6,2,0)
		h1.addWidget(self.combo7,2,1)
		h1.addWidget(self.combo11,2,2)
		h2 = QVBoxLayout()
		h2.addWidget(dwell_lbl)
		h2.addLayout(h1)
		
		h3 = QGridLayout()
		h3.addWidget(avgptsA_lbl,1,3)
		h3.addWidget(self.avgptsB_lbl,1,4)
		h3.addWidget(self.combo8,2,3)
		h3.addWidget(self.combo10,2,4)
		h4 = QVBoxLayout()
		h4.addWidget(avg_lbl)
		h4.addLayout(h3)
		
		h5 = QHBoxLayout()
		h5.addLayout(h2)
		h5.addLayout(h4)
		
		g1_0 = QGridLayout()
		g1_0.addWidget(MyBar,0,0)
		g1_4 = QGridLayout()
		g1_4.addWidget(lbl6,0,0)
		g1_4.addWidget(self.combo13,0,1)
		g1_5 = QGridLayout()
		g1_5.addWidget(lbl1,0,0)
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
		g1_3.addWidget(grating_lbl,0,3)
		g1_3.addWidget(self.combo9,1,3)
		
		v1 = QVBoxLayout()
		v1.addLayout(g1_0)
		v1.addLayout(g1_4)
		v1.addLayout(g1_5)
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
		g4_1.addWidget(hdf5file_lbl,3,0)
		g4_1.addWidget(self.hdf5file_,3,1)
		v4 = QVBoxLayout()
		v4.addLayout(g4_0)
		v4.addLayout(g4_1)
		
		g5_2 = QGridLayout()
		g5_2.addWidget(run_str,0,0)
		g5_0 = QGridLayout()
		g5_0.addWidget(lbl5,0,0)
		g5_1 = QGridLayout()
		g5_1.addLayout(g5_2,0,0)
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
		v8.addLayout(h5)
		v8.addWidget(schroll_lbl)
		v8.addWidget(self.combo12)
		v8.addLayout(v4)
		v8.addLayout(v5)
		v8.addLayout(v6)
		v8.addWidget(self.tree)
		
		##############################################
		
		# set GRAPHS and TOOLBARS to a new vertical group vcan
		self.win = pg.GraphicsWindow()
		
		self.p0 = self.win.addPlot()
		self.c_k2001a_end_Aon = self.p0.plot(pen=pg.mkPen('g',width=4, style=QtCore.Qt.DashLine), symbol='s', symbolPen='g', symbolBrush='g', symbolSize=5)
		self.c_k2001a_end_Aoff = self.p0.plot(pen=pg.mkPen('m',width=4, style=QtCore.Qt.DashLine), symbol='s', symbolPen='m', symbolBrush='m', symbolSize=5)
		self.c_k2001a_end_Bon = self.p0.plot(pen=pg.mkPen('g',width=4, style=QtCore.Qt.DotLine), symbol='p', symbolPen='g', symbolBrush='g', symbolSize=5)
		self.c_k2001a_end_Boff = self.p0.plot(pen=pg.mkPen('r',width=4, style=QtCore.Qt.DotLine), symbol='p', symbolPen='r', symbolBrush='r', symbolSize=5)
		
		self.c_a34972a_end_Aon = self.p0.plot(pen=pg.mkPen('g',width=4, style=QtCore.Qt.SolidLine), symbol='d', symbolPen='g', symbolBrush='g', symbolSize=5)
		self.c_a34972a_end_Aoff = self.p0.plot(pen=pg.mkPen('y',width=4, style=QtCore.Qt.SolidLine), symbol='d', symbolPen='y', symbolBrush='y', symbolSize=5)
		self.c_a34972a_end_Bon = self.p0.plot(pen=pg.mkPen('g',width=4, style=QtCore.Qt.SolidLine), symbol='o', symbolPen='g', symbolBrush='g', symbolSize=5)
		self.c_a34972a_end_Boff = self.p0.plot(pen=pg.mkPen('w',width=4, style=QtCore.Qt.SolidLine), symbol='o', symbolPen='w', symbolBrush='w', symbolSize=5)
		
		self.c_guv_end_Aon = []
		self.c_guv_end_Aoff = []
		self.c_guv_end_Bon = []
		self.c_guv_end_Boff = []
		
		self.p0.enableAutoRange()
		self.p0.setLabel('left', "Signal", units='', color='green')
		self.p0.setLabel('bottom', "Wavelength", units=self.unit_str, color='white')
		#self.p0.setLogMode(y=True)
		
		self.win.nextRow()
		
		self.p1 = self.win.addPlot()
		self.c_k2001a_all_Aon = self.p1.plot(pen=pg.mkPen('g',width=2, style=QtCore.Qt.DashLine), symbol='s', symbolPen='g', symbolBrush='g', symbolSize=3)
		self.c_k2001a_all_Aoff = self.p1.plot(pen=pg.mkPen('m',width=2, style=QtCore.Qt.DashLine), symbol='s', symbolPen='r', symbolBrush='r', symbolSize=3)
		self.c_k2001a_all_Bon = self.p1.plot(pen=pg.mkPen('g',width=2, style=QtCore.Qt.DotLine), symbol='p', symbolPen='g', symbolBrush='g', symbolSize=3)
		self.c_k2001a_all_Boff = self.p1.plot(pen=pg.mkPen('r',width=2, style=QtCore.Qt.DotLine), symbol='p', symbolPen='r', symbolBrush='r', symbolSize=3)
		
		self.c_a34972a_all_Aon = self.p1.plot(pen=pg.mkPen('g',width=2, style=QtCore.Qt.SolidLine), symbol='d', symbolPen='g', symbolBrush='g', symbolSize=3)
		self.c_a34972a_all_Aoff = self.p1.plot(pen=pg.mkPen('y',width=2, style=QtCore.Qt.SolidLine), symbol='d', symbolPen='r', symbolBrush='r', symbolSize=3)
		self.c_a34972a_all_Bon = self.p1.plot(pen=pg.mkPen('g',width=2, style=QtCore.Qt.SolidLine), symbol='o', symbolPen='g', symbolBrush='g', symbolSize=3)
		self.c_a34972a_all_Boff = self.p1.plot(pen=pg.mkPen('w',width=2, style=QtCore.Qt.SolidLine), symbol='o', symbolPen='r', symbolBrush='r', symbolSize=3)
		
		self.c_guv_all_Aon = []
		self.c_guv_all_Aoff = []
		self.c_guv_all_Bon = []
		self.c_guv_all_Boff = []
		
		# create plot and add it to the figure
		self.p2 = pg.ViewBox()
		self.c_time_wl=pg.PlotCurveItem(pen=pg.mkPen('y', width=3))
		self.p2.addItem(self.c_time_wl)
		# connect respective axes to the plot 
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Wavelength", units=self.unit_str, color='yellow')
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis('right').linkToView(self.p2)
		self.p2.setXLink(self.p1)
		
		# Use automatic downsampling and clipping to reduce the drawing load
		self.p1.enableAutoRange()
		self.p1.setDownsampling(mode='peak')
		self.p1.setClipToView(True)
		
		# Labels and titels are placed here since they change dynamically
		self.p1.setLabel('left', "Signal", units='', color='red')
		self.p1.setLabel('bottom', "Elapsed time", units='s', color='white')
		#self.p1.setLogMode(y=True)
		
		##############################################
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		
		# Initialize tab screen
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		
		# Add tabs
		self.tabs.addTab(self.win,"scan")
		self.tabs.addTab(self.tableWidget,"tab vals")
		self.tabIndex=1
		
		hbox = QHBoxLayout()
		hbox.addLayout(v8,1)
		hbox.addWidget(self.tabs,3)
		
		# catch signal tabCloseRequested from the QTabWidget
		self.tabs.tabCloseRequested.connect(self.removeThisTab)
		
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
		self.combo8.activated[str].connect(self.onActivated8)
		self.combo9.activated[str].connect(self.onActivated9)
		self.combo10.activated[str].connect(self.onActivated10)
		self.combo11.activated[str].connect(self.onActivated11)
		self.combo12.activated[str].connect(self.onActivated12)
		self.combo13.activated[str].connect(self.onActivated13)
		
		# save all paramter data in the config file
		#self.saveButton.clicked.connect(self.save_)
		#self.saveButton.clicked.connect(self.set_elapsedtime_text)
	
		# run the main script
		self.runButton.clicked.connect(self.set_run)
		
		# abort the script run
		self.abortButton.clicked.connect(self.set_abort)
		
		# pause the script run
		self.pauseButton.clicked.connect(self.set_pause)
		
		# doubleclick a file and plot data
		self.tree.doubleClicked.connect(self.plotfile)
		
		##############################################
		
		self.inst_list = {}
		
		self.threadpool = QThreadPool()
		print("Multithreading in TEST_gui_v1 with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning = False
		
		self.abortButton.setEnabled(False)
		self.pauseButton.setEnabled(False)
		
		self.write2file.setEnabled(True)
		self.fileLoadAs.setEnabled(True)
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
		self.combo8.setEnabled(False)
		self.combo9.setEnabled(False)
		self.combo10.setEnabled(False)
		self.combo11.setEnabled(False)
		self.combo12.setEnabled(False)
		self.combo13.setEnabled(False)
		
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.set_disconnect)
		self.timer.setSingleShot(True)
		
		##############################################
		
		self.setGeometry(100, 100, 900, 450)
		self.setWindowTitle(''.join(["Direktoratet for strålevern og atomsikkerhet - Scan Control And Data Acqusition"]))
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		hbox.setSizeConstraint(hbox.SetFixedSize)
		
		w = QWidget()
		w.setLayout(hbox)
		self.setCentralWidget(w)
		self.show()
		
		
	def removeThisTab(self, index):
		
		if index in [0,1]:
			QMessageBox.critical(self, 'Message',"You can not close this tab!")
			return
		
		widget = self.tabs.widget(index)
		if widget is not None:
			widget.deleteLater()
		self.tabs.removeTab(index)
		self.tabIndex-=1
		
		
	def get_scan_sections(self):
		
		mylist=[]
		for i in self.config.sections():
			if i not in ["LastScan","Instruments"]:
				mylist.extend([i])
		
		return mylist
		
		
	def initUI_(self):
		
		self.start_lbl.setText(''.join(["Start[",self.unit_str,"]"]))
		self.stop_lbl.setText(''.join(["Stop[",self.unit_str,"]"]))
		self.step_lbl.setText(''.join(["Step[",self.unit_str,"]"]))
		
		self.p0.setLabel('bottom', "Wavelength", units=self.unit_str, color='white')
		self.p1.getAxis('right').setLabel("Wavelength", units=self.unit_str, color='yellow')
		self.tableWidget.setHorizontalHeaderLabels(["Detector",''.join(["Wavel. [",self.unit_str,"]"]),"Channel signals","Mirror pos","Shutter","Time [s]"])

		self.startEdit.setText(str(self.sssd[0]))
		self.stopEdit.setText(str(self.sssd[1]))
		self.stepEdit.setText(str(self.sssd[2]))
		self.dwelltimeEdit.setText(str(self.sssd[3])) 
		
		if self.write2txt_check:
			self.txtfile_.setText(''.join([self.write2txt_str,' (.txt)']))
			self.txtfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.txtfile_.setText("No text file")
			self.txtfile_.setStyleSheet("QWidget {color: red}")
			
		if self.write2db_check:
			self.dbfile_.setText(''.join([self.write2db_str,' (.db)']))
			self.dbfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.dbfile_.setText("No sqlite3 file")
			self.dbfile_.setStyleSheet("QWidget {color: red}")
		
		if self.write2mat_check:
			self.matfile_.setText(''.join([self.write2mat_str,' (.mat)']))
			self.matfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.matfile_.setText("No matlab file")
			self.matfile_.setStyleSheet("QWidget {color: red}")
		
		if self.write2hdf5_check:
			self.hdf5file_.setText(''.join([self.write2hdf5_str,' (.hdf5)']))
			self.hdf5file_.setStyleSheet("QWidget {color: green}")
		else:
			self.hdf5file_.setText("No hdf5 file")
			self.hdf5file_.setStyleSheet("QWidget {color: red}")
			
		##############################################
		
		self.shind_lbl.setText(''.join([" Shutter ", self.shutnow.upper()]))

		if self.shutnow=="on":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkGreen; border-radius: 10px; background-color: green}")
		elif self.shutnow=="off":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkRed; border-radius: 10px; background-color: red}")
		elif self.shutnow=="?":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkGrey; border-radius: 10px; background-color: grey}")
		
		##############################################
		
		self.combo3.setCurrentIndex(self.mylist3.index(self.unit_str))
		self.combo4.setCurrentIndex(self.mylist4.index(self.shutset))
		self.combo5.setCurrentIndex(self.mylist5.index(self.posset))
		self.combo6.setCurrentIndex(self.mylist6.index(str(self.posA_delay)))
		self.combo7.setCurrentIndex(self.mylist7.index(str(self.posB_delay)))
		self.combo8.setCurrentIndex(self.mylist8.index(str(self.avgpts_a)))
		self.combo9.setCurrentIndex(self.mylist9.index(self.grating_str))
		self.combo10.setCurrentIndex(self.mylist10.index(str(self.avgpts_b)))
		self.combo11.setCurrentIndex(self.mylist11.index(str(self.posAB_delay)))
		self.combo12.setCurrentIndex(self.mylist12.index(str(self.schroll_pts)))
		
		self.mylist13=self.get_scan_sections()
		self.combo13.clear()
		self.combo13.addItems(self.mylist13)
		self.combo13.setCurrentIndex(self.mylist13.index(self.last_used_scan))
		
		##############################################
		
		self.posind_lbl.setText(''.join([" Position ", self.posnow]))
		
		if self.posnow=="A":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkYellow; border-radius: 10px; background-color: yellow}")
		elif self.posnow=="B":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkMagenta; border-radius: 10px; background-color: magenta}")
		elif self.posnow=="?":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkGrey; border-radius: 10px; background-color: grey}")
		
		##############################################
		
		self.lcd.display(self.time_str)
		
		
	def set_bstyle_v1(self,button):
		button.setStyleSheet('QPushButton {font-size: 25pt}')
		button.setFixedWidth(40)
		button.setFixedHeight(65)
		
		
	def onActivated3(self, text):
		self.unit_str=str(text)
		
		self.start_lbl.setText(''.join(["Start[",str(text),"]"]))
		self.stop_lbl.setText(''.join(["Stop[",str(text),"]"]))
		self.step_lbl.setText(''.join(["Step[",str(text),"]"]))
		self.p0.setLabel('bottom', "Wavelength", units=self.unit_str, color='white')
		self.p1.getAxis('right').setLabel("Wavelength", units=self.unit_str, color='yellow')
		self.tableWidget.setHorizontalHeaderLabels(["Detector",''.join(["Wavel. [",self.unit_str,"]"]),"Channel signals","Mirror pos","Shutter","Time [s]"])
		
	def onActivated4(self, text):
		self.shutset = str(text)
			
			
	def onActivated5(self, text):
		self.posset = str(text)
		
		if self.posset=="A":
			self.combo6.setEnabled(True)
			self.combo7.setEnabled(False)
			self.combo8.setEnabled(True)
			self.combo10.setEnabled(False)
		elif self.posset=="B":
			self.combo6.setEnabled(False)
			self.combo7.setEnabled(True)
			self.combo8.setEnabled(False)
			self.combo10.setEnabled(True)
		elif self.posset=="A<->B":
			self.combo6.setEnabled(True)
			self.combo7.setEnabled(True)
			self.combo8.setEnabled(True)
			self.combo10.setEnabled(True)
			
			
	def onActivated6(self, text):
		self.posA_delay=int(text)
		
	def onActivated7(self, text):
		self.posB_delay=int(text)
		
	def onActivated8(self, text):
		self.avgpts_a=int(text)
		
	def onActivated9(self, text):
		self.grating_str=str(text)
		
	def onActivated10(self, text):
		self.avgpts_b=int(text)
		
	def onActivated11(self, text):
		self.posAB_delay=float(text)
		
	def onActivated12(self, text):
		self.schroll_pts=int(text)
		
	def onActivated13(self, text):
		self.last_used_scan = str(text)
		
		self.config.read('config.ini')
		self.config.set("LastScan","last_used_scan", self.last_used_scan)
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
		self.load_()
		self.initUI_()
		
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
		tableWidget.setStyleSheet("QWidget {color: blue}")
		
		# place content into individual table fields
		#tableWidget.setItem(0,0, QTableWidgetItem("abe"))
		
		tableWidget.setHorizontalHeaderLabels(["Detector",''.join(["Wavel. [",self.unit_str,"]"]),"Channel signals","Mirror pos","Shutter","Time [s]"])
		#tableWidget.setTextAlignment(Qt.AlignHCenter)
		
		# set horizontal header properties
		hh = tableWidget.horizontalHeader()
		for tal in range(5):
			if tal==2:
				hh.setSectionResizeMode(tal, QHeaderView.Stretch)
			else:
				hh.setSectionResizeMode(tal, QHeaderView.ResizeToContents)
		
		#tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
		
		# set column width to fit contents
		#tableWidget.resizeColumnsToContents()
		#tableWidget.resizeRowsToContents()
		#tableWidget.setFixedWidth(250)
		
		# enable sorting
		#tableWidget.setSortingEnabled(True)
		
		return tableWidget
			
			
	def instrumentsDialog(self):
		
		self.Inst = Instruments_dialog.Instruments_dialog(self, self.inst_list, self.timer)
		self.Inst.exec()
		
		keys = self.inst_list.keys() & ["MS257_in","MS257_out","Oriel","K2001A","Agilent34972A","GUV"]
		if not keys:
			self.runButton.setText("Load instrument!")
			self.runButton.setEnabled(False)
		else:
			self.runButton.setText("Scan")
			self.runButton.setEnabled(True)
			
			self.abortButton.setEnabled(False)
			self.pauseButton.setEnabled(False)
			
			self.write2file.setEnabled(True)
			self.fileLoadAs.setEnabled(True)
			self.conMode.setEnabled(True)
			self.testMenu.setEnabled(True)
			self.startEdit.setEnabled(True)
			self.stopEdit.setEnabled(True)
			self.stepEdit.setEnabled(True)
			self.dwelltimeEdit.setEnabled(True)
			self.combo12.setEnabled(True)
			self.combo13.setEnabled(True)
		
		
		if self.inst_list.get('MS257_in') or self.inst_list.get('MS257_out'):
			self.combo3.setEnabled(True)
			self.combo9.setEnabled(True)
		else:
			self.combo3.setEnabled(False)
			self.combo9.setEnabled(False)
		
		if self.inst_list.get('MS257_in'):
			self.combo4.setEnabled(True)
		else:
			self.combo4.setEnabled(False)
			
		if self.inst_list.get('Oriel'):
			self.combo5.setEnabled(True)
			self.combo11.setEnabled(True)
			if self.posset=="A":
				self.combo6.setEnabled(True)
				self.combo7.setEnabled(False)
				if self.inst_list.get('GUV') or self.inst_list.get('K2001A') or self.inst_list.get('Agilent34972A'):
					self.combo8.setEnabled(True)
					self.combo10.setEnabled(False)
			elif self.posset=="B":
				self.combo6.setEnabled(False)
				self.combo7.setEnabled(True)
				self.posB_delay_lbl.setText("Pos B")
				if self.inst_list.get('GUV') or self.inst_list.get('K2001A') or self.inst_list.get('Agilent34972A'):
					self.combo8.setEnabled(False)
					self.combo10.setEnabled(True)
					self.avgptsB_lbl.setText("Pos B")
			elif self.posset=="A<->B":
				self.combo6.setEnabled(True)
				self.combo7.setEnabled(True)
				self.posB_delay_lbl.setText("Pos B")
				if self.inst_list.get('GUV') or self.inst_list.get('K2001A') or self.inst_list.get('Agilent34972A'):
					self.combo8.setEnabled(True)
					self.combo10.setEnabled(True)
					self.avgptsB_lbl.setText("Pos B")
		else:
			self.combo5.setEnabled(False)
			self.combo11.setEnabled(False)
			
			self.combo6.setEnabled(False)
			self.combo7.setEnabled(False)
			self.posB_delay_lbl.setText("Pos ?")
			if self.inst_list.get('GUV') or self.inst_list.get('K2001A') or self.inst_list.get('Agilent34972A'):
				self.combo8.setEnabled(False)
				self.combo10.setEnabled(True)
				self.avgptsB_lbl.setText("Pos ?")
			
		
		
	def write2fileDialog(self):
		
		self.Write2file_dialog = Write2file_dialog.Write2file_dialog(self)
		self.Write2file_dialog.exec()
		
		try:
			self.config.read('config.ini')
			
			self.write2txt_str=self.config.get(self.last_used_scan,'write2txt').strip().split(',')[0]
			self.write2txt_check=self.bool_(self.config.get(self.last_used_scan,'write2txt').strip().split(',')[1])
			self.write2db_str=self.config.get(self.last_used_scan,'write2db').strip().split(',')[0]
			self.write2db_check=self.bool_(self.config.get(self.last_used_scan,'write2db').strip().split(',')[1])
			self.write2mat_str=self.config.get(self.last_used_scan,'write2mat').strip().split(',')[0]
			self.write2mat_check=self.bool_(self.config.get(self.last_used_scan,'write2mat').strip().split(',')[1])
			self.write2hdf5_str=self.config.get(self.last_used_scan,'write2hdf5').strip().split(',')[0]
			self.write2hdf5_check=self.bool_(self.config.get(self.last_used_scan,'write2hdf5').strip().split(',')[1])
		except:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(sys.exc_info()[0])]))
			raise ValueError
		
		if self.write2txt_check:
			self.txtfile_.setText(''.join([self.write2txt_str,' (.txt)']))
			self.txtfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.txtfile_.setText("No text file")
			self.txtfile_.setStyleSheet("QWidget {color: red}")
		
		if self.write2db_check:
			self.dbfile_.setText(''.join([self.write2db_str,' (.db)']))
			self.dbfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.dbfile_.setText("No sqlite3 file")
			self.dbfile_.setStyleSheet("QWidget {color: red}")
			
		if self.write2mat_check:
			self.matfile_.setText(''.join([self.write2mat_str,' (.mat)']))
			self.matfile_.setStyleSheet("QWidget {color: green}")
		else:
			self.matfile_.setText("No matlab file")
			self.matfile_.setStyleSheet("QWidget {color: red}")
			
		if self.write2hdf5_check:
			self.hdf5file_.setText(''.join([self.write2hdf5_str,' (.hdf5)']))
			self.hdf5file_.setStyleSheet("QWidget {color: green}")
		else:
			self.hdf5file_.setText("No hdf5 file")
			self.hdf5file_.setStyleSheet("QWidget {color: red}")
			
			
			
	def load_config_dialog(self):
		
		self.Load_config_dialog = Load_config_dialog.Load_config_dialog(self, self.config, self.load_, self.initUI_)
		self.Load_config_dialog.exec()
		
		
	def testMS257Dialog(self):
		
		self.MS257_TEST_dialog = MS257_TEST_dialog.MS257_TEST_dialog(self, self.inst_list)
		self.MS257_TEST_dialog.exec()
		
		
	def testOrielDialog(self):
		
		self.Oriel_TEST_dialog = Oriel_TEST_dialog.Oriel_TEST_dialog(self, self.inst_list)
		self.Oriel_TEST_dialog.exec()
		
		
	def testK2001ADialog(self):
		
		self.K2001A_TEST_dialog = K2001A_TEST_dialog.K2001A_TEST_dialog(self)
		self.K2001A_TEST_dialog.exec()
		
		
	def testA34972ADialog(self):
		
		self.Agilent34972A_TEST_dialog = Agilent34972A_TEST_dialog.Agilent34972A_TEST_dialog(self)
		self.Agilent34972A_TEST_dialog.exec()
		
		
	def testGUVDialog(self):
		
		self.GUV_TEST_dialog = GUV_TEST_dialog.GUV_TEST_dialog(self)
		self.GUV_TEST_dialog.exec()
		
		
	def email_data_dialog(self):
		
		self.Send_email_dialog = Send_email_dialog.Send_email_dialog(self)
		self.Send_email_dialog.exec()
		
		
	def email_set_dialog(self):
		
		self.Email_dialog = Email_settings_dialog.Email_dialog(self, self.lcd)
		self.Email_dialog.exec()
		
		
	def create_file(self,mystr):
		head, tail = os.path.split(mystr)
		if head:
			head = head.replace("/",os.sep).replace("\\",os.sep)
		else:
			QMessageBox.critical(self, 'Message','No path to folder(s) provided!')
			return ''
		
		if tail:
			saveinfile=''.join([head,os.sep,tail,'_',self.time_str])
		else:
			saveinfile=''.join([head,os.sep,'data_',self.time_str])
			
		try:
			os.makedirs(os.path.dirname(saveinfile), exist_ok=True)
		except Exception as e:
			QMessageBox.critical(self, 'Message',''.join(["Folder named ",head," not valid!\n",str(e)]))
			return ''
		
		return saveinfile
	
	
	def prepare_file(self):
		# Save to a textfile
		
		if self.inst_list.get('K2001A') or self.inst_list.get('Agilent34972A') or self.inst_list.get('GUV'):
			# Save to a TXT datafile
			if self.write2txt_check:
				self.textfile = ''.join([self.create_file(self.write2txt_str),".txt"])
				if self.textfile!='.txt':
					with open(self.textfile, 'w', encoding="utf-8") as thefile:
						thefile.write(''.join(["Detector type\tMS257_IN [",self.unit_str,"]\tMS257_OUT [",self.unit_str,"]\tSignal\tMirror pos.\tShut.\tTimetr.[s]\tAbs date and time\n"]))
				else:
					return False
				
			# Save to a MATLAB datafile
			if self.write2mat_check:
				self.matfile = ''.join([self.create_file(self.write2mat_str),".mat"])
				if self.matfile!=".mat":
					pass
				else:
					return False
				
			# Save to a HDF5 datafile
			if self.write2hdf5_check:
				self.hdf5file = ''.join([self.create_file(self.write2hdf5_str),".hdf5"])
				if self.hdf5file!=".hdf5":
					pass
				else:
					return False
				
				dt = h5py.string_dtype(encoding="utf-8")
				dt_ = h5py.vlen_dtype(numpy.dtype('float32'))
				# Create header for new inputs
				with h5py.File(self.hdf5file, 'w') as f:
					f.create_dataset("detector", (0, ),  maxshape=(None, ), dtype=dt)
					f.create_dataset("ms257_in", (0, ),  maxshape=(None, ), dtype=dt)
					f.create_dataset("ms257_out", (0, ),  maxshape=(None, ), dtype=dt)
					f.create_dataset("k2001a_signal", (0, ),  maxshape=(None, ))
					f.create_dataset("a34972a_signal", (0, ),  maxshape=(None, ))
					f.create_dataset("guv_signal", (0, ),  maxshape=(None, ), dtype=dt_)
					f.create_dataset("wavelength", (0, ),  maxshape=(None, ))
					f.create_dataset("mirrorpos", (0, ),  maxshape=(None, ), dtype=dt)
					f.create_dataset("shutter", (0, ),  maxshape=(None, ), dtype=dt)
					f.create_dataset("timetrace", (0, ),  maxshape=(None, ), dtype=dt)
					f.create_dataset("absolutetime", (0, ),  maxshape=(None, ), dtype=dt)
			
			# Save to a sqlite3 datafile
			# First delete the sqlite3 file if it exists
			if self.write2db_check:
				self.dbfile = ''.join([self.create_file(self.write2db_str),".db"])
				if self.dbfile!=".db":
					try:
						os.remove(self.dbfile)
					except OSError:
						pass
				else:
					return False
				
				# Then create it again for new inputs
				self.conn = sqlite3.connect(self.dbfile)
				self.db = self.conn.cursor()
				
				if self.inst_list.get('GUV'):
					self.db.execute('''CREATE TABLE guv (guvtype text, ms257_in text, ms257_out text, signal text, channels text, legend text, mirrorpos text, shutter text, timetrace real, absolutetime text)''')
				
				if self.inst_list.get('Agilent34972A'):
					self.db.execute('''CREATE TABLE agilent (ms257_in text, ms257_out text, signal real, mirrorpos text, shutter text, timetrace real, absolutetime text, legend text)''')
				
				if self.inst_list.get('K2001A'):
					self.db.execute('''CREATE TABLE keithley (ms257_in text, ms257_out text, signal real, mirrorpos text, shutter text, timetrace real, absolutetime text, legend text)''')
				
		return True
	
	
	def set_run(self):
		
		keys = self.inst_list.keys() & ["MS257_in","MS257_out","Oriel","K2001A","Agilent34972A","GUV"]
		if not keys:
			QMessageBox.critical(self, 'Message',"No instruments connected. At least 1 instrument is required.")
			return
		
		if self.unit_str=="nm":
			multply=1e-9
		elif self.unit_str=="um":
			multply=1e-6
			
		try:
			start_ = [float(i) for i in self.startEdit.text().split(';')]
			stop = [float(i) for i in self.stopEdit.text().split(';')]
			step = [float(i) for i in self.stepEdit.text().split(';')] 
			dwell = [float(i) for i in self.dwelltimeEdit.text().split(';')]
			
			all_len=[]
			for len_,_ in itertools.groupby(sorted([start_,stop,step,dwell], key=len), key=len):
				all_len.append(len_)
				
			if len(all_len)>1:
				QMessageBox.critical(self, 'Message',"Scan intervals must be EQUALLY sized lists seperated by colon(;)!")
				return
			
		except Exception as e:
			QMessageBox.critical(self, 'Message',"Scan intervals must be real numbers seperated by colon(;)!")
			return
		
		for i,j,k,l in zip(start_,stop,step,dwell):
			if i*multply<0 or i*multply>2500e-9:
				QMessageBox.warning(self, 'Message',"Minimum start wavelength is in the range from 0 nm to 2500 nm")
				return
			if j*multply<0 or j*multply>2500e-9:
				QMessageBox.warning(self, 'Message',"Minimum stop wavelength is in the range from 0 nm to 2500 nm")
				return
			if i>=j:
				QMessageBox.warning(self, 'Message',"Stop wavelength must be larger than the start wavelength")
				return
			if k*multply<0.01e-9 or k*multply>100e-9:
				QMessageBox.warning(self, 'Message',"Minimum step is in the range from 0.01 nm to 100 nm")
				return
			if l<0.1 or l>10:
				QMessageBox.warning(self, 'Message',"Monochromator dwell time is in the range from 0.1 sec to 10 sec")
				return
		
		self.clear_vars_graphs()
		
		self.config.read('config.ini')
		self.guvtype_str=self.config.get("Instruments",'guvtype')
		
		if self.guvtype_str=='GUV-541':
			self.guv_channels=self.config.get("Instruments",'guv541').strip().split(',')
		elif self.guvtype_str=='GUV-2511':
			self.guv_channels=self.config.get("Instruments",'guv2511').strip().split(',')
		elif self.guvtype_str=='GUV-3511':
			self.guv_channels=self.config.get("Instruments",'guv3511').strip().split(',')
		
		colors = itertools.cycle(["r", "b", "g", "y", "m", "c", "w"])
		#colors = itertools.cycle([tuple(int(i) for i in numpy.array(cm.jet(i))[:-1]*255) for i in numpy.arange(20,250,len(self.guv_channels))])
		for i in range(len(self.guv_channels)):
			mycol=next(colors)
			self.c_guv_end_Aon.append(self.p0.plot(pen=pg.mkPen(mycol,width=1), symbol='s', symbolPen=mycol, symbolBrush=mycol, symbolSize=3))
			self.c_guv_all_Aon.append(self.p1.plot(pen=pg.mkPen(mycol,width=1), symbol='s', symbolPen='g', symbolBrush='g', symbolSize=7 ))
			mycol=next(colors)
			self.c_guv_end_Bon.append(self.p0.plot(pen=pg.mkPen(mycol,width=1), symbol='p', symbolPen=mycol, symbolBrush=mycol, symbolSize=3))
			self.c_guv_all_Bon.append(self.p1.plot(pen=pg.mkPen(mycol,width=1), symbol='p', symbolPen='g', symbolBrush='g', symbolSize=7 ))
			mycol=next(colors)
			self.c_guv_end_Aoff.append(self.p0.plot(pen=pg.mkPen(mycol,width=1), symbol='d', symbolPen=mycol, symbolBrush=mycol, symbolSize=3))
			self.c_guv_all_Aoff.append(self.p1.plot(pen=pg.mkPen(mycol,width=1), symbol='d', symbolPen='r', symbolBrush='r', symbolSize=7 ))
			mycol=next(colors)
			self.c_guv_end_Boff.append(self.p0.plot(pen=pg.mkPen(mycol,width=1), symbol='o', symbolPen=mycol, symbolBrush=mycol, symbolSize=3))
			self.c_guv_all_Boff.append(self.p1.plot(pen=pg.mkPen(mycol,width=1), symbol='o', symbolPen='r', symbolBrush='r', symbolSize=7 ))
		
		self.my_legend = self.p0.addLegend()
		
		if not self.prepare_file():
			QMessageBox.critical(self, 'Message','Scan terminated due to problems creating file or folder(s)')
			return
			
		self.timer.stop()
		
		self.abortButton.setEnabled(True)
		self.pauseButton.setEnabled(True)
		
		self.write2file.setEnabled(False)
		self.fileLoadAs.setEnabled(False)
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
		self.combo8.setEnabled(False)
		self.combo9.setEnabled(False)
		self.combo10.setEnabled(False)
		self.combo11.setEnabled(False)
		self.combo12.setEnabled(False)
		self.combo13.setEnabled(False)
		
		self.tabs.setCurrentIndex(0)
		self.runButton.setText("Scaning...")
		self.isRunning = True
		
		shutter_list={'shutset':self.shutset}
		pos_list={'posset':self.posset,'posA_delay':self.posA_delay, 'posB_delay':self.posB_delay, 'posAB_delay':self.posAB_delay}
		self.sssd = [start_, stop, step, dwell]
		
		self.md = Indicator_invs_dialog.Indicator_invs_dialog(self, "...preparing scan...", "green", "indicators"+os.sep+"ajax-loader-green-ball2.gif")
		
		obj = type('setscan_obj',(object,),{'inst_list':self.inst_list, 'unit':self.unit_str, 'grating':self.grating_str, 'avgpts':[self.avgpts_a,self.avgpts_b], 'shutter_list':shutter_list, 'pos_list':pos_list, 'sssd':self.sssd})
		
		self.worker=Scan_Worker.Scan_Worker(obj)
		
		self.worker.signals.update_movie.connect(self.update_movie)
		
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
		
		
		
	def update_movie(self,pyqt_object):
		
		if pyqt_object=='stop':
			self.md.close_()
		
		
	def update_end_k2001a(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime, my_legend = pyqt_object
		self.time_counter+=1
		
		#################################################
		
		if self.posnow=="A":
			if self.shutnow=="on":
				self.wl_k2001a_end_Aon.extend([ wl ])
				self.volt_k2001a_end_Aon.extend([ volt ])
				self.c_k2001a_end_Aon.setData(self.wl_k2001a_end_Aon, numpy.abs(self.volt_k2001a_end_Aon))
				if len(self.wl_k2001a_end_Aon)==1:
					self.my_legend.addItem(self.c_k2001a_end_Aon, name=''.join(['K2001A, ',my_legend]))
					
			elif self.shutnow in ["off","?"]:
				self.wl_k2001a_end_Aoff.extend([ wl ])
				self.volt_k2001a_end_Aoff.extend([ volt ])
				self.c_k2001a_end_Aoff.setData(self.wl_k2001a_end_Aoff, numpy.abs(self.volt_k2001a_end_Aoff))
				if len(self.wl_k2001a_end_Aoff)==1:
					self.my_legend.addItem(self.c_k2001a_end_Aoff, name=''.join(['K2001A, ',my_legend]))
			
		elif self.posnow in ["B","?"]:
			if self.shutnow=="on":
				self.wl_k2001a_end_Bon.extend([ wl ])
				self.volt_k2001a_end_Bon.extend([ volt ])
				self.c_k2001a_end_Bon.setData(self.wl_k2001a_end_Bon, numpy.abs(self.volt_k2001a_end_Bon))
				if len(self.wl_k2001a_end_Bon)==1:
					self.my_legend.addItem(self.c_k2001a_end_Bon, name=''.join(['K2001A, ',my_legend]))
					
			elif self.shutnow in ["off","?"]:
				self.wl_k2001a_end_Boff.extend([ wl ])
				self.volt_k2001a_end_Boff.extend([ volt ])
				self.c_k2001a_end_Boff.setData(self.wl_k2001a_end_Boff, numpy.abs(self.volt_k2001a_end_Boff))
				if len(self.wl_k2001a_end_Boff)==1:
					self.my_legend.addItem(self.c_k2001a_end_Boff, name=''.join(['K2001A, ',my_legend]))
		
		#################################################
		
		if my_legend[-1]==u'\u0394':
			insttype_str = "K2001A"+" ("+u'\u0394'+")"
		else:
			insttype_str = "K2001A"
		
		#################################################
		
		self.detector_.extend([insttype_str])
		self.ms257_in_.extend([ms257_in])
		self.ms257_out_.extend([ms257_out])
		self.wl_k2001a.extend([wl]) 
		self.volt_k2001a.extend([volt])
		self.pos_.extend([self.posnow])
		self.shutter_.extend([self.shutnow])
		self.time_k2001a.extend([time])
		self.dateandtime_k2001a.extend([dateandtime])
		
		#################################################
		
		if self.write2db_check:
			# Save to a sqlite3 file
			'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, timetrace real, absolutetime text)'''
			self.db.execute(''.join(["INSERT INTO keithley VALUES ('",ms257_in,"','", ms257_out,"',", str(abs(volt)), ",'", self.posnow,"','", self.shutnow, "','", time, "','", dateandtime,"','", my_legend ,"')"]))
			# Save (commit) the changes
			self.conn.commit()
			
		#################################################
		
		if self.write2hdf5_check:
			with h5py.File(self.hdf5file, 'a') as f:
				#print("hdf5, detector:", type(insttype_str))
				dset = f["detector"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = insttype_str
				
				#print("hdf5, ms257_in:", type(ms257_in))
				dset = f["ms257_in"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = ms257_in
				
				#print("hdf5, ms257_out:", type(ms257_out))
				dset = f["ms257_out"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = ms257_out
				
				#print("hdf5, volt:", type(volt))
				dset = f["k2001a_signal"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = volt
				
				dset = f["wavelength"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = wl
				
				#print("hdf5, posnow:", type(self.posnow))
				dset = f["mirrorpos"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = self.posnow
				
				dset = f["shutter"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = self.shutnow
				
				#print("hdf5, time:", type(time))
				dset = f["timetrace"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = time
				
				#print("hdf5, dateandtime:", type(dateandtime))
				dset = f["absolutetime"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = dateandtime
				
		#################################################
		
		if self.write2mat_check:
			# save to a MATLAB file
			matdata={}
			matdata["detector"]=self.detector_
			matdata["ms257_in"]=self.ms257_in_
			matdata["ms257_out"]=self.ms257_out_
			matdata["k2001a_signal"]=self.volt_k2001a
			matdata["a34972a_signal"]=self.volt_a34972a
			matdata["guv_signal"]=numpy.array(self.volt_guv)
			matdata["wavelength"]=self.wl_k2001a
			matdata["mirrorpos"]=self.pos_
			matdata["shutter"]=self.shutter_
			matdata["timetrace"]=self.time_k2001a
			matdata["absolutetime"]=self.dateandtime_k2001a
			
			scipy.io.savemat(self.matfile, matdata)
			#print(scipy.io.loadmat(self.matfile).keys()) 
			#b = scipy.io.loadmat(self.matfile)
			#print(b["wavelength"])
		
		#################################################
		
		if self.write2txt_check:
			# Save to a readable textfile
			with open(self.textfile, 'a', encoding="utf-8") as thefile:
				thefile.write("%s " %insttype_str)
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
		self.tableWidget.setRowHeight(self.tal,12)
		#self.tableWidget.resizeRowToContents(self.tal)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem(insttype_str))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem( str(wl) ))
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem(format(volt, ".3e" )) )
		self.tableWidget.setItem(self.tal, 3, QTableWidgetItem(self.posnow) )
		self.tableWidget.setItem(self.tal, 4, QTableWidgetItem(self.shutnow) )
		self.tableWidget.setItem(self.tal, 5, QTableWidgetItem(format(float(time),".2f") ))
		
		
		
		
		
	def update_end_a34972a(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime, my_legend = pyqt_object
		self.time_counter+=1
		
		#################################################
			
		if self.posnow=="A":
			if self.shutnow=="on":
				self.wl_a34972a_end_Aon.extend([ wl ])
				self.volt_a34972a_end_Aon.extend([ volt ])
				self.c_a34972a_end_Aon.setData(self.wl_a34972a_end_Aon, numpy.abs(self.volt_a34972a_end_Aon))
				if len(self.wl_a34972a_end_Aon)==1:
					self.my_legend.addItem(self.c_a34972a_end_Aon, name=''.join(["A34972A, ",my_legend]))
					
			elif self.shutnow in ["off","?"]:
				self.wl_a34972a_end_Aoff.extend([ wl ])
				self.volt_a34972a_end_Aoff.extend([ volt ])
				self.c_a34972a_end_Aoff.setData(self.wl_a34972a_end_Aoff, numpy.abs(self.volt_a34972a_end_Aoff))
				if len(self.wl_a34972a_end_Aoff)==1:
					self.my_legend.addItem(self.c_a34972a_end_Aoff, name=''.join(["A34972A, ",my_legend]))
				
		elif self.posnow in ["B","?"]:
			if self.shutnow=="on":
				self.wl_a34972a_end_Bon.extend([ wl ])
				self.volt_a34972a_end_Bon.extend([ volt ])
				self.c_a34972a_end_Bon.setData(self.wl_a34972a_end_Bon, numpy.abs(self.volt_a34972a_end_Bon))
				if len(self.wl_a34972a_end_Bon)==1:
						self.my_legend.addItem(self.c_a34972a_end_Bon, name=''.join(["A34972A, ",my_legend]))
					
			elif self.shutnow in ["off","?"]:
				self.wl_a34972a_end_Boff.extend([ wl ])
				self.volt_a34972a_end_Boff.extend([ volt ])
				self.c_a34972a_end_Boff.setData(self.wl_a34972a_end_Boff, numpy.abs(self.volt_a34972a_end_Boff))
				if len(self.wl_a34972a_end_Boff)==1:
					self.my_legend.addItem(self.c_a34972a_end_Boff, name=''.join(["A34972A, ",my_legend]))
		
		#################################################
		
		if my_legend[-1]==u'\u0394':
			insttype_str = "Agilent"+" ("+u'\u0394'+")"
		else:
			insttype_str = "Agilent"
		
		#################################################
		
		self.detector_.extend([insttype_str])
		self.ms257_in_.extend([ms257_in])
		self.ms257_out_.extend([ms257_out])
		self.wl_a34972a.extend([wl])
		self.volt_a34972a.extend([volt])
		self.pos_.extend([self.posnow])
		self.shutter_.extend([self.shutnow])
		self.time_a34972a.extend([time])
		self.dateandtime_a34972a.extend([dateandtime])
		
		#################################################
		
		if self.write2db_check:
			# Save to a sqlite3 file
			'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, timetrace real, absolutetime text)'''
			self.db.execute(''.join(["INSERT INTO agilent VALUES ('",ms257_in,"','", ms257_out,"',", str(abs(volt)), ",'", self.posnow,"','", self.shutnow, "','", time, "','", dateandtime,"','", my_legend,"')"]))
			# Save (commit) the changes
			self.conn.commit()
		
		#################################################
		
		if self.write2hdf5_check:
			with h5py.File(self.hdf5file, 'a') as f:
				dset = f["detector"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = insttype_str
				
				dset = f["ms257_in"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = ms257_in
				
				dset = f["ms257_out"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = ms257_out
				
				dset = f["a34972a_signal"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = volt
				
				dset = f["wavelength"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = wl
				
				dset = f["mirrorpos"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = self.posnow
				
				dset = f["shutter"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = self.shutnow
				
				dset = f["timetrace"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = time
				
				dset = f["absolutetime"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = dateandtime
				
		#################################################
		
		if self.write2mat_check:
			# save to a MATLAB file
			matdata={}
			matdata["detector"]=self.detector_
			matdata["ms257_in"]=self.ms257_in_
			matdata["ms257_out"]=self.ms257_out_
			matdata["k2001a_signal"]=self.volt_k2001a
			matdata["a34972a_signal"]=self.volt_a34972a
			matdata["guv_signal"]=numpy.array(self.volt_guv)
			matdata["wavelength"]=self.wl_a34972a
			matdata["mirrorpos"]=self.pos_
			matdata["shutter"]=self.shutter_
			matdata["timetrace"]=self.time_a34972a
			matdata["absolutetime"]=self.dateandtime_a34972a
			
			scipy.io.savemat(self.matfile, matdata)
			#print(scipy.io.loadmat(self.matfile).keys()) 
			#b = scipy.io.loadmat(self.matfile)
			#print(b['wavelength'])
		
		#################################################
		
		if self.write2txt_check:
			# Save to a readable textfile
			with open(self.textfile, 'a', encoding="utf-8") as thefile:
				thefile.write("%s " %insttype_str)
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
		#self.tableWidget.resizeRowToContents(self.tal)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem(insttype_str))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem( str(wl) ))
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem(format(volt, ".3e" )) )
		self.tableWidget.setItem(self.tal, 3, QTableWidgetItem(self.posnow) )
		self.tableWidget.setItem(self.tal, 4, QTableWidgetItem(self.shutnow) )
		self.tableWidget.setItem(self.tal, 5, QTableWidgetItem(format(float(time),".2f") ))
				
				
				
				
				
				
				
	def update_end_guv(self,pyqt_object):
		
		ms257_in, ms257_out, wl, volt, time, dateandtime, my_legend = pyqt_object
		self.time_counter+=1
		
		#################################################
		
		if self.posnow=="A":
			if self.shutnow=="on":
				self.wl_guv_end_Aon.append( [wl]*len(volt) )
				self.volt_guv_end_Aon.append( [abs(i) for i in volt] )
				
				wl_ = list(map(list, zip(*self.wl_guv_end_Aon)))
				signal_ = list(map(list, zip(*self.volt_guv_end_Aon)))
				for i in range(len(wl_)):
					self.c_guv_end_Aon[i].setData(wl_[i], signal_[i])
					if len(self.wl_guv_end_Aon)==1:
						self.my_legend.addItem(self.c_guv_end_Aon[i], name=''.join([self.guvtype_str,', ',my_legend,' ch.',self.guv_channels[i]]) )
					
			elif self.shutnow in ["off","?"]:
				self.wl_guv_end_Aoff.append( [wl]*len(volt) )
				self.volt_guv_end_Aoff.append( [abs(i) for i in volt] )
				
				wl_ = list(map(list, zip(*self.wl_guv_end_Aoff)))
				signal_ = list(map(list, zip(*self.volt_guv_end_Aoff)))
				for i in range(len(wl_)):
					self.c_guv_end_Aoff[i].setData(wl_[i], signal_[i])
					if len(self.wl_guv_end_Aoff)==1:
						self.my_legend.addItem(self.c_guv_end_Aoff[i], name=''.join([self.guvtype_str,', ',my_legend,' ch.',self.guv_channels[i]]) )
						
		elif self.posnow in ["B","?"]:
			if self.shutnow=="on":
				self.wl_guv_end_Bon.append( [wl]*len(volt) )
				self.volt_guv_end_Bon.append( [abs(i) for i in volt] )
				
				wl_ = list(map(list, zip(*self.wl_guv_end_Bon)))
				signal_ = list(map(list, zip(*self.volt_guv_end_Bon)))
				for i in range(len(wl_)):
					self.c_guv_end_Bon[i].setData(wl_[i], signal_[i])
					if len(self.wl_guv_end_Bon)==1:
						self.my_legend.addItem(self.c_guv_end_Bon[i], name=''.join([self.guvtype_str,', ',my_legend,' ch.',self.guv_channels[i]]) )
					
			elif self.shutnow in ["off","?"]:
				self.wl_guv_end_Boff.append( [wl]*len(volt) )
				self.volt_guv_end_Boff.append( [abs(i) for i in volt] )
				
				wl_ = list(map(list, zip(*self.wl_guv_end_Boff)))
				signal_ = list(map(list, zip(*self.volt_guv_end_Boff)))
				for i in range(len(wl_)):
					self.c_guv_end_Boff[i].setData(wl_[i], signal_[i])
					if len(self.wl_guv_end_Boff)==1:
						self.my_legend.addItem(self.c_guv_end_Boff[i], name=''.join([self.guvtype_str,', ',my_legend,' ch.',self.guv_channels[i]]) )
		
		
		#################################################
		
		if my_legend[-1]==u'\u0394':
			guvtype_str = self.guvtype_str+" ("+u'\u0394'+")"
		else:
			guvtype_str = self.guvtype_str
		
		#################################################
		
		self.detector_.extend([guvtype_str])
		self.ms257_in_.extend([ms257_in])
		self.ms257_out_.extend([ms257_out])
		self.wl_guv.extend([wl])
		self.volt_guv.append([abs(i) for i in volt])
		self.pos_.extend([self.posnow])
		self.shutter_.extend([self.shutnow])
		self.time_guv.extend([time])
		self.dateandtime_guv.extend([dateandtime])
		
		#################################################
		
		if self.write2db_check:
			# Save to a sqlite3 file
			'''CREATE TABLE spectra (wavelength real, voltage real, position text, shutter real, timetrace real, absolutetime text)'''
			self.db.execute(''.join(["INSERT INTO guv VALUES ('", self.guvtype_str ,"','",ms257_in,"','",ms257_out,"','", str(list(abs(i) for i in volt)),"','", str(list(int(i) for i in self.guv_channels)),"','",my_legend,"','", self.posnow,"','", self.shutnow, "','", time, "','", dateandtime, "')"]))
			# Save (commit) the changes
			self.conn.commit()
		
		#################################################
		
		if self.write2hdf5_check:
			with h5py.File(self.hdf5file, 'a') as f:
				dset = f["detector"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = guvtype_str
				
				dset = f["ms257_in"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = ms257_in
				
				dset = f["ms257_out"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = ms257_out
				
				dset = f["guv_signal"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = numpy.array([abs(i) for i in volt])
				
				dset = f["wavelength"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = wl
				
				dset = f["mirrorpos"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = self.posnow
				
				dset = f["shutter"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = self.shutnow
				
				dset = f["timetrace"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = time
				
				dset = f["absolutetime"]
				#print("dset: ",dset.size)
				dset.resize((dset.size+1,))
				dset[-1] = dateandtime
				
		#################################################
		
		if self.write2mat_check:
			# save to a MATLAB file
			matdata={}
			matdata["detector"]=self.detector_
			matdata["ms257_in"]=self.ms257_in_
			matdata["ms257_out"]=self.ms257_out_
			matdata["k2001a_signal"]=self.volt_k2001a
			matdata["a34972a_signal"]=self.volt_a34972a
			matdata["guv_signal"]=numpy.array(self.volt_guv)
			matdata["wavelength"]=self.wl_guv
			matdata["mirrorpos"]=self.pos_
			matdata["shutter"]=self.shutter_
			matdata["timetrace"]=self.time_guv
			matdata["absolutetime"]=self.dateandtime_guv
			
			scipy.io.savemat(self.matfile, matdata)
			#print(scipy.io.loadmat(self.matfile).keys()) 
			#b = scipy.io.loadmat(self.matfile)
			#print(b['wavelength'])
		
		#################################################
		
		if self.write2txt_check:
			# Save to a readable textfile
			with open(self.textfile, 'a', encoding="utf-8") as thefile:
				thefile.write("%s " %guvtype_str)
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
		#self.tableWidget.resizeRowToContents(self.tal)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem(guvtype_str))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem( str(wl) ))
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem( ', '.join([format(i, ".3e" ) for i in volt]) ))
		self.tableWidget.setItem(self.tal, 3, QTableWidgetItem(self.posnow) )
		self.tableWidget.setItem(self.tal, 4, QTableWidgetItem(self.shutnow) )
		self.tableWidget.setItem(self.tal, 5, QTableWidgetItem(format(float(time),".2f") ))
				
				
				
				
				
	def update_all_k2001a(self,pyqt_object):
		
		volt, time = pyqt_object
		self.time_counter+=1
		#################################################
		
		if self.posnow=="A":
			if self.shutnow=="on":
				self.time_k2001a_all_Aon.extend([ float(time) ])
				self.volt_k2001a_all_Aon.extend([ float(volt) ])
				self.c_k2001a_all_Aon.setData(self.time_k2001a_all_Aon, self.volt_k2001a_all_Aon)
			elif self.shutnow in ["off","?"]:
				self.time_k2001a_all_Aoff.extend([ float(time) ])
				self.volt_k2001a_all_Aoff.extend([ float(volt) ])
				self.c_k2001a_all_Aoff.setData(self.time_k2001a_all_Aoff, self.volt_k2001a_all_Aoff)
				
		elif self.posnow in ["B","?"]:
			if self.shutnow=="on":
				self.time_k2001a_all_Bon.extend([ float(time) ])
				self.volt_k2001a_all_Bon.extend([ float(volt) ])
				self.c_k2001a_all_Bon.setData(self.time_k2001a_all_Bon, self.volt_k2001a_all_Bon)
			elif self.shutnow in ["off","?"]:
				self.time_k2001a_all_Boff.extend([ float(time) ])
				self.volt_k2001a_all_Boff.extend([ float(volt) ])
				self.c_k2001a_all_Boff.setData(self.time_k2001a_all_Boff, self.volt_k2001a_all_Boff)
				
				
				
	def update_all_a34972a(self,pyqt_object):
		
		volt, time = pyqt_object
		self.time_counter+=1
		#################################################
		
		if self.posnow=="A":
			if self.shutnow=="on":
				self.time_a34972a_all_Aon.extend([ float(time) ])
				self.volt_a34972a_all_Aon.extend([ float(volt) ])
				self.c_a34972a_all_Aon.setData(self.time_a34972a_all_Aon, self.volt_a34972a_all_Aon)
			elif self.shutnow in ["off","?"]:
				self.time_a34972a_all_Aoff.extend([ float(time) ])
				self.volt_a34972a_all_Aoff.extend([ float(volt) ])
				self.c_a34972a_all_Aoff.setData(self.time_a34972a_all_Aoff, self.volt_a34972a_all_Aoff)
				
		elif self.posnow in ["B","?"]:
			if self.shutnow=="on":
				self.time_a34972a_all_Bon.extend([ float(time) ])
				self.volt_a34972a_all_Bon.extend([ float(volt) ])
				self.c_a34972a_all_Bon.setData(self.time_a34972a_all_Bon, self.volt_a34972a_all_Bon)
			elif self.shutnow in ["off","?"]:
				self.time_a34972a_all_Boff.extend([ float(time) ])
				self.volt_a34972a_all_Boff.extend([ float(volt) ])
				self.c_a34972a_all_Boff.setData(self.time_a34972a_all_Boff, self.volt_a34972a_all_Boff)
				
				
	def update_all_guv(self,pyqt_object):
		
		volt, time = pyqt_object
		self.time_counter+=1
		#################################################
		
		if self.posnow=="A":
			if self.shutnow=="on":
				self.time_guv_all_Aon.append( [float(time)]*len(volt) )
				self.volt_guv_all_Aon.append( [abs(i) for i in volt] )
				
				time_ = list(map(list, zip(*self.time_guv_all_Aon)))
				signal_ = list(map(list, zip(*self.volt_guv_all_Aon)))
				for i in range(len(time_)):
					self.c_guv_all_Aon[i].setData(time_[i], signal_[i])
				
			elif self.shutnow in ["off","?"]:
				self.time_guv_all_Aoff.append( [float(time)]*len(volt) )
				self.volt_guv_all_Aoff.append( [abs(i) for i in volt] )
				
				time_ = list(map(list, zip(*self.time_guv_all_Aoff)))
				signal_ = list(map(list, zip(*self.volt_guv_all_Aoff)))
				for i in range(len(time_)):
					self.c_guv_all_Aoff[i].setData(time_[i], signal_[i])
					
		elif self.posnow in ["B","?"]:
			if self.shutnow=="on":
				self.time_guv_all_Bon.append( [float(time)]*len(volt) )
				self.volt_guv_all_Bon.append( [abs(i) for i in volt] )
				
				time_ = list(map(list, zip(*self.time_guv_all_Bon)))
				signal_ = list(map(list, zip(*self.volt_guv_all_Bon)))
				for i in range(len(time_)):
					self.c_guv_all_Bon[i].setData(time_[i], signal_[i])
					
			elif self.shutnow in ["off","?"]:
				self.time_guv_all_Boff.append( [float(time)]*len(volt) )
				self.volt_guv_all_Boff.append( [abs(i) for i in volt] )
				
				time_ = list(map(list, zip(*self.time_guv_all_Boff)))
				signal_ = list(map(list, zip(*self.volt_guv_all_Boff)))
				for i in range(len(time_)):
					self.c_guv_all_Boff[i].setData(time_[i], signal_[i])
				
				
	def update_wl_time(self,pyqt_object):
		
		wl, time = pyqt_object
		self.time_counter+=1
		#################################################
		
		if self.time_counter > self.schroll_pts:
			self.time[:-1] = self.time[1:]  # shift data in the array one sample left
			self.time[-1] = float(time)
			self.wl[:-1] = self.wl[1:]  # shift data in the array one sample left
			self.wl[-1] = wl
		else:
			self.time.extend([ float(time) ])
			self.wl.extend([ wl ])
			
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
		
		self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
		self.p2.enableAutoRange()
		
		#self.time.extend([ float(time) ])
		#self.wl.extend([ wl ])
		self.c_time_wl.setData(self.time, self.wl)
		
		
	def update_shutter(self,onoff):
		
		self.shutnow = onoff
		
		self.config.read("config.ini")
		self.config.set(self.last_used_scan,"shutter", ','.join([self.shutset, self.shutnow]) )
		with open("config.ini", 'w') as configfile:
			self.config.write(configfile)
			
		self.shind_lbl.setText(''.join([" Shutter ", self.shutnow.upper()]))
		if self.shutnow=="on":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkGreen; border-radius: 10px; background-color: green}")
		elif self.shutnow=="off":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkRed; border-radius: 10px; background-color: red}")
		elif self.shutnow=="?":
			self.shind_lbl.setStyleSheet("QWidget {border: 2px solid darkGrey; border-radius: 10px; background-color: grey}")
			
			
	def update_oriel(self,aorb):
		
		self.posnow = aorb
		
		self.config.read("config.ini")
		self.config.set(self.last_used_scan,"pos", ','.join([self.posset, self.posnow]) )
		with open("config.ini", 'w') as configfile:
			self.config.write(configfile)
			
		self.posind_lbl.setText(''.join([" Position ", self.posnow]))
		if self.posnow=="A":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkYellow; border-radius: 10px; background-color: yellow}")
		elif self.posnow=="B":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkMagenta; border-radius: 10px; background-color: magenta}")
			self.avgptsB_lbl.setText("Pos B")
			self.posB_delay_lbl.setText("Pos B")
		elif self.posnow=="?":
			self.posind_lbl.setStyleSheet("QWidget {border: 2px solid darkGrey; border-radius: 10px; background-color: grey}")
			self.avgptsB_lbl.setText("Pos ?")
			self.posB_delay_lbl.setText("Pos ?")
			
			
	def make_3Dplot(self):
		
		try:
			wl_ = [float(i) for i in self.wl_]
			time_ = [float(i) for i in self.time_]
			volt_ = [float(i) for i in self.volt_]
		except ValueError:
			return
		
		fig=plt.figure(figsize=(8,6))
		ax= fig.add_subplot(111, projection="3d")
		
		ax.plot(wl_, time_, volt_, linewidth=1)
		#ax=fig.gca(projection="2d")
		ax.set_xlabel(''.join(["lambda[",self.unit_str,"]"]))
		ax.set_ylabel("Time[s]")
		ax.set_zlabel("Signal")
		
		plt.show()
		#fig.savefig(''.join(['plot_',self.time_str,'_3D.png']))
		
		
	def set_disconnect(self):
		
		##########################################
		
		if self.inst_list.get("MS257_in"):
			if self.inst_list.get("MS257_in").is_open():
				self.inst_list.get("MS257_in").close()
			self.inst_list.pop("MS257_in", None)
				
		##########################################
		
		if self.inst_list.get("MS257_out"):
			if self.inst_list.get("MS257_out").is_open():
				self.inst_list.get("MS257_out").close()
			self.inst_list.pop("MS257_out", None)
			
		##########################################
		
		if self.inst_list.get("Oriel"):
			if self.inst_list.get("Oriel").is_open():
				self.inst_list.get("Oriel").close()
			self.inst_list.pop("Oriel", None)
				
		##########################################
		
		if self.inst_list.get("K2001A"):
			if self.inst_list.get("K2001A").is_open():
				self.inst_list.get("K2001A").close()
			self.inst_list.pop("K2001A", None)
			
		##########################################
		
		if self.inst_list.get("Agilent34972A"):
			if self.inst_list.get("Agilent34972A").is_open():
				self.inst_list.get("Agilent34972A").close()
			self.inst_list.pop("Agilent34972A", None)
			
		##########################################
		
		if self.inst_list.get("GUV"):
			if self.inst_list.get("GUV").is_open():
				self.inst_list.get("GUV").close()
			self.inst_list.pop("GUV", None)
			
		##########################################
		
		keys = self.inst_list.keys() & ["MS257_in","MS257_out","Oriel","K2001A","Agilent34972A","GUV"]
		if not keys:
			self.runButton.setText("Load instrument!")
			self.runButton.setEnabled(False)
		else:
			self.runButton.setText("Scan")
			self.runButton.setEnabled(True)
		
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
			
			
			
	def plotfile(self, index):
		
		
		myfile = self.sender().model().filePath(index)
		head, tail = os.path.split(myfile)
		
		###############################################
		
		if tail[-3:]!=".db":
			QMessageBox.critical(self, "Message","Only sql files (*.db) are plotable!")
			return
		
		else:
			conn = sqlite3.connect(myfile)
			db = conn.cursor()
			
			# all curves plotted
			curves_guv = []
			curves_k2001a = []
			curves_agilent = []
			
			# all the legends
			guv_channels = []
			legends = []
			
			keithley_legends=[]
			agilent_legends=[]
			
			# signals
			signal_agilent=[]
			signal_keithley=[]
			signal_guv=[]
			
			# wavelength
			ms257_in=[]
			
			###################################################
			
			win = pg.GraphicsWindow()
			p0 = win.addPlot()
			my_legend = p0.addLegend()
			
			self.tabs.addTab(win,tail)
			self.tabIndex+=1
			self.tabs.setCurrentIndex(self.tabIndex)
			
			p0.enableAutoRange()
			p0.setLabel("left", "Signal", units="", color="green")
			p0.setLabel("bottom", "Wavelength", units=self.unit_str, color="white")
			#self.p0.setLogMode(y=True)
			
			colors = itertools.cycle(["r", "b", "g", "y", "m", "c", "w"])
			#colors = itertools.cycle([tuple(int(i) for i in numpy.array(cm.jet(i))[:-1]*255) for i in numpy.arange(20,250,len(self.guv_channels))])
			
			try:
				guv_legends=[]
				for i in db.execute("SELECT legend FROM guv ORDER BY timetrace ASC"):
					guv_legends.extend(list(i))
			except Exception as e:
				QMessageBox.warning(self, "Message",''.join(["Some GUV parameters are missing! Use this software produced sql file format (.db).\n\n",str(e)]))
				
			legends_counter = collections.Counter(guv_legends)
			legends_guv = list(legends_counter.keys())
			#print(legends_counter.values())
			
			for ii,tal in zip(legends_guv,range(len(legends_guv))):
				signal_guv.append([])
				ms257_in.append([])
				curves_guv.append([])
				
				for ms257_in_, signal_, channels_, legend_, timetrace, guvtype in db.execute("SELECT ms257_in, signal, channels, legend, timetrace, guvtype FROM guv WHERE legend=? ORDER BY timetrace ASC", (ii,)):
					signal_guv[tal].append(eval(signal_))
					ms257_in[tal].append([float(ms257_in_)]*len(eval(signal_)))
				
				legends.append([legend_]*len(eval(signal_)))
				guv_channels.append(eval(channels_))
				
				signal_guv[tal] = list(map(list, zip(*signal_guv[tal])))
				ms257_in[tal] = list(map(list, zip(*ms257_in[tal])))
				
				for _ in range(len(signal_guv[tal])):
					mycol=next(colors)
					curves_guv[tal].append(p0.plot(pen=pg.mkPen(mycol,width=1), symbol="d", symbolPen=mycol, symbolBrush=mycol, symbolSize=3))
				
				for i in range(len(signal_guv[tal])):
					curves_guv[tal][i].setData(ms257_in[tal][i], signal_guv[tal][i])
					my_legend.addItem(curves_guv[tal][i], name=''.join([guvtype,", ",legends[tal][i],", ch.",str(guv_channels[tal][i])]) )
				
			#################################################
			#################################################
			#################################################
		
			try:
				for legend_ in db.execute("SELECT legend FROM keithley ORDER BY timetrace ASC"):
					keithley_legends.extend(list(legend_))
			except Exception as e:
				QMessageBox.warning(self, "Message",''.join(["Some Keithely parameters are missing! Use this software produced sql file format (.db).\n\n",str(e)]))
			
			legends_counter = collections.Counter(keithley_legends)
			legends_keithley = list(legends_counter.keys())
			ms257_in = []
			legends = []
			
			for ii in legends_keithley:
				signal_keithley.append([])
				ms257_in.append([])
				
				for ms257_in_, signal_, legend_, timetrace in db.execute("SELECT ms257_in, signal, legend, timetrace FROM keithley WHERE legend=? ORDER BY timetrace ASC", (ii,)):
					signal_keithley[-1].append(signal_)
					ms257_in[-1].append(float(ms257_in_))
				
				legends.append(legend_)
				
				mycol=next(colors)
				curves_k2001a.append(p0.plot(pen=pg.mkPen(mycol,width=4, style=QtCore.Qt.DashLine), symbol="s", symbolPen=mycol, symbolBrush=mycol, symbolSize=5))
				
				curves_k2001a[-1].setData(ms257_in[-1], signal_keithley[-1])
				my_legend.addItem(curves_k2001a[-1], name=''.join(["K2001A, ",legends[-1]]) )
			
			#################################################
			#################################################
			#################################################
			
			try:
				for legend in db.execute("SELECT legend FROM agilent ORDER BY timetrace ASC"):
					agilent_legends.extend(list(legend))
			except Exception as e:
				QMessageBox.warning(self, "Message",''.join(["Some Agilent parameters are missing! Use this software produced sql file format (.db).\n\n",str(e)]))
			
			legends_counter = collections.Counter(agilent_legends)
			legends_agilent = list(legends_counter.keys())
			ms257_in = []
			legends = []
			
			for ii in legends_agilent:
				signal_agilent.append([])
				ms257_in.append([])
				
				for ms257_in_, signal_, legend_, timetrace in db.execute("SELECT ms257_in, signal, legend, timetrace FROM agilent WHERE legend=? ORDER BY timetrace ASC", (ii,)):
					signal_agilent[-1].append(signal_)
					ms257_in[-1].append(float(ms257_in_))
				
				legends.append(legend_)
				
				mycol=next(colors)
				curves_agilent.append(p0.plot(pen=pg.mkPen(mycol,width=4, style=QtCore.Qt.SolidLine), symbol="d", symbolPen=mycol, symbolBrush=mycol, symbolSize=5))
				
				curves_agilent[-1].setData(ms257_in[-1], signal_agilent[-1])
				my_legend.addItem(curves_agilent[-1], name=''.join(["A34972A, ",legends[-1]]) )
				
				
				
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
		if self.inst_list.get("K2001A") or self.inst_list.get("Agilent34972A") or self.inst_list.get("GUV"):
			#self.make_3Dplot()
			if self.write2db_check:
				self.conn.close()
				
		self.load_()
		
		if self.emailset_str[1] == "yes":
			self.send_notif()
		if self.emailset_str[2] == "yes":
			self.send_data()
			
		self.isRunning = False
		
		self.abortButton.setEnabled(False)
		self.pauseButton.setEnabled(False)
		
		self.write2file.setEnabled(True)
		self.fileLoadAs.setEnabled(True)
		self.conMode.setEnabled(True)
		self.testMenu.setEnabled(True)
		self.startEdit.setEnabled(True)
		self.stopEdit.setEnabled(True)
		self.stepEdit.setEnabled(True)
		self.dwelltimeEdit.setEnabled(True)
		self.combo12.setEnabled(True)
		self.combo13.setEnabled(True)
		
		keys = self.inst_list.keys() & ["MS257_in","MS257_out","Oriel","K2001A","Agilent34972A","GUV"]
		
		if not keys:
			self.runButton.setText("Load instrument!")
			self.runButton.setEnabled(False)
		else:
			self.runButton.setText("Scan")
			self.runButton.setEnabled(True)
		
		if self.inst_list.get("MS257_in") or self.inst_list.get("MS257_out"):
			self.combo3.setEnabled(True)
			self.combo9.setEnabled(True)
		else:
			self.combo3.setEnabled(False)
			self.combo9.setEnabled(False)
		
		if self.inst_list.get("Oriel"):
			self.combo5.setEnabled(True)
			self.combo11.setEnabled(True)
			if self.posset=="A":
				self.combo6.setEnabled(True)
				self.combo7.setEnabled(False)
				if self.inst_list.get("GUV") or self.inst_list.get("K2001A") or self.inst_list.get("Agilent34972A"):
					self.combo8.setEnabled(True)
					self.combo10.setEnabled(False)
			elif self.posset=="B":
				self.combo6.setEnabled(False)
				self.combo7.setEnabled(True)
				self.posB_delay_lbl.setText("Pos B")
				if self.inst_list.get("GUV") or self.inst_list.get("K2001A") or self.inst_list.get("Agilent34972A"):
					self.combo8.setEnabled(False)
					self.combo10.setEnabled(True)
					self.avgptsB_lbl.setText("Pos B")
			elif self.posset=="A<->B":
				self.combo6.setEnabled(True)
				self.combo7.setEnabled(True)
				self.posB_delay_lbl.setText("Pos B")
				if self.inst_list.get("GUV") or self.inst_list.get("K2001A") or self.inst_list.get("Agilent34972A"):
					self.combo8.setEnabled(True)
					self.combo10.setEnabled(True)
					self.avgptsB_lbl.setText("Pos B")
		else:
			self.combo5.setEnabled(False)
			self.combo11.setEnabled(False)
			
			self.combo6.setEnabled(False)
			self.combo7.setEnabled(True)
			self.posB_delay_lbl.setText("Pos ?")
			if self.inst_list.get("GUV") or self.inst_list.get("K2001A") or self.inst_list.get("Agilent34972A"):
				self.combo8.setEnabled(False)
				self.combo10.setEnabled(True)
				self.avgptsB_lbl.setText("Pos ?")
		
		if self.inst_list.get("MS257_in"):
			self.combo4.setEnabled(True)
		else:
			self.combo4.setEnabled(False)
		
		self.timer.start(1000*300)
		
		
	def warning(self, mystr):
		
		QMessageBox.warning(self, "Message", mystr)
		
		
	def critical(self, mystr):
		
		QMessageBox.critical(self, "Message", mystr)
		
		
	def send_notif(self):
		
		self.md1 = Indicator_dialog.Indicator_dialog(self, "...sending files...", "indicators"+os.sep+"ajax-loader-ball.gif")
		
		contents=["The scan is done. Please visit the experiment site and make sure that all light sources are switched off."]
		subject="The scan is done"
		
		obj = type("obj",(object,),{"subject":subject, "contents":contents, "settings":self.emailset_str, "receivers":self.emailrec_str})
		
		worker=Email_Worker(obj)
		worker.signals.critical.connect(self.critical)
		worker.signals.warning.connect(self.warning)
		worker.signals.finished.connect(self.finished1)
		
		# Execute
		self.threadpool.start(worker)
		self.isRunning = True
		
		
	def send_data(self):
		
		self.md1 = Indicator_dialog.Indicator_dialog(self, "...sending files...", "indicators"+os.sep+"ajax-loader-ball.gif")
		
		contents=["The scan is  done and the logged data is attached to this email. Please visit the experiment site and make sure that all light sources are switched off."]
		subject="The scan data from the latest scan!"
		
		if self.write2txt_check:
			contents.extend([self.textfile])
		if self.write2db_check:
			contents.extend([self.dbfile])
		if self.write2mat_check:
			contents.extend([self.matfile])
		if self.write2hdf5_check:
			contents.extend([self.hdf5file])
			
		obj = type("obj",(object,),{"subject":subject, "contents":contents, "settings":self.emailset_str, "receivers":self.emailrec_str})
		
		worker=Email_Worker(obj)
		worker.signals.critical.connect(self.critical)
		worker.signals.warning.connect(self.warning)
		worker.signals.finished.connect(self.finished1)
		
		# Execute
		self.threadpool.start(worker)
		self.isRunning = True
		
		
	def finished1(self):
		
		self.isRunning = False
		self.md1.close_()
		
		
	def clear_vars_graphs(self):
		# PLOT 2 initial canvas settings
		self.tal=-1
		self.time_counter=0
		
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
		self.wl_k2001a=[]
		self.wl_a34972a=[]
		self.wl_guv=[]
		self.volt_k2001a=[]
		self.volt_a34972a=[]
		self.volt_guv=[]
		self.pos_=[]
		self.shutter_=[]
		self.time_k2001a=[]
		self.time_a34972a=[]
		self.time_guv=[]
		self.dateandtime_k2001a=[]
		self.dateandtime_a34972a=[]
		self.dateandtime_guv=[]
		
		self.tableWidget.clearContents()
		
		if hasattr(self,"my_legend"):
			self.my_legend.scene().removeItem(self.my_legend)
			#self.my_legend.removeItem(self.my_legend)
		
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
		
		for i,j in zip(self.c_guv_end_Aon,self.c_guv_end_Aoff):
			i.clear()
			j.clear()
		for i,j in zip(self.c_guv_end_Bon,self.c_guv_end_Boff):
			i.clear()
			j.clear()
		for i,j in zip(self.c_guv_all_Aon,self.c_guv_all_Aoff):
			i.clear()
			j.clear()
		for i,j in zip(self.c_guv_all_Bon,self.c_guv_all_Boff):
			i.clear()
			j.clear()
		
		self.c_guv_end_Aon = []
		self.c_guv_end_Aoff = []
		self.c_guv_end_Bon = []
		self.c_guv_end_Boff = []
		
		self.c_guv_all_Aon = []
		self.c_guv_all_Aoff = []
		self.c_guv_all_Bon = []
		self.c_guv_all_Boff = []
		
		self.c_time_wl.clear()
		
		
	def load_(self):
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read("config.ini")
			self.last_used_scan = self.config.get("LastScan","last_used_scan")
			
			self.schroll_pts = int(self.config.get(self.last_used_scan,"schroll"))
			self.posset = self.config.get(self.last_used_scan,"pos").strip().split(',')[0]
			self.posnow = self.config.get(self.last_used_scan,"pos").strip().split(',')[1]
			self.posA_delay = int(self.config.get(self.last_used_scan,"posA_delay"))
			self.posB_delay = int(self.config.get(self.last_used_scan,"posB_delay"))
			self.posAB_delay = float(self.config.get(self.last_used_scan,"posAB_delay"))
			
			self.shutset = self.config.get(self.last_used_scan,"shutter").strip().split(',')[0]
			self.shutnow = self.config.get(self.last_used_scan,"shutter").strip().split(',')[1]
			
			self.sssd = self.config.get(self.last_used_scan,"sssd").strip().split(',')
			self.unit_str = self.config.get(self.last_used_scan,"unit")
			self.grating_str = self.config.get(self.last_used_scan,"grating")
			self.avgpts_a = int(self.config.get(self.last_used_scan,"avgpts_a"))
			self.avgpts_b = int(self.config.get(self.last_used_scan,"avgpts_b"))
			
			self.write2txt_str=self.config.get(self.last_used_scan,"write2txt").strip().split(',')[0]
			self.write2txt_check=self.bool_(self.config.get(self.last_used_scan,"write2txt").strip().split(',')[1])
			self.write2db_str=self.config.get(self.last_used_scan,"write2db").strip().split(',')[0]
			self.write2db_check=self.bool_(self.config.get(self.last_used_scan,"write2db").strip().split(',')[1])
			self.write2mat_str=self.config.get(self.last_used_scan,"write2mat").strip().split(',')[0]
			self.write2mat_check=self.bool_(self.config.get(self.last_used_scan,"write2mat").strip().split(',')[1])
			self.write2hdf5_str=self.config.get(self.last_used_scan,"write2hdf5").strip().split(',')[0]
			self.write2hdf5_check=self.bool_(self.config.get(self.last_used_scan,"write2hdf5").strip().split(',')[1])
			self.time_str = self.config.get(self.last_used_scan,"timetrace")
			
			self.emailrec_str = self.config.get(self.last_used_scan,"emailrec").strip().split(',')
			self.emailset_str = self.config.get(self.last_used_scan,"emailset").strip().split(',')
			
			self.ms257inport_str=self.config.get("Instruments","ms257inport").strip().split(',')[0]
			self.ms257inport_check=self.bool_(self.config.get("Instruments","ms257inport").strip().split(',')[1])
			self.ms257outport_str=self.config.get("Instruments","ms257outport").strip().split(',')[0]
			self.ms257outport_check=self.bool_(self.config.get("Instruments","ms257outport").strip().split(',')[1])
			self.k2001aport_str=self.config.get("Instruments","k2001aport").strip().split(',')[0]
			self.k2001aport_check=self.bool_(self.config.get("Instruments","k2001aport").strip().split(',')[1])
			self.a34972aport_str=self.config.get("Instruments","a34972aport").strip().split(',')[0]
			self.a34972aport_check=self.bool_(self.config.get("Instruments","a34972aport").strip().split(',')[1])
			self.guvport_str=self.config.get("Instruments","guvport").strip().split(',')[0]
			self.guvport_check=self.bool_(self.config.get("Instruments","guvport").strip().split(',')[1])
			self.orielport_str=self.config.get("Instruments","orielport").strip().split(',')[0]
			self.orielport_check=self.bool_(self.config.get("Instruments","orielport").strip().split(',')[1])
			self.guvtype_str=self.config.get("Instruments","guvtype")
			self.guv541 = self.config.get("Instruments","guv541").strip().split(',')
			self.guv2511 = self.config.get("Instruments","guv2511").strip().split(',')
			self.guv3511 = self.config.get("Instruments","guv3511").strip().split(',')
		except configparser.NoOptionError as nov:
			QMessageBox.critical(self, "Message",''.join(["Main FAULT while reading the config.ini file\n",str(nov)]))
			raise
		
	def bool_(self,txt):
		
		if txt=="True":
			return True
		elif txt=="False":
			return False
		
		
	def save_(self):
		self.time_str=time.strftime("%y%m%d-%H%M")
		self.lcd.display(self.time_str)
		
		self.config.read("config.ini")
		self.config.set("LastScan","last_used_scan", self.last_used_scan )
		self.config.set(self.last_used_scan,"schroll", str(self.schroll_pts) )
		self.config.set(self.last_used_scan,"pos", ','.join([self.posset, self.posnow]) )
		self.config.set(self.last_used_scan,"posA_delay", str(self.posA_delay) )
		self.config.set(self.last_used_scan,"posB_delay", str(self.posB_delay) )
		self.config.set(self.last_used_scan,"posAB_delay", str(self.posAB_delay) )
		self.config.set(self.last_used_scan,"shutter", ','.join([self.shutset, self.shutnow]) )
		self.config.set(self.last_used_scan,"avgpts_a", str(self.avgpts_a) )
		self.config.set(self.last_used_scan,"avgpts_b", str(self.avgpts_b) )
		self.config.set(self.last_used_scan,"sssd",','.join([str(self.startEdit.text()),str(self.stopEdit.text()),str(self.stepEdit.text()),str(self.dwelltimeEdit.text())]))
		self.config.set(self.last_used_scan,"unit",self.unit_str)
		self.config.set(self.last_used_scan,"grating",self.grating_str)
		self.config.set(self.last_used_scan,"timetrace",self.time_str)

		with open("config.ini", 'w') as configfile:
			self.config.write(configfile)
			
			
	def closeEvent(self, event):
		reply = QMessageBox.question(self, "Message", "Quit now? Changes will not be saved!", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			
			if self.inst_list.get("MS257_in"):
				if not hasattr(self, "worker"):
					if self.inst_list.get("MS257_in").is_open():
						self.inst_list.get("MS257_in").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, "Message", "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("MS257_in").is_open():
							self.inst_list.get("MS257_in").close()
							
			if self.inst_list.get("MS257_out"):
				if not hasattr(self, "worker"):
					if self.inst_list.get("MS257_out").is_open():
						self.inst_list.get("MS257_out").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, "Message", "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("MS257_out").is_open():
							self.inst_list.get("MS257_out").close()
							
			if self.inst_list.get("Oriel"):
				if not hasattr(self, "worker"):
					if self.inst_list.get("Oriel").is_open():
						self.inst_list.get("Oriel").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, "Message", "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("Oriel").is_open():
							self.inst_list.get("Oriel").close()
							
			if self.inst_list.get("K2001A"):
				if hasattr(self, "worker"):
					if self.inst_list.get("K2001A").is_open():
						self.inst_list.get("K2001A").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, "Message", "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("K2001A").is_open():
							self.inst_list.get("K2001A").close()
					
			if self.inst_list.get("Agilent34972A"):
				if hasattr(self, "worker"):
					if self.inst_list.get("Agilent34972A").is_open():
						self.inst_list.get("Agilent34972A").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, "Message", "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("Agilent34972A").is_open():
							self.inst_list.get("Agilent34972A").close()
					
			if self.inst_list.get("GUV"):
				if hasattr(self, "worker"):
					if self.inst_list.get("GUV").is_open():
						self.inst_list.get("GUV").close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, "Message", "Run in progress. Abort the run then quit!")
						event.ignore()
						return
					else:
						if self.inst_list.get("GUV").is_open():
							self.inst_list.get("GUV").close()
					
			if hasattr(self, "timer"):
				if self.timer.isActive():
					self.timer.stop()
			
			event.accept()
		else:
		  event.ignore()
		  
		  
	def save_plots(self):
		
		if self.write2txt_check:
			save_to_file=''.join([self.create_file(self.write2txt_str),".png"])
		elif self.write2db_check:
			save_to_file=''.join([self.create_file(self.write2db_str),".png"])
		elif self.write2mat_check:
			save_to_file=''.join([self.create_file(self.write2mat_str),".png"])
		elif self.write2hdf5_check:
			save_to_file=''.join([self.create_file(self.write2hdf5_str),".png"])	
		else:
			save_to_file=''.join([self.create_file("data_plot_"),".png"])	
			
		# create an exporter instance, as an argument give it
		# the item you wish to export
		
		exporter = pg.exporters.ImageExporter(self.p0)
		# Correction of the BUG in ImageExporter 
		# https://github.com/pyqtgraph/pyqtgraph/issues/538
		#I use the following contruct to circumvent the problem:
		exporter.params.param("width").setValue(1920, blockSignal=exporter.widthChanged)
		exporter.params.param("height").setValue(1080, blockSignal=exporter.heightChanged)
		#This way I don't have to modify internal code. Beware, if you set the values to the default values (640, 480) the variables will not update their type to int!

		# set export parameters if needed
		#exporter.parameters()['width'] = 100   # (note this also affects height parameter)
		# save to file
		if save_to_file:
			exporter.export(save_to_file)
		
		
#########################################
#########################################
#########################################
	
	
def main():
	
	app = QApplication(sys.argv)
	ex = Run_gui()
	#sys.exit(app.exec())

	# avoid message 'Segmentation fault (core dumped)' with app.deleteLater()
	app.exec()
	app.deleteLater()
	sys.exit()
	
	
if __name__ == '__main__':
		
	main()
	
	
