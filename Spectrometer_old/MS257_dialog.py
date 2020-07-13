#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, sys, re, serial, time, numpy, visa
import pyqtgraph as pg

from PyQt5.QtCore import QObject, QThreadPool, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout,
														 QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
														 QVBoxLayout, QHBoxLayout, QPushButton)

import MS257


class WorkerSignals(QObject):
	# Create signals to be used
	update0 = pyqtSignal(object)
	finished = pyqtSignal()
	


class MS257_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''	
	def __init__(self,*argv):
		super(MS257_Worker, self).__init__()
		
		# constants	
		self.ms257 = argv[0].MS257
		self.set_ = argv[1].set_
		self.val = argv[2].val
		
		self.signals = WorkerSignals()
	
	@pyqtSlot()
	def run(self):
		if self.set_=='unit':
			self.ms257.setUNITS(self.val.upper())
			
		elif self.set_=='wl':
			self.ms257.goToWL(self.val)
			X_pos=self.ms257.getCurrentPOS()
			X_wl=self.ms257.getCurrentWL()
			self.signals.update0.emit([float(X_pos),float(X_wl)])
			
		elif self.set_=='pos':
			self.ms257.goToPOS(self.val)
			X_pos=self.ms257.getCurrentPOS()
			X_wl=self.ms257.getCurrentWL()
			self.signals.update0.emit([float(X_pos),float(X_wl)])
			
		elif self.set_=='shutter':
			self.ms257.setSHUTTER(self.val)
		
		self.signals.finished.emit()
				
				
				
				
				
				
				
class MS257_dialog(QDialog):
	
	def __init__(self, parent, config):
		super().__init__(parent)
		
		# constants
		self.config = config
		
		self.ms257inport_str=self.config.get('DEFAULT','ms257inport').strip().split(',')[0]
		self.ms257outport_str=self.config.get('DEFAULT','ms257outport').strip().split(',')[0]
		self.schroll_pts = int(self.config.get('DEFAULT','schroll'))
		self.unit_str = self.config.get('DEFAULT','unit')
		self.shutter_str = self.config.get('DEFAULT','shutter')
		
		self.setupUi()
		
		
	def setupUi(self):
		self.serialport = QLabel("Serial port (input)",self)
		
		self.combo1 = QComboBox(self)
		mylist1=[self.ms257inport_str ,self.ms257outport_str]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(self.ms257inport_str))
		self.combo1.setFixedWidth(100)
		self.combo1.setEditable(True)
		
		schroll_lbl = QLabel("Schroll elapsed time",self)
		schroll_lbl.setFixedWidth(150)
		self.combo0 = QComboBox(self)
		mylist0=["250 pts","500 pts","1000 pts","2000 pts","5000 pts"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(''.join([str(self.schroll_pts)," pts"])))
		self.combo0.setFixedWidth(100)
		
		setUnits_lbl = QLabel("Set unit",self)
		setUnits_lbl.setFixedWidth(150)
		self.combo2 = QComboBox(self)
		self.mylist2=["nm","um","wn"]
		self.combo2.addItems(self.mylist2)
		self.combo2.setCurrentIndex(self.mylist2.index(self.unit_str))
		self.combo2.setFixedWidth(100)
		
		setShutter_lbl = QLabel("Set shutter",self)
		setShutter_lbl.setFixedWidth(150)
		self.combo3 = QComboBox(self)
		self.mylist3=["on","off", "on and off"]
		self.combo3.addItems(self.mylist3)
		self.combo3.setCurrentIndex(self.mylist3.index(self.shutter_str))
		self.combo3.setFixedWidth(100)
		
		self.goWLButton = QPushButton("Go to wavelength",self)
		self.goWLButton.setFixedWidth(150)
		self.goWLButtonEdit = QLineEdit("",self)
		self.goWLButtonEdit.setFixedWidth(100)
		
		self.goPosButton = QPushButton("Go to position",self)
		self.goPosButton.setFixedWidth(150)
		self.goPosButtonEdit = QLineEdit("",self)
		self.goPosButtonEdit.setFixedWidth(100)
		
		self.clearButton = QPushButton("Clear",self)
		#self.clearButton.setFixedWidth(200)
		##############################################
		
		g0_1 = QGridLayout()
		g0_1.addWidget(self.serialport,0,0)
		g0_1.addWidget(self.combo1,0,1)
		g0_1.addWidget(schroll_lbl,1,0)
		g0_1.addWidget(self.combo0,1,1)
		g0_1.addWidget(setUnits_lbl,2,0)
		g0_1.addWidget(self.combo2,2,1)
		g0_1.addWidget(setShutter_lbl,3,0)
		g0_1.addWidget(self.combo3,3,1)
		g0_1.addWidget(self.goWLButton,4,0)
		g0_1.addWidget(self.goWLButtonEdit,4,1)
		g0_1.addWidget(self.goPosButton,5,0)
		g0_1.addWidget(self.goPosButtonEdit,5,1)
		g0_1.addWidget(self.clearButton,6,0,1,2)
		
		##############################################
		
		# set graph  and toolbar to a new vertical group vcan
		self.pw1 = pg.PlotWidget()
		
		##############################################
		
		# create table
		self.tableWidget = self.createTable()

		##############################################
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox = QHBoxLayout()
		hbox.addLayout(g0_1)
		hbox.addWidget(self.tableWidget)
		
		vbox = QVBoxLayout()
		vbox.addLayout(hbox)
		vbox.addWidget(self.pw1)
		
		self.threadpool = QThreadPool()
		print("Multithreading in MS257_dialog with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning=False
		
		self.setLayout(vbox)
		self.setWindowTitle("Test MS257 monochromator")
		
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
		self.p1.getAxis('left').setLabel("Wavelength", units=self.unit_str.lower(), color='yellow')
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Position", units="", color='red')
		self.p1.scene().addItem(self.p0_1)
		self.p1.getAxis('right').linkToView(self.p0_1)
		self.p0_1.setXLink(self.p1)
		
		self.p1.getAxis('bottom').setLabel("Point no.", units="", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw1.setDownsampling(mode='peak')
		self.pw1.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		self.combo3.activated[str].connect(self.onActivated3)
		
		# run or cancel the main script
		self.clearButton.clicked.connect(self.clear_vars_graphs)
		self.clearButton.setEnabled(False)
		
		self.goPosButton.clicked.connect(self.set_runPosWl)
		self.goWLButton.clicked.connect(self.set_runPosWl)
	
	def createTable(self):
		tableWidget = QTableWidget()
 
		# set row count
		#tableWidget.setRowCount(20)
		
		# set column count
		tableWidget.setColumnCount(3)
		
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
		
		tableWidget.setHorizontalHeaderLabels(["Point no.","Stepper position",''.join(["Wavelength[",self.unit_str.lower(),"]"])])
		#tableWidget.setVerticalHeaderLabels(["aa","bb","cc","dd"])
		
		# set horizontal header properties
		hh = tableWidget.horizontalHeader()
		hh.setStretchLastSection(True)
        
		# set column width to fit contents
		tableWidget.resizeColumnsToContents()
		
		# enable sorting
		#tableWidget.setSortingEnabled(True)
		
		return tableWidget
	
	
	def onActivated0(self, text):
		old_st=self.schroll_pts
		
		my_string=str(text)
		self.schroll_pts=int(my_string.split()[0])
		
		if old_st>self.schroll_pts:
			self.clear_vars_graphs()
			
			
	def onActivated1(self, text):
		self.ms257port_str=str(text)
		if self.ms257port_str=="COM3":
			self.serialport.setText("Serial port (input)")
		elif self.ms257port_str=="COM4":
			self.serialport.setText("Serial port (output)")
			
		print("Monochromator serial port changed to", str(text))
	
	
	def onActivated2(self, text):
		if not hasattr(self, 'MS257'):
			try:
				self.MS257 = MS257.MS257(self.ms257port_str)
			except Exception as e:
				QMessageBox.warning(self, 'Message',"No response from the MS257 serial port! Check the port name and the cable connection.")
				self.combo2.setCurrentIndex(self.mylist2.index(self.unit_str))
				return
			self.MS257.set_timeout(60)
		
		self.unit_str=str(text)
		self.p1.getAxis('left').setLabel(units=self.unit_str.lower())
		
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		self.combo3.setEnabled(False)
		
		self.goWLButton.setEnabled(False)
		self.goWLButtonEdit.setEnabled(False)
		self.goPosButton.setEnabled(False)
		self.goPosButtonEdit.setEnabled(False)
		self.isRunning=True
		
		obj=type('obj',(object,),{ 'ms257':self.MS257, 'set_':"unit", 'val':str(text) })
		
		self.worker=MS257_Worker(obj)	
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
		
		
	def onActivated3(self, text):
		if not hasattr(self, 'MS257'):
			try:
				self.MS257 = MS257.MS257(self.ms257port_str)
			except Exception as e:
				QMessageBox.warning(self, 'Message',"No response from the MS257 serial port! Check the port name and the cable connection.")
				self.combo3.setCurrentIndex(self.mylist3.index(self.shutter_str))
				return
			self.MS257.set_timeout(60)
		
		self.shutter_str=str(text)
		if self.shutter=="on and off":
			QMessageBox.warning(self, 'Message',"Set the shutter to position on or position off.")
			return
		
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		self.combo3.setEnabled(False)
		
		self.goWLButton.setEnabled(False)
		self.goWLButtonEdit.setEnabled(False)
		self.goPosButton.setEnabled(False)
		self.goPosButtonEdit.setEnabled(False)
		self.isRunning=True
		
		obj=type('obj',(object,),{ 'ms257':self.MS257, 'set_':"shutter", 'val':str(text) })
		
		self.worker=MS257_Worker(obj)	
		self.worker.signals.finished.connect(self.finished)
		
		# Execute
		self.threadpool.start(self.worker)
		
		
	def set_runPosWl(self):
		if not hasattr(self, 'MS257'):
			try:
				self.MS257 = MS257.MS257(self.ms257port_str)
			except Exception as e:
				QMessageBox.warning(self, 'Message',"No response from the MS257 serial port! Check the port name and the cable connection.")
				return
			self.MS257.set_timeout(60)
		
		sender=self.sender()
		
		if sender.text()=="Go to wavelength":
			set_ = "wl"
			val = str(self.goWLButtonEdit.text())
			
			if self.unit_str=='nm':
				if float(val)<200 or float(val)>2500:
					QMessageBox.warning(self, 'Message',"MS257 wavelength range is from 200 nm to 2500 nm")
					return
			if self.unit_str=='um':
				if float(val)<0.200 or float(val)>2.500:
					QMessageBox.warning(self, 'Message',"MS257 wavelength range is from 0.2 um to 2.5 um")
					return
				
		elif sender.text()=="Go to position":
			set_ = "pos"
			val = str(self.goPosButtonEdit.text())
			
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		self.combo3.setEnabled(False)
		
		self.goWLButton.setEnabled(False)
		self.goWLButtonEdit.setEnabled(False)
		self.goPosButton.setEnabled(False)
		self.goPosButtonEdit.setEnabled(False)
		self.isRunning=True
		
		obj=type('obj',(object,),{ 'ms257':self.MS257, 'set_':set_, 'val':val })
		
		self.worker=MS257_Worker(obj)	
		self.worker.signals.update0.connect(self.update0)
		self.worker.signals.finished.connect(self.finished)

		# Execute
		self.threadpool.start(self.worker)
		
		
	def update0(self,pos,wl):
		self.tal+=1
		
		# set row height
		self.tableWidget.setRowCount(self.tal+1)
		self.tableWidget.setRowHeight(self.tal, 12)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem(str(self.tal)))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem(str(pos)))
		self.tableWidget.setItem(self.tal, 2, QTableWidgetItem(str(wl)))
		
		if len(self.tals)>self.schroll_pts:
			self.tals[:-1] = self.tals[1:]  # shift data in the array one sample left
			self.tals[-1] = self.tal
			self.plot_pos_tr[:-1] = self.plot_pos_tr[1:]  # shift data in the array one sample left
			self.plot_pos_tr[-1] = pos
			#self.plot_time_tr[:-1] = self.plot_time_tr[1:]  # shift data in the array one sample left
			#self.plot_time_tr[-1] = timelist
			self.plot_wl_tr[:-1] = self.plot_wl_tr[1:]  # shift data in the array one sample left
			self.plot_wl_tr[-1] = wl
		else:
			self.tals.extend([ self.tal ])
			self.plot_pos_tr.extend([ pos ])
			self.plot_wl_tr.extend([ wl ])
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
		self.curve1.setData(self.tals, self.plot_pos_tr)
		self.curve2.setData(self.tals, self.plot_wl_tr)
		
		
	def finished(self):
		self.isRunning=False
		self.combo0.setEnabled(True)
		self.combo1.setEnabled(True)
		self.combo2.setEnabled(True)
		self.combo3.setEnabled(True)
		
		self.goWLButton.setEnabled(True)
		self.goWLButtonEdit.setEnabled(True)
		self.goPosButton.setEnabled(True)
		self.goPosButtonEdit.setEnabled(True)
		
		self.clearButton.setEnabled(True)
		self.clearButton.setText("Clear")
		
		
	def clear_vars_graphs(self):
		self.tal=-1
		self.tals=[]
		self.all_time_tr=[]
		self.plot_pos_tr=[]
		self.plot_wl_tr=[]
		#self.plot_time_tr=[]
		self.curve1.clear()
		self.curve2.clear()
		self.tableWidget.clearContents()
		
		self.clearButton.setEnabled(False)
		self.clearButton.setText("Cleared")
		
		
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message', "Quit now? Changes will not be saved!", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			if hasattr(self, 'MS257'):
				if not hasattr(self, 'worker'):
					if self.MS257.is_open():
						self.MS257.close()
				else:
					if self.isRunning:
						QMessageBox.warning(self, 'Message', "Run in progress. Cancel the scan then quit!")
						event.ignore()
						return None
					else:
						if self.MS257.is_open():
							self.MS257.close()
			event.accept()
		else:
		  event.ignore() 
		  
		  
		  
		  
		  
