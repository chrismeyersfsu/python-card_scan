#!/usr/bin/python
from subprocess import Popen, PIPE, STDOUT
import os
import sys

class TTS:
	def __init__(self):
		cmd = "festival --tts"
		self.festival = Popen(['festival', '--pipe'], bufsize=0, stdin=PIPE)
		self.say("Loaded Text to Speech")

	def say(self, text):
		cmd = "(SayText \"%s\")" % (text)
		self.festival.stdin.write(cmd)
		self.festival.stdin.flush()


