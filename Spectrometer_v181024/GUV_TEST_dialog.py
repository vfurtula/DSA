#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, sys, re, serial, time, numpy, itertools, configparser
import pyqtgraph as pg

from PyQt5.QtCore import QObject, QThreadPool, QRunnable, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout,
														 QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
														 QVBoxLayout, QHBoxLayout, QPushButton)

import GUV




class WorkerSignals(QObject):
	# Create signals to be used
	update0 = pyqtSignal(object,object)
	finished = pyqtSignal()
	
	


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
		self.guv = argv[0].guv
		
		self.signals = WorkerSignals()
	
	def abort(self):
		self.abort_flag=True
	
	@pyqtSlot()
	def run(self):
		time_start = time.time()
		while not self.abort_flag:
			X_val=[float(j) for j in [format(i,'.6e') for i in self.guv.return_powden()]]
			time_diff = format(time.time()-time_start,'.3e')
			T_val=[float(time_diff)]*len(X_val)
			#X_val=[float(i) for i in self.guv.return_voltage().strip().split(',')]
			self.signals.update0.emit(T_val, X_val)
			#time.sleep(0.05)
		
		self.signals.finished.emit()
				
			
			
		
		
class GUV_TEST_dialog(QDialog):

	def __init__(self, parent):
		super().__init__(parent)
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		
		try:
			self.config.read('config.ini')
		
			self.guvip=self.config.get('DEFAULT','guvport').strip().split(',')[0]
			self.guvport=self.config.get('DEFAULT','guvport').strip().split(',')[1]
			self.guvtype_str=self.config.get('DEFAULT','guvtype')
			self.schroll_pts = int(self.config.get('DEFAULT','schroll'))
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, 'Message',''.join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
		
		self.setupUi()
		
	def setupUi(self):
		
		ipport = QLabel("TCP/IP port",self)
		self.ipportEdit = QLineEdit(self.guvip,self)
		
		tcpport = QLabel("TCP port",self)
		self.tcpportEdit = QLineEdit(self.guvport,self)
		
		guvtype_lbl = QLabel("GUV type",self)
		self.guvtype_cb = QComboBox(self)
		mylist=["GUV-541","GUV-2511","GUV-3511"]
		self.guvtype_cb.addItems(mylist)
		self.guvtype_cb.setCurrentIndex(mylist.index(self.guvtype_str))
		
		self.runstopButton = QPushButton("START",self)
		self.clearButton = QPushButton("Clear",self)
		
		schroll_lbl = QLabel("Schroll elapsed time ",self)
		self.combo0 = QComboBox(self)
		mylist0=["250 pts","500 pts","1000 pts","2000 pts"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(''.join([str(self.schroll_pts)," pts"])))
		
		##############################################
		
		g0_1 = QGridLayout()
		g0_1.addWidget(ipport,0,0)
		g0_1.addWidget(self.ipportEdit,0,1)
		g0_1.addWidget(tcpport,0,2)
		g0_1.addWidget(self.tcpportEdit,0,3)
		g0_1.addWidget(guvtype_lbl,0,4)
		g0_1.addWidget(self.guvtype_cb,0,5)
		
		g0_2 = QGridLayout()
		g0_2.addWidget(schroll_lbl,0,0)
		g0_2.addWidget(self.combo0,0,1)
		g0_2.addWidget(self.runstopButton,0,2)
		g0_2.addWidget(self.clearButton,0,3)
		
		g0_3 = QVBoxLayout()
		g0_3.addLayout(g0_1)
		g0_3.addLayout(g0_2)
		
		##############################################
		
		# set graph  and toolbar to a new vertical group vcan
		self.pw1 = pg.PlotWidget()
		self.pw1.setFixedWidth(600)
		
		##############################################
		
		# create table
		self.tableWidget = self.createTable()

		##############################################
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		vbox = QVBoxLayout()
		vbox.addLayout(g0_3)
		vbox.addWidget(self.pw1)
		
		hbox = QVBoxLayout()
		hbox.addLayout(vbox)
		hbox.addWidget(self.tableWidget)
		
		self.threadpool = QThreadPool()
		print("Multithreading in the GUV dialog with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning=False
		
		self.setLayout(hbox)
		self.setWindowTitle("Test GUV")
		
		# PLOT 2 settings
		# create plot and add it to the figure canvas
		self.p1 = self.pw1.plotItem
		self.curves=[]
		colors = itertools.cycle(["r", "b", "g", "y", "m", "c", "w"])
		for i in range(20):
			mycol=next(colors)
			self.curves.append(self.p1.plot(pen=pg.mkPen(color=mycol), symbol='s', symbolPen=mycol, symbolBrush=mycol, symbolSize=4))
		# create plot and add it to the figure
		self.p0_1 = pg.ViewBox()
		self.curve2 = pg.PlotCurveItem(pen='r')
		self.p0_1.addItem(self.curve2)
		# connect respective axes to the plot 
		#self.p1.showAxis('left')
		self.p1.getAxis('left').setLabel("Power density", units="", color='yellow')
		self.p1.showAxis('right')
		self.p1.getAxis('right').setLabel("Arb unit", units="", color='red')
		self.p1.scene().addItem(self.p0_1)
		self.p1.getAxis('right').linkToView(self.p0_1)
		self.p0_1.setXLink(self.p1)
		
		self.p1.getAxis('bottom').setLabel("Time passed", units="s", color='yellow')
		# Use automatic downsampling and clipping to reduce the drawing load
		self.pw1.setDownsampling(mode='peak')
		self.pw1.setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		self.combo0.activated[str].connect(self.onActivated0)
		self.guvtype_cb.activated[str].connect(self.onActivated1)
		
		# run or cancel the main script
		self.runstopButton.clicked.connect(self.runstop)
		self.clearButton.clicked.connect(self.set_clear)
		self.clearButton.setEnabled(False)
		
		
	def onActivated0(self, text):
		
		my_string=str(text)
		self.schroll_pts=int(my_string.split()[0])
	
	def onActivated1(self, text):
		
		self.guvtype_str=str(text)
			
	def createTable(self):
		
		tableWidget = QTableWidget()
		#tableWidget.setFixedWidth(175)
		
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
		
		tableWidget.setHorizontalHeaderLabels(["Time[s]","Channel power density"])
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
			self.GUV = GUV.GUV([str(self.ipportEdit.text()),str(self.tcpportEdit.text()),self.guvtype_str],False)
		except Exception as e:
			reply = QMessageBox.critical(self, ''.join([self.guvtype_str,' TEST MODE']), ''.join([self.guvtype_str," could not return valid echo signal. Check the port name and check the connection.\n",str(e),"\n\nShould the program proceeds into the TEST MODE?"]), QMessageBox.Yes | QMessageBox.No)
			if reply == QMessageBox.Yes:
				self.GUV = GUV.GUV([str(self.ipportEdit.text()),str(self.tcpportEdit.text()),self.guvtype_str],True)
			else:
				return
		
		self.set_clear()
		self.runstopButton.setEnabled(True)
		self.runstopButton.setText("STOP")
		
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.ipportEdit.setEnabled(False)
		self.tcpportEdit.setEnabled(False)
		self.guvtype_cb.setEnabled(False)
		self.isRunning=True
		
		setrun_obj=type('setscan_obj',(object,),{ 'guv':self.GUV })
		
		self.worker=GUV_Worker(setrun_obj)	
		self.worker.signals.update0.connect(self.update0)
		self.worker.signals.finished.connect(self.finished)

		# Execute
		self.threadpool.start(self.worker)
		
	def update0(self,times,volts):
		
		self.tal+=1
		
		# set row height
		self.tableWidget.setRowCount(self.tal+1)
		self.tableWidget.setRowHeight(self.tal, 12)
		
		# add row elements
		self.tableWidget.setItem(self.tal, 0, QTableWidgetItem(format(times[0],'.2e')))
		self.tableWidget.setItem(self.tal, 1, QTableWidgetItem(', '.join([format(float(i), '.2e') for i in volts]) ))
		
		all_elements = sum(len(i) for i in self.times)
		if all_elements > self.schroll_pts:
			self.times[:-1] = self.times[1:]  # shift data in the array one sample left
			self.times[-1] = times
			self.plot_volts_tr[:-1] = self.plot_volts_tr[1:]  # shift data in the array one sample left
			self.plot_volts_tr[-1] = volts
		else:
			self.times.append( times )
			self.plot_volts_tr.append( volts )
			
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
		
		times_ = list(map(list, zip(*self.times)))
		plot_volts_tr_ = list(map(list, zip(*self.plot_volts_tr)))
		
		for i in range(len(times_)):
			self.curves[i].setData(times_[i], plot_volts_tr_[i])
			#self.curve2.setData(self.times, self.plot_volts_tr)
			
			
	def finished(self):
		
		self.isRunning=False
		self.ipportEdit.setEnabled(True)
		self.tcpportEdit.setEnabled(True)
		self.guvtype_cb.setEnabled(True)
		self.combo0.setEnabled(True)
		self.clearButton.setEnabled(True)
		self.clearButton.setText("Clear")
	
	def clear_vars_graphs(self):
		
		# PLOT 2 initial canvas settings
		self.tal=-1
		self.times=[]
		self.plot_volts_tr=[]
		for i in range(20):
			self.curves[i].clear()
		self.curve2.clear()
		self.tableWidget.clearContents()
	
	def closeEvent(self, event):
		
		reply = QMessageBox.question(self, 'Message', "Quit now? Changes will not be saved!", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			
			if hasattr(self, 'GUV'):
				if self.isRunning:
					QMessageBox.warning(self, 'Message', "Run in progress. Cancel the scan then quit!")
					event.ignore()
					return
				
			event.accept()
		else:
		  event.ignore() 
