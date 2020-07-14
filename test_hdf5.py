#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 10:35:01 2019

@author: Vedran Furtula
"""


import h5py, random
import numpy

run_test = 0

if run_test==0:
	
	dt_ = h5py.vlen_dtype(numpy.dtype('float32'))
	
	with h5py.File('resize_dataset.hdf5', 'w') as f:
		d1 = f.create_dataset('dataset1', (0, ),  maxshape=(None, ), dtype=dt_)
		d2 = f.create_dataset('dataset2', (0, ),  maxshape=(None, ))
		#d1[:10] = np.random.randn(10)
		#d2[:5] = np.random.randn(5)
		#d.resize((200,))
		#d[100:200] = np.random.randn(100)

	with h5py.File('resize_dataset.hdf5', 'r') as f:
		dset = f['dataset1']
		print("dset: ", dset[:])

	for tal in range(10):
		with h5py.File('resize_dataset.hdf5', 'a') as f:
			dset = f["dataset1"]
			print("dset: ",dset.size)
			
			X_train_data = numpy.array([random.random() for i in range(tal+1)])
			#dset.resize((dset.shape[0] + X_train_data.shape[0]), axis = 0)
			#dset[-X_train_data.shape[0]:] = X_train_data
    
			dset.resize((dset.size+1,))
			dset[-1] = X_train_data
			
	for tal in range(20):
		with h5py.File('resize_dataset.hdf5', 'a') as f:
			dset = f['dataset2']
			print("dset: ",dset.size)
			dset.resize((dset.size+1,))
			dset[-1] = tal

	with h5py.File('resize_dataset.hdf5', 'r') as f:
		
		print("Header: ", f.keys())
		
		dset1 = f['dataset1']
		print(dset1)
		print(dset1[:])
		
		dset2 = f['dataset2']
		print(dset2)
		print(dset2[:])
		
elif run_test==1:
	
	with h5py.File("data/hdf5/data_200419-1939.hdf5", 'r') as f:
		
		print("Header: ", f.keys())
		
		dset1 = f['detector']
		print("detector: ", dset1[1:10])
		
		dset1 = f["ms257_in"]
		print("ms257_in: ",dset1[1:10])
		
		dset1 = f["ms257_out"]
		print("ms257_out: ",dset1[1:10])
		
		dset1 = f["k2001a_signal"]
		print("k2001a_signal: ",dset1[1:10])
		
		dset1 = f["guv_signal"]
		print("guv_signal: ",dset1[1:10])
		
		
