#!/usr/bin/env python3
### Python3 script to pull catalog metadata and add processing metadata, outputs to stdout
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
from urllib.request import urlopen
from collections import OrderedDict

#######################
###### ARGUMENTS ######
#######################

parser = argparse.ArgumentParser(
	description ="Script to pull catalog metadata, remove holdings info (e.g. checkout status), end add processing metadata (e.g. date processed)")
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
parser.add_argument(
	'-m', '--mediatype', type=str, 
	help='Use \"3.5\" or \"5.25\" or \"CD\" or \"USB\"',required=True,
	choices=['3.5','5.25', 'CD', 'USB'])
parser.add_argument(
	'-k', '--key', type=str,
	help='catkey', required=False)  

## Array for all args passed to script
args = parser.parse_args()

###############################
########## VARIABLES ##########
###############################

date = datetime.datetime.today().strftime('%Y-%m-%d') # set's today's date as $date variable
lib = args.lib
mediaType = args.mediatype
catKey = args.key

####################################
############ FUNCTIONS #############
####################################

# Get json from a URL (we're going to use keyURL), read and decode the response and then put in ordered dictionary
def get_json_data(url):
	response = urlopen(url)
	data = response.read().decode()
	return json.loads((data), object_pairs_hook=OrderedDict)

########################
#####  THE GOODS  ######
########################

### do a catalog call based on the catkey

catUrl = str("https://search.library.utoronto.ca/details?%s&format=json" % catKey) #set catalog search url based on catkey

# make a dictionary out of the response from catUrl

cat_dic = get_json_data(catUrl) #run get_json_data function using catUrl)
title = cat_dic['record']['title'] #set the $title variable based on record.title in json
imprint = cat_dic['record']['imprint'] #set the $imprint variable
catkey = cat_dic['record']['catkey'] #set the $catkey variable
description = cat_dic['record']['description'] #set the $description variable


## Create dictionary of capture data to add to json metadata
capture_dic = {
	'disk':{
	'CaptureDate': date,
	'media': mediaType,
	'library': lib}
	}

## delete holdings info (e.g. checkout info) from cat_dic
del cat_dic['record']['holdings']

## add capture dictionary to cat_dic dictionary
cat_dic.update(capture_dic)

## dump resulting json to stdout/screen:
json.dump(cat_dic, sys.stdout, indent=4) ## outputs json dump of created dictionary to system sydout, indented, can pipe to file or screen

print() #line break
sys.exit (0) #exit



