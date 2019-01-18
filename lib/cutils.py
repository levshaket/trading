#! /usr/bin/python3

# library: cutils

# e.g. import cutils as cu

# purpose: common utilities for python 3



# modules
import os, json



# library functions

def save(python_object, filename, directory):
	file_ = os.path.join(directory,filename)
	with open(file_,'w') as f:
		json.dump(python_object, f)

def load(filename, directory):
	file_ = os.path.join(directory, filename)
	with open(file_,'r') as f:
		python_object = json.load(f)
	return python_object
