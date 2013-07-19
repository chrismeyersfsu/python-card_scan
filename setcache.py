#!/usr/bin/python
import os
import sys
import pickle

def save_set_cache(path, cards):
	f = file(path,"wb")
	pickle.dump(cards, f)
	f.close()

def load_set_cache(path):
	try:
		f = file(path, "rb")
	# TODO: don't assume the ioerror means the file doesn't exist
	# check to see if the file exists
	except IOError:
		return None
	cards = pickle.load(f)
	f.close()
	return cards



