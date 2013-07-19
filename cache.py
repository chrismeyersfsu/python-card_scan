#!/usr/bin/python
import cv
import scan_card
from scan_card import ScanCard, overlay_text_on_image
import match_card
import os

BASE_SET_DIR = "/home/meyers/Data/magic_sets"
CACHE_DIR = BASE_SET_DIR 
CAPTURE_NUM = 1
font = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX, .75, .75, 0, 2)

# Load the known sets
SETS = [
	"MM", "From the Vault: Exiled", "Unhinged", "M13", "New Phyrexia", "DDJ", "Starter 2000", "Premium Deck Series: Fire and Lightning", "CH", "R", 
	"ON", "Future Sight", "Shards of Alara", "PT", "Ravnica: City of Guilds", "5E", "UD", "HL", "U", "B", 
	"PC2", "Magic 2010", "Beatdown Box Set", "US", "Lorwyn", "JU", "Mirrodin Besieged", "Dissension", "From the Vault: Legends", "From the Vault: Relics", 
	"9E", "Innistrad", "Premium Deck Series: Slivers", "From the Vault: Dragons", "BRB", "Planechase", "Premium Deck Series: Graveborn", "P3", "AQ", "A", 
	"Duel Decks: Elves vs. Goblins", "Planar Chaos", "Worldwake", "Eventide", "4E", "SC", "Magic 2012", "IN", "Magic 2011", "VI", 
	"CMD", "UG", "GP", "Duel Decks: Jace vs. Chandra", "DGM", "DS", "NE", "LE", "MR", "RTR", 
	"Dark Ascension", "Time Spiral Timeshifted", "Alara Reborn", "Duel Decks: Venser vs. Koth", "MI", "Duel Decks: Elspeth vs. Tezzeret", "Rise of the Eldrazi", "AP", "CM1", "CFX", 
	"6E", "DK", "Time Spiral", "Duel Decks: Knights vs. Dragons", "Champions of Kamigawa", "ST", "PS", "FD", "Duel Decks: Divine vs. Demonic", "SH", 
	"CS", "Saviors of Kamigawa", "AL", "EX", "FE", "Morningtide", "Scars of Mirrodin", "LG", "7E", "GTC", 
	"UL", "TE", "Duel Decks: Ajani vs. Nicol Bolas", "IA", "AN", "Duel Decks: Phyrexia vs. the Coalition", "OD", "V12", "P2", "Zendikar", 
	"TO", "Shadowmoor", "Betrayers of Kamigawa", "WL", "Tenth Edition", "8E", "Duel Decks: Garruk vs. Liliana", "PY", "Archenemy", "DDK", 
	"Avacyn Restored", "MMA"
]
SETS = [
		"Innistrad"
]
SETS = [
"S00", "MM", "ROE", "M13", "DDJ", "ALA", "DDC", "M10", "CH", "DDI", 
"R", "DRB", "ON", "ISD", "PT", "5E", "UD", "HL", "U", "B", 
"PC2", "US", "JU", "V10", "DDE", "FUT", "WWK", "9E", "DDH", "BRB", 
"AVR", "P3", "EVG", "M12", "AQ", "A", "SHM", "M11", "V09", "4E", 
"ARC", "SC", "IN", "DIS", "ZEN", "VI", "SOK", "CMD", "RAV", "UNH", 
"UG", "GP", "PLC", "DGM", "DS", "V11", "NE", "LE", "MR", "RTR", 
"NPH", "H09", "TSP", "MI", "PD3", "AP", "CM1", "CFX", "6E", "DK", 
"HOP", "SOM", "ST", "PS", "DD2", "FD", "DKA", "DDG", "ARB", "SH", 
"CS", "PD2", "10E", "AL", "EX", "FE", "BOK", "BD", "MBS", "DDF", 
"EVE", "LG", "7E", "GTC", "UL", "TE", "DDD", "IA", "AN", "OD", 
"V12", "P2", "TO", "TSB", "WL", "LRW", "CHK", "8E", "MOR", "PY", 
"DDK", "MMA"
]
known = match_card.load_sets(BASE_SET_DIR, SETS)

# Cache for some reason
cache = match_card.GradientCache(CACHE_DIR)

# Open the camera stream
#cam = cv.CreateCameraCapture(-1)
cam = cv.CreateCameraCapture(1)

scanCard = ScanCard(cam)

# win, snapshot, match, background
scan_card.setup_windows()

match_pending = False

while True:
	'''
	key_code = cv.WaitKey(10)
	if key_code == 98:
		background = grab_background(cam)
	'''

	capture = scanCard.check_for_card()
	if capture is not None:
		print "Card captured, proceeding to find a match"
		(card, set_name), is_sure = match_card.match_card(capture, known, cache)

		# Display matched information
		if is_sure == True:
			print "\tMatch Found!"
			#card = unicode(card.decode('UTF-8'))
			
			path = os.path.join(BASE_SET_DIR, set_name, card+".full.jpg")
			try:
				tmp = cv.LoadImage(path)
				overlay_text_on_image(tmp, "%s - %s" % (card, set_name), font)
				cv.ShowImage("match", tmp)
				cv.ResizeWindow("match", 800, 600)
				match_pending = True
			except IOError:
				print "test.py Could not load card %s" % (path)

		else:
			print "\tMatch not found"
	
	
	scanCard.display_snapshot()
	key_code = cv.WaitKey(10)
	if key_code == 114:
		scanCard.update_background()
		scanCard.display_background()
		print "Updated background image"

