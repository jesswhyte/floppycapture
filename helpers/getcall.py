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
import json
import urllib
import re
from urllib.request import urlopen
from collections import OrderedDict

###### ARGUMENTS ######

parser = argparse.ArgumentParser(
	description ="Script to convert catkey to callnum for, say, filenames")
parser.add_argument(
	'-k', '--key', type=str,
	help='catkey', required=True)  

## Array for all args passed to script
args = parser.parse_args()
catKey = args.key

def get_json_data(url):
	response = urlopen(url)
	data = response.read().decode()
	return json.loads((data), object_pairs_hook=OrderedDict)

### do a catalog call based on the catkey

catUrl = str("https://search.library.utoronto.ca/details?%s&format=json" % catKey) #set catalog search url based on catkey

# make a dictionary out of the response from catUrl

cat_dic = get_json_data(catUrl) #run get_json_data function using catUrl)

title = cat_dic['record']['title'] #set the $title variable based on record.title in json

callnumber = cat_dic['record']['holdings']['items'][0]['callnumber']

#print(callnumber) ## if you want to print original call number
#callnumber = callnumber.replace('.','-') ## if you wanted to replace dots with dashes
callnumber = callnumber.replace(' ','_')
print(callnumber)

sys.exit (0) #exit



