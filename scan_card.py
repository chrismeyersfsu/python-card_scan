import math
import cv
import os
import numpy
import cv2
from detect_card import detect_card
from cv_utils import float_version, show_scaled, sum_squared, ccoeff_normed, clone_image, overlay_text_on_image, create_dummy_image, flip_image, to_gray_image

def get_card(color_capture, corners):
	target = [(0,0), (223,0), (223,310), (0,310)]
	mat = cv.CreateMat(3,3, cv.CV_32FC1)
	cv.GetPerspectiveTransform(corners, target, mat)
	warped = cv.CloneImage(color_capture)
	cv.WarpPerspective(color_capture, warped, mat)
	cv.SetImageROI(warped, (0,0,223,310) )
	return warped


def setup_windows():
	cv.NamedWindow('background')
	cv.NamedWindow('snapshot')
	cv.NamedWindow('main')
	cv.NamedWindow('match')

	cv.MoveWindow('snapshot', 750, 550)
	cv.MoveWindow('match', 1200, 550)
	cv.MoveWindow('background', 50, 500)
	cv.WaitKey(10)
	#cv.StartWindowThread()


def save_captures(num, captures):
	dir = "data/capture_%02d" % num
	if not os.path.exists(dir):
		os.mkdir(dir)
	for i, img in enumerate(captures):
		path = os.path.join(dir, "card_%04d.png" % i)
		if os.path.exists(path):
			raise Exception("path %s already exists!" % path)
		cv.SaveImage(path, img)

def cv2array(im): 
  depth2dtype = { 
		cv.IPL_DEPTH_8U: 'uint8', 
		cv.IPL_DEPTH_8S: 'int8', 
		cv.IPL_DEPTH_16U: 'uint16', 
		cv.IPL_DEPTH_16S: 'int16', 
		cv.IPL_DEPTH_32S: 'int32', 
		cv.IPL_DEPTH_32F: 'float32', 
		cv.IPL_DEPTH_64F: 'float64', 
	} 

  arrdtype=im.depth 
  a = numpy.fromstring( 
		 im.tostring(), 
		 dtype=depth2dtype[im.depth], 
		 count=im.width*im.height*im.nChannels) 
  a.shape = (im.height,im.width,im.nChannels) 
  return a 

class ScanCard:
	def __init__(self, camera):
		self.recent_frames_max = 3
		self.camera = camera
		self.last_frame = None
		self.last_frame_flipped = None
		self.last_frame_gray = None
		self.recent_frames = []
		self.recent_frames_gray = []
		self.snapshot = None
		self.background = None
		self.background_flipped = None
		self.last_frame = None
		self.size = None
		self.num_pixels = None
		self.snapshot = None
		self.has_moved = None
		self.font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, .5, .5)

	def update_snapshot_window(img):
		tmp = cv.CloneImage(img)
		cv.PutText(tmp, "%s" % (snapshot), (1,24), self.font, (255,255,255))
		cv.ShowImage("snapshot", tmp)

	def grab_frame(self):
		frame = cv.QueryFrame(self.camera)
		frame_gray = to_gray_image(frame)
		frame_flipped = flip_image(frame)

		# Set the size of things if this is the first image we have seen
		if self.last_frame is None:
			self.size = cv.GetSize(frame)
			self.num_pixels = self.size[0]*self.size[1]
	
		self.recent_frames_gray.append(frame_gray)
		self.recent_frames.append(frame)
		if len(self.recent_frames) > self.recent_frames_max:
			del self.recent_frames[0]
			del self.recent_frames_gray[0]

		self.last_frame = clone_image(frame)
		self.last_frame_flipped = frame_flipped
		self.last_frame_gray = frame_gray
		return frame 


	def display_background(self, text=None):
		if text is not None:
			overlay_text_on_image(self.background_flipped, text, self.font)
		cv.ShowImage('background', self.background_flipped)

	def display_live(self, text=None):
		if text is not None:
			overlay_text_on_image(self.last_frame_flipped, text, self.font)
		cv.ShowImage('main', self.last_frame_flipped)

	def display_snapshot(self):
		if self.snapshot is not None:
			cv.ShowImage('snapshot', self.snapshot)

	def update_background(self, frame=None):
		if frame is None:
			frame = self.last_frame
			if frame is None:
				frame = self.grab_frame()
		self.background = clone_image(frame)
		
		self.background_gray = to_gray_image(self.background)
		self.background_flipped = flip_image(self.background)

	def calc_biggest_diff(self):
		return max(sum_squared(self.last_frame_gray, frame) / self.num_pixels for frame in self.recent_frames_gray)

	def calc_background_similarity(self):
		return min(ccoeff_normed(self.background_gray, frame) for frame in self.recent_frames_gray)

	def check_for_card(self):
		found = False
		base_corr = 0

		self.grab_frame()
		# if the user didn't set the background, get the first frame and consider it the background
		if self.background is None:
			print "Updating background on the account of it being NOne"
			self.update_background()
		
		history_diff = self.calc_biggest_diff()

		# Detect movement
		if history_diff > 10:
			self.has_moved = True

		# No movement now, but there was before
		elif self.has_moved == True:
			base_corr = self.calc_background_similarity()
			# Looking at the background, false alarm
			# set the frame as the new background, this helps with lightning change
			if base_corr >= 0.75:
				#self.update_background()
				self.has_moved = False
			else:
				# background and current frame are < 25% similar
				corners = detect_card(self.last_frame_gray, self.background_gray)
				if corners is not None:
					self.snapshot = get_card(self.last_frame_gray, corners)
					self.snapshot = flip_image(self.snapshot)
					found = True
					self.has_moved = False
				else:
					self.has_moved = False
		
		self.display_background()
		self.display_live("%.4f [0-10 stable, >10 unstable] | %.4f [>0.75 is background, <0.75 contains foreground]" % (history_diff, base_corr))

		if found is True:
			return clone_image(self.snapshot)
		return None

