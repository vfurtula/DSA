#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import os, re, imp, serial, time, yagmail, zipfile

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot

from PyQt5.QtWidgets import (QDialog, QMessageBox, QGridLayout, QLabel, QLineEdit, QComboBox, QVBoxLayout, QPushButton, QFileDialog)


import Message_dialog


class WorkerSignals(QObject):
	
	# Create signals to be used
	about = pyqtSignal(object)
	critical = pyqtSignal(object)
	finished = pyqtSignal()
	
	


class Zip_Worker(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''
	def __init__(self,*argv):
		super(Zip_Worker, self).__init__()
		
		# constants	
		self.folder = argv[0].folder
		
		self.signals = WorkerSignals()
		
		
	@pyqtSlot()
	def run(self):
		
		self.zip_folder()
		
		
	def zipdir(self, path, ziph):
		# ziph is zipfile handle
		for root, dirs, files in os.walk(path):
			for thefile in files:
				ziph.write(os.path.join(root, thefile))
			
	def zip_folder(self):
		
		try:
			zipf = zipfile.ZipFile(''.join([self.folder,'.zip']), 'w', zipfile.ZIP_DEFLATED)
			self.zipdir(self.folder, zipf)
			zipf.close()
			self.signals.about.emit(''.join(['Zipped directory at the location:\n\n',self.folder,'.zip']))
		except Exception as e:
			self.signals.critical.emit(str(e))
		
		self.signals.finished.emit()
		




class Send_email_dialog(QDialog):

	def __init__(self, parent, config):
		super().__init__(parent)
		
		# constants
		self.config = config
		
		self.emailset_str = self.config.get('DEFAULT','emailset').strip().split(',')
		self.emailrec_str = self.config.get('DEFAULT','emailrec').strip().split(',')
		
		self.all_files=["The attached files are some chosen data sent from the microstepper computer."]

		self.setupUi()

	def setupUi(self):
		
		self.lb0 = QLabel("Receiver(s) comma(,) separated:",self)
		self.le1 = QLineEdit()
		self.le1.setText(', '.join([i for i in self.emailrec_str]))
		self.le1.textChanged.connect(self.on_text_changed)
		
		self.btnSave = QPushButton("Receivers saved",self)
		self.btnSave.clicked.connect(self.btn_save)
		self.btnSave.setEnabled(False)
		
		self.btnSend = QPushButton("Send e-mail",self)
		self.btnSend.clicked.connect(self.btn_send_email)
		self.btnSend.setEnabled(False)
		
		self.btnBrowse = QPushButton("Pick files",self)
		self.btnBrowse.clicked.connect(self.btn_browse_files)
		
		self.btnZip = QPushButton("Zip folder",self)
		self.btnZip.clicked.connect(self.zip_folder)
		
		self.btnClear = QPushButton("Clear list",self)
		self.btnClear.clicked.connect(self.btn_clear_list)
		self.btnClear.setEnabled(False)
		
		self.threadpool = QThreadPool()
		
		# set layout
		grid_0 = QGridLayout()
		grid_0.addWidget(self.lb0,0,0)
		grid_0.addWidget(self.le1,1,0)
		grid_0.addWidget(self.btnSave,2,0)
		
		grid_1 = QGridLayout()
		grid_1.addWidget(self.btnSend,0,0)
		grid_1.addWidget(self.btnBrowse,0,1)
		grid_1.addWidget(self.btnZip,0,2)
		grid_1.addWidget(self.btnClear,0,3)
		
		grid_2 = QGridLayout()
		self.lb1 = QLabel("No files selected!",self)
		grid_2.addWidget(self.lb1,0,0)
		
		v0 = QVBoxLayout()
		v0.addLayout(grid_0)
		v0.addLayout(grid_1)
		v0.addLayout(grid_2)
		
		self.setLayout(v0)
		self.setWindowTitle("E-mail data")
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		v0.setSizeConstraint(v0.SetFixedSize)
		
	def btn_send_email(self):
		
		try:
			self.yag = yagmail.SMTP(self.emailset_str[0])
			self.yag.send(self.emailrec_str, "File(s) sent from the datalog computer", contents=self.all_files)
			QMessageBox.warning(self, 'Message', ''.join(["E-mail is sent to ", ' and '.join([i for i in self.emailrec_str]) ," including ",str(len(self.all_files[1:]))," attachment(s)!"]))
		except Exception as e:
			QMessageBox.warning(self, 'Message',''.join(["Could not load the gmail account ",self.emailset_str[0],"! Try following steps:\n1. Check internet connection. Only wired internet will work, ie. no wireless.\n2. Check the account username and password.\n3. Make sure that the account accepts less secure apps."]))
			
			
	def btn_clear_list(self):
	
		self.all_files=["The attached files are some chosen data sent from the datalog computer."]
		self.lb1.setText("No files selected!")

		self.btnSend.setEnabled(False)
		self.btnClear.setEnabled(False)
		
		
	def btn_browse_files(self):
		
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		files, _ = QFileDialog.getOpenFileNames(self,"Open files","", "All Files (*);;Python Files (*.py);;Text Files (*.txt)", options=options)
		if files:
			self.all_files.extend(files)
		
		for emails in self.emailrec_str:
			if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", emails):
				self.btnSend.setEnabled(False)
			else:
				if len(self.all_files)==1:
					self.btnSend.setEnabled(False)
				else:
					self.btnSend.setEnabled(True)
					
		if len(self.all_files)==1:
			self.lb1.setText("No files selected!")
			self.btnClear.setEnabled(False)
		else:
			self.print_files = "Selected files:\n"
			self.tal = 0
			for paths in self.all_files[1:]:
				head, tail = os.path.split(paths)
				self.tal +=1
				self.print_files += ''.join([str(self.tal),': ',tail, "\n"])
				
			self.lb1.setText(self.print_files)
			self.btnClear.setEnabled(True)
			
	def finished(self):
		
		self.md.close_()
	
	def about(self,mystr):
		
		QMessageBox.about(self, 'Message',mystr)
		
	def critical(self,mystr):
		
		QMessageBox.critical(self, 'Message',mystr)
		
	def zip_folder(self):
		
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		folder = QFileDialog.getExistingDirectory(self, 'Select directory to zip', options=options)
		if folder:
			self.md = Message_dialog.Message_dialog(self, "Zipping folder", "...please wait...")
			
			obj = type('obj',(object,),{'folder':folder})
			
			worker=Zip_Worker(obj)
			worker.signals.critical.connect(self.critical)
			worker.signals.about.connect(self.about)
			worker.signals.finished.connect(self.finished)
			
			# Execute
			self.threadpool.start(worker)
			
			
	def on_text_changed(self):
		
		self.emailrec_str = str(self.le1.text()).split(',')
		self.emailrec_str = [emails.strip() for emails in self.emailrec_str]
		
		for emails in self.emailrec_str:
			if not re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", emails):
				self.btnSend.setEnabled(False)
				self.btnSave.setText("*Invalid e-mail(s)*")
				self.btnSave.setEnabled(False)
			else:
				if len(self.all_files)==1:
					self.btnSend.setEnabled(False)
				else:
					self.btnSend.setEnabled(True)
				self.btnSave.setText("*Save receivers*")
				self.btnSave.setEnabled(True)
				
				
	def btn_save(self):
		
		self.btnSave.setText("Receivers saved")
		self.btnSave.setEnabled(False)
		
		self.config.set('DEFAULT', 'emailrec', ','.join([i for i in self.emailrec_str]))
		
		with open('config.ini', 'w') as configfile:
			self.config.write(configfile)
			
			
	def closeEvent(self,event):
	
		event.accept()
