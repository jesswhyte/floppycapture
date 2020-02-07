#!/usr/bin/env python3

#IN PROGRESS
### environment-specific Python3 script to pull catalog metadata and add processing metadata

### Jess Whyte 

#######################
###### IMPORTS  #######
#######################

import sys
import argparse 
import os
import subprocess as subproc
import datetime
import json
import urllib
import re
#import csv
from urllib.request import urlopen
from collections import OrderedDict

#######################
###### ARGUMENTS ######
#######################

parser = argparse.ArgumentParser(
	description ="Script to pull catalog metadata and add processing metadata (e.g. date processed)")
parser.add_argument(
	'-l', '--lib', type=str,
	help='Library, for a list of library IDs, visit ufot.me/libs ', 
	required=True,
	choices=['ARCH','ART','ASTRO','CHEM','CRIM',
	'DENT','OPIRG','EARTH','EAL','ECSL','FCML',
	'FNH','GERSTEIN','INFORUM','INNIS','KNOX',
	'LAW','MDL','MATH','MC','PONTIF','MUSIC',
	'NEWCOLLEGE','NEWMAN','OISE','PJRC','PHYSICS',
	'REGIS','RCL','UTL','ROM','MPI','STMIKES',
	'TFRBL','TRIN','UC','UTARMS','UTM','UTSC','VIC'])
#parser.add_argument(
 #       '-d','--dir', type=str,
  #      help='Start directory, e.g. /home/jess/CAPTURED', required=True)
parser.add_argument(
	'-m', '--mediatype', type=str, 
	help='Use \"3.5\" or \"5.25\" or CD or USB-key',required=True,
	choices=['3.5','5.25', 'CD', 'USB-key'])
parser.add_argument(
	'-c', '--call', type=str,
	help='Call or Collection Number', required=True) 
parser.add_argument(
	'-k', '--key', type=str,
	help='Catkey')

## Array for all args passed to script
args = parser.parse_args()

###############################
########## VARIABLES ##########
###############################

date = datetime.datetime.today().strftime('%Y-%m-%d')
lib = args.lib
mediaType = args.mediatype
callNum = args.call 
callNum = callNum.upper() #makes callNum uppercase
callDum=callNum.replace('.','-') #replaces . in callNum with - for callDum
callNum = re.sub(r".DISK\w","",callNum) # removes the DISK[#] identifier needed for callDum, but only after creating callDum
catKey = args.key
#dir = args.dir
callUrl = str(
	"https://search.library.utoronto.ca/search?N=0&Ntx=mode+matchallpartial&Nu=p_work_normalized&Np=1&Ntk=p_call_num_949&format=json&Ntt=%s" % callNum
)

#################################
########## CLASS STUFF ##########
#################################

# font colors for notices/warnings, visit https://gist.github.com/vratiu/9780109 for a nice guide to the color codes if you want to change
class bcolors:
    OKGREEN = '\033[92m' #green
    INPUT = '\033[93m' #yellow, used for when user input required
    FAIL = '\033[91m' #red, used for failure
    ENDC = '\033[0m' # end color
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREENBLOCK = '\x1b[1;31;40m' # green with background, used for updates user should check (e.g. Title/Cat report)
    ENDGB = '\x1b[0m' #end x1b block

####################################
############ FUNCTIONS #############
####################################

# Get json from a URL (we're going to use callURL), read and decode the response and then put in ordered dictionary
def get_json_data(url):
	response = urlopen(url)
	data = response.read().decode()
	return json.loads((data), object_pairs_hook=OrderedDict)

# For when there are multiple cat keys for a call number - we might not need this for this, if we're using catkeys only
def disambiguate_records(d):
	print(bcolors.BOLD + 'Multiple Cat Keys were found for this call number.' + bcolors.ENDC)
	x = 1
	for r in d['result']['records']:
		y = 1
		print()
		print(bcolors.GREENBLOCK + "Record %d" % x + bcolors.ENDGB)
		print("Title: %s" % r['title'])
		print("Imprint: %s" % r['imprint'])
		print("CatKey: %s" % r['catkey'])
		print('Holdings:')
		for h in r['holdings']['items']:
			print("Holding %d" % y)
			print("Call Number: %s\n" % h['callnumber'])
			y += 1
		x += 1
	while True:
		try:
			cr = int(input(bcolors.INPUT+'Which is correct? '+bcolors.ENDC))
			cr = cr - 1
			ck = d['result']['records'][cr]['catkey']
			break
		except (IndexError, ValueError):
			print(bcolors.FAIL+'Invalid response.'+bcolors.ENDC)

	return ck

########################
#####  THE GOODS  ######
########################

## Commented out output stuff, can just > to $file.json ??? thoughts ????
#outputPath = lib+"/"+callDum+"/"

#if os.path.exists(outputPath):
#	print("WARNING: outputPath already exists")

### Communicate we're going to search the callNum as given...
#print("Searching callNum: "+callNum+"...")

### GET THE TITLE AND OTHER METADATA #######

### do a catcall based on -k catkey or -c callNum

if not catKey: #get that catkey if we don't have it
	call_dic = get_json_data(callUrl)
	num_results = call_dic['result']['numResults']

	# If there are multiple records, prompt for which one is correct
	if num_results > 1:
		# From what we've seen, there should only be one record
		if len(call_dic['result']['records']) > 1:
			sys.exit(bcolors.FAIL+'There\'s more than one record. Script is not designed to handle this case. Please set disk aside or consult catalog'+bcolors.ENDC)
		results_dict = get_json_data(call_dic['result']['records'][0]['jsonLink'])
		catKey = disambiguate_records(results_dict)
	else: #option to take catkey given with -k flag (e.g. if you want to set a custom callnum)
		catKey = call_dic['result']['records'][0]['catkey']

catUrl = str("https://search.library.utoronto.ca/details?%s&format=json" % catKey) #set catalog search url based on catkey

os.system("curl \'"+catUrl+"\' | jq .") # display json output from catKey

correctRecord = input(bcolors.INPUT+"Is this the correct record (n to exit)? "+bcolors.ENDC) #ask if this is the correct record

if correctRecord.lower() == 'n' or correctRecord.lower() == 'no':
	sys.exit("No entries updated. Exiting...")
#else:
#	try:	
#		os.makedirs(outputPath) #### I don't know if we need this if >> to a file
#	except:
#		print("Error making directory, likely exists")


# make a dictionary out of the response from catUrl
# extracts the title value from title key from that dictionary
# will write later in the json dump

#update dictionary for json write
cat_dic = get_json_data(catUrl)
title = cat_dic['record']['title']
imprint = cat_dic['record']['imprint']
catkey = cat_dic['record']['catkey']
description = cat_dic['record']['description']

### PRINT THE METADATA
## x1b stuff is just to make it show up a different color so it's noticeable

print(bcolors.GREENBLOCK + "Confirming:\nTitle: %s\nImprint: %s\nCatKey: %s \nDescription: %s" % (title, imprint, catkey, description) + bcolors.ENDGB)


### ADD JSON METADATA ABOUT CAPTURE PROCESS 
## Create dictionary of capture data
capture_dic = {
	'disk':{
	'CaptureDate': date,
	'media': mediaType,
	'library': lib,
	}

## delete holdings info (e.g. checkout info) from cat_dic
del cat_dic['record']['holdings']

## write to TEMPmetadata.json for now
with open('TEMPmetadata.json','w+') as metadata:
	cat_dic.update(capture_dic)
	json.dump(cat_dic, metadata)


# metadata.close 
metadata.close()


### Rename our metadata.txt file
newMetadata = callDum + '.json'
os.rename('TEMPmetadata.json', outputPath + newMetadata)
print("Updated metadata file: "+ outputPath + newMetadata)




sys.exit ("Exiting...")



