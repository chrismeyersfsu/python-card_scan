#!/usr/bin/python
import csv
import os

abbrev2full = {
	'10E': '10-th Edition',
	'4E': '4-th Edition',
	'5E': '5-th Edition',
	'6E': '6-th Edition',
	'7E': '7-th Edition',
	'8E': '8-th Edition',
	'9E': '9-th Edition',
	'A': 'Alpha',
	'AL': 'Alliances',
	'ALA': 'Shards of Alara',
	'AN': 'Arabian Nights',
	'AP': 'Apocalypse',
	'AQ': 'Antiquities',
	'ARB': 'Alara Reborn',
	'ARC': 'Archmage',
	'AS': 'Astral',
	'AT': 'Anthologies',
	'AVG': 'Ajani VS Nicol Bolas',
	'AVR': 'Avacyn Restored',
	'B': 'Beta',
	'BD': 'Beatdown',
	'BOK': 'Betrayers of Kamigawa',
	'BR': 'Battle Royale',
	'BT': 'Box Topper',
	'CEI': 'Collector\'s Edition - International',
	'CON': 'Conflux',
	'CH': 'Chronicles',
	'CMA': 'Commander\'s Arsenal',
	'CMD': 'Commander',
	'CSP': 'Coldsnap',
	'COK': 'Champions of Kamigawa',
	'DDF': 'Elspeth VS Tezzeret',
	'DDI': 'Venser VS Koth',
	'DDJ': 'Izzet VS Golgari',
	'DDK': 'Sorin VS Tibalt',
	'DGM': 'Dragon\'s Maze',
	'DK': 'The Dark',
	'DKA': 'Dark Ascension',
	'DM': 'Deckmasters',
	'DPA': 'Duels of the Planeswalkers',
	'DRB': 'From the Vault: Dragons',
	'DS': 'Darksteel',
	'DIS': 'Dissension',
	'DVD': 'Divine VS Demonic',
	'EVE': 'Eventide',
	'EVG': 'Elves VS Goblins',
	'EX': 'Exodus',
	'FD': 'Fifth Dawn',
	'FE': 'Fallen Empires',
	'FUT': 'Future Sight',
	'FVE': 'From the Vault: Exiled',
	'FVR': 'From the Vault: Relics',
	'GEA': 'Magic Gear',
	'GPT': 'Guildpact',
	'GTC': 'Gatecrash',
	'GVL': 'Garruk VS Liliana',
	'HL': 'Homelands',
	'IA': 'Ice Age',
	'IN': 'Invasion',
	'INT': 'Introductory',
	'ISD': 'Innistrad',
	'JU': 'Judgment',
	'JVC': 'Jace VS Chandra',
	'LE': 'Legions',
	'LG': 'Legends',
	'LWN': 'Lorwyn',
	'M10': 'Magic 2010',
	'M11': 'Magic 2011',
	'M12': 'Magic 2012',
	'M13': 'Magic 2013',
	'M14': 'Magic 2014',
	'ME2': 'Masters Edition II',
	'ME3': 'Masters Edition III',
	'ME4': 'Masters Edition IV',
	'MBS': 'Mirrodin Besieged',
	'MED': 'Masters Edition',
	'MI': 'Mirage',
	'MM': 'Mercadian Masques',
	'MMA': 'Modern Masters',
	'MOR': 'Morningtide',
	'MR': 'Mirrodin',
	'NE': 'Nemesis',
	'NPH': 'New Phyrexia',
	'OD': 'Odyssey',
	'ON': 'Onslaught',
	'OS': '9x12 Cards aka Oversized',
	'P2': 'Portal Second Age',
	'P3': 'Portal Three Kingdoms',
	'PAC': 'Packs & Boxes',
	'PC2': 'Planechase (2012 Edition)',
	'PCH': 'Planechase',
	'PD2': 'Premium Deck Series: File and Lightning',
	'PD3': 'Premium Deck Series: Graveborn',
	'PDS': 'Premium Deck Series: Slivers',
	'PSH': 'Shadowmoor',
	'PS': 'Planeshift',
	'PLC': 'Planar Chaos',
	'PT': 'Portal',
	'PY': 'Prophecy',
	'PVC': 'Phyrexia VS The Coalition',
	'R': 'Revised',
	'R1': 'Renaissance (French)',
	'R2': 'Renaissance (Italian)',
	'R3': 'Renaissance (German)',
	'RAV': 'Ravnica: City of Guilds',
	'ROE': 'Rise of the Eldrazi',
	'RTR': 'Return to Ravnica',
	'S2': 'Starter 2000',
	'SC': 'Scourge',
	'SH': 'Stronghold',
	'SM': 'Summer Magic',
	'SOK': 'Saviors of Kamigawa',
	'SOM': 'Scars of Mirrodin',
	'ST': 'Starter 1999',
	'TBA': 'Knights VS Dragons',
	'TE': 'Tempest',
	'TO': 'Torment',
	'TSP': 'Time Spiral',
	'U': 'Unlimited',
	'UD': 'Urza\'s Destiny',
	'UG': 'Unglued',
	'UH': 'Unhinged',
	'UL': 'Urza\'s Legacy',
	'US': 'Urza\'s Saga',
	'V11': 'From the Vault: Legends',
	'V12': 'From the Vault: Realms',
	'VG': 'Vanguard',
	'VI': 'Visions',
	'WL': 'Weatherlight',
	'WWK': 'Worldwake',
	'ZEN': 'Zendikar',
}

class MagicAssistantCSV:
	'''
	TODO: we assume the header is already written if it's a resume.
	Instead, we should verify that assumption
	'''
	def __init__(self, file, append=True):
		global abbrev2full
		self.csvfile = None
		self.filename = file
		self._header = [ 'NAME','ID','COST','TYPE','POWER','TOUGHNESS','ORACLE','SET','RARITY','CTYPE','COUNT','LOCATION','OWNERSHIP','COMMENT','PRICE','COST','DBPRICE','RATING','ARTIST','COLLNUM','SPECIAL','FORTRADECOUNT','LANG','TEXT','OWN_COUNT','OWN_UNIQUE','ERROR' ]

		exists = True
		if append == True:
			exists = os.path.isfile(self.filename)
			self.csvfile = open(self.filename, 'a+b')
		else:
			self.csvfile = open(self.filename, 'w+b')

		self.csv = csv.writer(self.csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		if append == False or exists == False:
			self.output_header()

	def output_header(self):
		self.csv.writerow(self._header)

	def output_card(self, set_name, card_name):
		set_name_full = set_name
		if set_name not in abbrev2full:
			print "Serious problem, set abbreviation not in full table name, going with the abbreviation"
		else:
			set_name_full = abbrev2full[set_name]
		self.csv.writerow([card_name,'','','','','','',set_name_full,'','','','','','','','','','','','','','','','','','',''])

	def close(self):
		self.csvfile.close()

