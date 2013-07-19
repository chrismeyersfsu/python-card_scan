import os
from cv_utils import ccoeff_normed, img_from_buffer, float_version, clone_image, overlay_text_on_image
import cv
import math
import sys

# basedir is where the set images are
class MatchCard:
	def __init__(self, basedir):
		self.basedir = basedir
		self.img = None
		self.card_name = None
		self.set_name = None

	def set(self, set_name, card_name):
		self.card_name = card_name
		self.set_name = set_name
		self.font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, .5, .5)
		
		path = os.path.join(self.basedir, set_name, card_name+".full.jpg")
		try:
			self.img = cv.LoadImage(path)
		except IOError:
			return False
		return True

	def get_set_name(self):
		return self.set_name
	def get_card_name(self):
		return self.card_name

	def display(self):
		tmp = clone_image(self.img)
		overlay_text_on_image(tmp, "%s - %s" % (self.card_name, self.set_name), self.font)
		cv.ShowImage("match", tmp)
		cv.ResizeWindow("match", 800, 600)


PREV, NEXT, KEY, RESULT = 0, 1, 2, 3
MAXSIZE = 7000
class GradientCache:
	def __init__(self, base_dir):
		self.base_dir = base_dir
		self.cache = {}
		self.root = []
		self.root[:] = [self.root, self.root, None, None]
		self.full = False
		self.currsize = 0

	'''
	Returns card gotten from filesytem, based on set_name+name, and converted 
	to a format that can easily be analyized (i.e. looks like just the outlines)
	Further, the image is placed in a cache with the key being the concatenation
	of set_name+'/'+name

	return None if card not found
	return card if found (image)
	'''
	def getCard(self, set_name, name):
		key = "%s/%s" % (set_name, name)
		if key in self.cache:
			#bump entry to front of list, then return
			link = self.cache[key]
			#remove it from where it is
			link_prev, link_next, key, result = link
			link_prev[NEXT] = link_next
			link_next[PREV] = link_prev
			#put in right before root
			last = self.root[PREV]
			last[NEXT] = self.root[PREV] = link
			link[PREV] = last
			link[NEXT] = self.root
			return result

		# load the image
		path = os.path.join(self.base_dir, set_name, name+".full.jpg")
		try:
			img = cv.LoadImage(path, 0)
		except IOError:
			print >> sys.stderr, "getCard() Loading image %s failed" % (path)
			return None

		if cv.GetSize(img) != (223, 310):
			tmp = cv.CreateImage((223, 310), 8, 1)
			cv.Resize(img,tmp)
			img = tmp
		result = gradient(img)[1]

		if self.full:
			#add as the new root
			self.root[KEY] = key
			self.root[RESULT] = result
			self.cache[key] = self.root

			#make the oldelst link the new root
			self.root = self.root[NEXT]
			del self.cache[self.root[KEY]]
			self.root[KEY] = self.root[RESULT] = None
		else:
			# put result in a new link at the front of the queue
			last = self.root[PREV]
			link = [last, self.root, key, result]
			self.cache[key] = last[NEXT] = self.root[PREV] = link
			self.currsize += 1
			self.full = (self.currsize == MAXSIZE)

		return result


def load_sets(base_dir, set_names):
	cards = []
	for dir, subdirs, fnames in os.walk(base_dir):
		set = os.path.split(dir)[1]
		if set in set_names:
			print "Loading set %s" % (set)
			for fname in fnames:
				path = os.path.join(dir, fname)
				#img = cv.LoadImage(path.encode('utf-8'),0)
				try:
					img = cv.LoadImage(path,0)
				except IOError:
					print >> sys.stderr, "\tload_sets() Loading image %s failed" % (path)
					next
				if cv.GetSize(img) != (223, 310):
					tmp = cv.CreateImage((223, 310), 8, 1)
					cv.Resize(img,tmp)
					img = tmp
				phash = dct_hash(img)
				
				cards.append((
					fname.replace('.full.jpg',''),
					set,
					phash
				))
			print "\tDone loading set %s" % (set)

	return cards

#*********************
#card matching section
def gradient(img):
	cols, rows = cv.GetSize(img)

	x_drv = cv.CreateMat(rows,cols,cv.CV_32FC1)
	y_drv = cv.CreateMat(rows,cols,cv.CV_32FC1)
	mag = cv.CreateMat(rows,cols,cv.CV_32FC1)
	ang = cv.CreateMat(rows,cols,cv.CV_32FC1)

	cv.Sobel(img, x_drv, 1, 0)
	cv.Sobel(img, y_drv, 0, 1)
	cv.CartToPolar(x_drv,y_drv,mag,ang)
	return (mag,ang)

def angle_hist(mat):
	h = cv.CreateHist([9], cv.CV_HIST_ARRAY, [(0.001,math.pi*2)], True)
	cv.CalcHist([cv.GetImage(mat)], h)
	#cv.NormalizeHist(h,1.0)
	return h

def score(card, known, method):
	r = cv.CreateMat(1, 1, cv.CV_32FC1)
	cv.MatchTemplate(card, known, r, method)
	return r[0,0]

def match_card(card, known_set, cache):
	mag, grad = gradient(card)
	phash = dct_hash(card)

	#fetch the twenty candidates with the lowest hamming distance on the phash
	#there's a 99% chance that the matching card is one of the first 20
	candidate_matches = sorted([
		(name, set_name, hamming_dist(h, phash))
		for name, set_name, h in known_set
	], key = lambda (n,s,dist): dist)

	# Not even a chance, return
	if len(candidate_matches) is 0:
		return (('',''),False)

	#we want the first 20
	candidate_matches = candidate_matches[:20]

	#calculate the correlation score,
	#and also find the 'place' of each phash score
	#(multiple candidates can tie a phash score, so we rank by count of 
	#distances < our distance)
	candidate_scores= [
		(
			name, set_name,
			dist, len([d for _,_,d in candidate_matches if d < dist]),
			ccoeff_normed(grad, cache.getCard(set_name, name))
		) for name,set_name,dist in candidate_matches
	]
	'''
	print "candidate_scores"
	for name, set_name, dist, length, coef_norm in candidate_scores:
		print "\tname %s set_name %s dist %d length %d coef_nrom %d" % (name, set_name, dist, length, coef_norm)
	'''

	#sort by score, and add a rank
	candidate_scores = sorted(candidate_scores,
			key = lambda (n,s,d,hr,ccoeff): ccoeff,
			reverse = True)
	norm_factor = 0 - candidate_scores[-1][4]
	total_score = sum([ccoeff + norm_factor for n,s,d,hr,ccoeff in candidate_scores])

	#for each score, compute the normaized features (- mean, / std_median)
	#for correlation, we want the share of normalized score
	features = [
		(
			name, set_name,
			(corr_rank - 9.5) / 5.766,
			(h_rank - 6.759942) / 4.522550,
			(dist - 17.374153) / 3.014411,
			(((corr + norm_factor) / total_score)- 0.050000) / 0.040183,
		) for corr_rank, (name, set_name, dist, h_rank, corr)
		in enumerate(candidate_scores)
	]

	#compute the score (based on fancy machine learning.)
	#todo: make more automatic and configurable
	scores = [
		(
			name, set_name,
			1.0 / (1 + math.e ** -(-6.48728 + 0.53659 * cr + -0.11304 * hr + -3.06121 * d + 2.94122 * corr))
		) for name, set_name, cr, hr, d, corr in features
	]

	#consider the scores in order
	scores = sorted(scores, key=lambda (n,s,score): score, reverse=True)

	'''
	print "score"
	for name, set_name, score in scores:
		print "\tname %s set_name %s score %d" % (name, set_name, score)
	'''

	#each score is a probability 0.0-1.0 of how likely it is that
	#that name, set_name is the correct card. we'll consider <= 0.50 a no
	# >= 0.60 a yes, and 0.5..0.6 a maybe (todo: adjust?)

	yes_cards = [(n, s) for n, s, score in scores if score >= 0.6]
	maybe_cards = [(n, s) for n, s, score in scores if 0.6 > score > 0.5]

	'''
	print "maybe cards"
	for name, set_name in maybe_cards:
		print "\tname %s set_name %s" % (name, set_name)
	print "Done maybe"

	print "yes cards"
	for name, set_name in yes_cards:
		print "\tname %s set_name %s" % (name, set_name)
	print "Done maybe"
	'''

	#if we have one or more 'yes' cards
	if len(yes_cards) > 0:
		#if they're all the same card...
		if len(set([n for n,s in yes_cards])) == 1:
			#then we're sure it's that card (unsure on set, but it's the same art, so hard to tell
			return (yes_cards[0], True)
	elif len(maybe_cards) > 0:
		#we have no 'yes' cards at all. if we have any maybe cards...
		#if they're all the same card
		if len(set([n for n,s in maybe_cards])) == 1:
			#it *could* be this card, but we're not confidant
			return (maybe_cards[0], False)

	#we can't really say what it is with any sort of confidence
	return (('',''),False)


def dct_hash(img):
	img = float_version(img)
	small_img = cv.CreateImage((32, 32), 32, 1)
	cv.Resize(img[20:190, 20:205], small_img)

	dct = cv.CreateMat(32, 32, cv.CV_32FC1)
	cv.DCT(small_img, dct, cv.CV_DXT_FORWARD)
	dct = dct[1:9, 1:9]

	avg = cv.Avg(dct)[0]
	dct_bit = cv.CreateImage((8,8),8,1)
	cv.CmpS(dct, avg, dct_bit, cv.CV_CMP_GT)

	return [dct_bit[y, x]==255.0
			for y in xrange(8)
			for x in xrange(8)]

def hamming_dist(h1,h2):
	return sum(b1 != b2 for (b1,b2) in zip(h1,h2))

LIKELY_SETS = [
	'DKA', 'ISD',
	'NPH', 'MBS', 'SOM',
	'ROE', 'WWK', 'ZEN',
	'ARB', 'CON', 'ALA',
	'EVE', 'SHM', 'MOR', 'LRW',
	'M12', 'M11', 'M10', '10E',
	'HOP',
]

