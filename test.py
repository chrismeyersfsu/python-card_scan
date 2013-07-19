#!/usr/bin/python
import time
import cv
import scan_card
from scan_card import ScanCard, overlay_text_on_image
import match_card
from match_card import MatchCard
import os
import sys
from setcache import save_set_cache, load_set_cache
from text2speech import TTS
from magicassistantcsv import MagicAssistantCSV
import pickle

BASE_SET_DIR = "/home/meyers/Software/card_scan/data/win_cards/"
SET_CACHE_FILE = "data/set_cache"
CSV_FILE = "data/inventory.csv"


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

# Load the sets
known = load_set_cache(SET_CACHE_FILE)
if known is None:
	print "Processing magic sets"
	known = match_card.load_sets(BASE_SET_DIR, SETS)
	print "Saving sets to cache file %s" % (SET_CACHE_FILE)
	save_set_cache(SET_CACHE_FILE, known)
print "Magic sets loaded and ready"

cam = cv.CreateCameraCapture(-1)	# Camera, -1 indicates autofind
#cam = cv.CreateCameraCapture(1)
# TODO: detect failed to load camera, CAN NOT simply check if cam is None

scan_card.setup_windows() # win, snapshot, match, background
tts = TTS()		# Load test to speech festival
cache = match_card.GradientCache(BASE_SET_DIR)	# memory cache
scanCard = ScanCard(cam)
matchCard = MatchCard(BASE_SET_DIR)
csv = MagicAssistantCSV(CSV_FILE, append=True)

while True:
	capture = scanCard.check_for_card()
	if capture is not None:
		print "Card captured, proceeding to find a match"
		(card, set_name), is_sure = match_card.match_card(capture, known, cache)

		# Display matched information
		if is_sure == True:
			print "\tMatch Found!"
			res = matchCard.set(set_name, card)
			if res == True:
				matchCard.display()
				tts.say(card)
			else:
				tts.say("INVALID")
		else:
			print "\tMatch not found"
			tts.say("DINK")
	
	scanCard.display_snapshot()

	# Refresh background image ?
	key_code = cv.WaitKey(10)
	if key_code == 114:
		scanCard.update_background()
		scanCard.display_background()
		print "Updated background image"
	elif key_code == 98: #b
		csv.output_card(matchCard.get_set_name(), matchCard.get_card_name())
		tts.say("ADDED")

csv.close()
