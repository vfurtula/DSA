#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, sys, re, serial, time, numpy, visa, configparser
import pyqtgraph as pg

from PyQt5.QtCore import QObject, QThreadPool, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout,
														 QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
														 QVBoxLayout, QHBoxLayout, QPushButton)

import K2001A




class WorkerSignals(QObject):
	# Create signals to be used
	update0 = pyqtSignal(object)
	finished = pyqtSignal()
	
	
	
	
	
	
	
	
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
		self.k2001a = argv[0].k2001a
		
		self.signals = WorkerSignals()
	
	def abort(self):
		self.abort_flag=True
	
	@pyqtSlot()
	def run(self):
		self.k2001a.set_dc_voltage()
		while not self.abort_flag:
			X_val=self.k2001a.return_voltage()
			self.signals.update0.emit(float(X_val))
			#time.sleep(0.05)
			
		self.signals.finished.emit()
			
			
			
			
			
			
class K2001A_TEST_dialog(QDialog):

	def __init__(self, parent):
		super().__init__(parent)
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
		
			self.schroll_pts = int(self.config.get('DEFAULT','schroll'))
			self.k2001aport = self.config.get('DEFAULT','k2001aport').strip().split(',')[0]
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
		
		self.setupUi()

	def setupUi(self):
		
		serialport = QLabel("GPIB port",self)
		self.serialportEdit = QLineEdit(self.k2001aport,self)
		
		self.runstopButton = QPushButton("START",self)
		self.clearButton = QPushButton("Clear",self)
		
		schroll_lbl = QLabel("Schroll elapsed time ",self)
		self.combo0 = QComboBox(self)
		mylist0=["250 pts","500 pts","1000 pts","2000 pts","5000 pts"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(''.join([str(self.schroll_pts)," pts"])))
		
		##############################################
		
		g0_1 = QGridLayout()
		g0_1.addWidget(serialport,0,0)
		g0_1.addWidget(self.serialportEdit,0,1)
		g0_1.addWidget(schroll_lbl,0,2)
		g0_1.addWidget(self.combo0,0,3)
		g0_1.addWidget(self.runstopButton,0,4)
		g0_1.addWidget(self.clearButton,0,5)
		
		##############################################
		
		# set graph  and toolbar to a new vertical group vcan
		self.pw1 = pg.PlotWidget()
		
		##############################################
		
		# create table
		self.tableWidget = self.createTable()

		##############################################
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		vbox = QVBoxLayout()
		vbox.addLayout(g0_1)
		vbox.addWidget(self.pw1)
		
		hbox = QHBoxLayout()
		hbox.addLayout(vbox)
		hbox.addWidget(self.tableWidget)
		
		self.threadpool = QThreadPool()
		print("Multithreading in the K2001A with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning=False
		
		self.setLayout(hbox)
		self.setWindowTitle("Test Keithley 2001A")
		
		# PLOT 2 settings
		# create plot and add it to the figure canvas
		self.p1 = self.pw1.plotItem
		self.curve1=self.p1.plot(pen='w')
		# create plot and add it to the figure
		self.p0_1 = pg.ViewBox()
		self.curve2=pg.PlotCurveItem(pen='r')
		self.p0_1.addItem(self.curve2)
		# connect respective axes to the plot 
		#self.p1.showAxis('left')
		self.p1.getAxis('left').setLabel("Voltage", units="V", color='yellow')
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Arb unit, 1023=1.1V", units="", color='red')
		self.p1.scene().addItem(self.p0_1)
		self.p1.getAxis('right').linkToView(self.p0_1)
		self.p0_1.setXLink(self.p1)
		
		self.p1.getAxis('bottom').setLabel("Points", units="", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw1.setDownsampling(mode='peak')
		self.pw1.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		self.combo0.activated[str].connect(self.onActivated0)
		
		# run or cancel the main script
		self.runstopButton.clicked.connect(self.runstop)
		self.clearButton.clicked.connect(self.set_clear)
		self.clearButton.setEnabled(False)
		
	def onActivated0(self, text):
		
		old_st=self.schroll_pts
		
		my_string=str(text)
		self.schroll_pts=int(my_string.split()[0])
		
		if old_st>self.schroll_pts:
			self.set_clear()
	
	def createTable(self):
		
		tableWidget = QTableWidget()
 
		# set row count
		#tableWidget.setRowCount(20)
		
		# set column count
		tableWidget.setColumnCount(2)
		
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
		
		tableWidget.setHorizontalHeaderLabels(["Point no.","U[V]"])
		#tableWidget.setVerticalHeaderLabels(["aa","bb","cc","dd"])
		
		# set horizontal header properties
		hh = tableWidget.horizontalHeader()
		hh.setStretchLastSection(True)
        
		# set column width to fit contents
		tableWidget.resizeColumnsToContents()
		
		# enable sorting
		#tableWidget.setSortingEnabled(True)
		
		return tableWidget
	
	def set_cancel(self):

		self.worker.abort()
		
		self.clearButton.setEnabled(True)
		self.runstopButton.setText("START")
	
	def set_clear(self):
		
		self.clear_vars_graphs()
		self.clearButton.setEnabled(False)
		self.clearButton.setText("Cleared")
		
	def runstop(self):
		
		sender=self.sender()
		
		if sender.text()=="START":
			self.set_run()
		elif sender.text()=="STOP":
			self.set_cancel()
	
	def set_run(self):

		try:
			self.K2001A = K2001A.K2001A(str(self.serialportEdit.text()), False)
			rm = visa.ResourceManager()
			print(rm.list_resources())
		except Exception as e:
			reply = QMessageBox.critical(self, 'Keithley 2001A TEST MODE', ''.join(["K2001A could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
			if reply == QMessageBox.Yes:
				self.K2001A = K2001A.K2001A(str(self.serialportEdit.text()), True)
			else:
				return
		
		self.runstopButton.setEnabled(True)
		self.runstopButton.setText("STOP")
		
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.serialportEdit.setEnabled(False)
		self.isRunning=True
		
		setrun_obj=type('setscan_obj',(object,),{ 'k2001a':self.K2001A })
		
		self.worker=K2001A_Worker(setrun_obj)	
		self.worker.signals.update0.connect(self.update0)
		self.worker.signals.finished.connect(self.finished)

		# Execute
		self.threadpool.start(self.worker)
		
		
	def update0(self,volts):
		
		self.tal+=1
		
		# set row height
		self.tableWidget.setRowCount(self.tal+1)
		self.tableWidget.setRowHeight(self.tal, 12)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem(str(self.tal)))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem(str(volts)))
		
		if len(self.tals)>self.schroll_pts:
			self.tals[:-1] = self.tals[1:]  # shift data in the array one sample left
			self.tals[-1] = self.tal
			self.plot_as_tr[:-1] = self.plot_as_tr[1:]  # shift data in the array one sample left
			self.plot_as_tr[-1] = volts
			#self.plot_time_tr[:-1] = self.plot_time_tr[1:]  # shift data in the array one sample left
			#self.plot_time_tr[-1] = timelist
			self.plot_volts_tr[:-1] = self.plot_volts_tr[1:]  # shift data in the array one sample left
			self.plot_volts_tr[-1] = volts
		else:
			self.tals.extend([ self.tal ])
			self.plot_as_tr.extend([ volts ])
			self.plot_volts_tr.extend([ volts ])
			#self.plot_time_tr.extend([ timelist ])
		
		## Handle view resizing 
		def updateViews():
			## view has resized; update auxiliary views to match
			self.p0_1.setGeometry(self.p1.vb.sceneBoundingRect())
			#p3.setGeometry(p1.vb.sceneBoundingRect())

			## need to re-update linked axes since this was called
			## incorrectly while views had different shapes.
			## (probably this should be handled in ViewBox.resizeEvent)
			self.p0_1.linkedViewChanged(self.p1.vb, self.p0_1.XAxis)
			#p3.linkedViewChanged(p1.vb, p3.XAxis)
			
		updateViews()
		self.p1.vb.sigResized.connect(updateViews)

		self.curve1.setData(self.tals, self.plot_as_tr)
		self.curve2.setData(self.tals, self.plot_volts_tr)
	
	def finished(self):
		self.isRunning=False
		self.serialportEdit.setEnabled(True)
		self.combo0.setEnabled(True)
		self.clearButton.setEnabled(True)
		self.clearButton.setText("Clear")
	
	def clear_vars_graphs(self):
		# PLOT 2 initial canvas settings
		self.tal=-1
		self.tals=[]
		self.all_time_tr=[]
		self.plot_as_tr=[]
		self.plot_volts_tr=[]
		#self.plot_time_tr=[]
		self.curve1.clear()
		self.curve2.clear()
		self.tableWidget.clearContents()
	
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message', "Quit now? Changes will not be saved!", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			if hasattr(self, 'K2001A'):
				if self.isRunning:
					QMessageBox.warning(self, 'Message', "Run in progress. Cancel the scan then quit!")
					event.ignore()
					return
				
			event.accept()
		else:
		  event.ignore() 
