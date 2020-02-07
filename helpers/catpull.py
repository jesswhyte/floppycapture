#!/usr/bin/python3


##### TO DO ######
# -adapt to allow for -k entry (which would override -c entry and provide callNum)

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

### CLASS for text colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

### Add call number as argument

parser = argparse.ArgumentParser(
	description ="pull cat JSON to check holdings")

parser.add_argument(
	'-c', '--call', type=str,
	help='Call or Collection Number', required=True)

## Array for all args passed to script
args = parser.parse_args()

## get all my call Num/Call Dum variations down
callNum = args.call
callNum = callNum.upper()
callDum = callNum.replace('.','-')
callNum = re.sub(r".DISK\d","",callNum)
callUrl = str(
	"https://search.library.utoronto.ca/search?N=0&Ntx=mode+matchallpartial&Nu=p_work_normalized&Np=1&Ntk=p_call_num_949&format=json&Ntt=%s" % callNum
)


#get some json from a URL
def get_json_data(url):
	response = urlopen(url)
	data = response.read().decode()
	return json.loads((data), object_pairs_hook=OrderedDict)
	print(data)

# For when there are multiple cat keys for a call number
def disambiguate_records(d):
	print('\x1b[1;31;40m' + 'Multiple Cat Keys were found for this call number.' + '\x1b[0m')
	x = 1
	for r in d['result']['records']:
		y = 1
		print()
		print('\x1b[1;33;40m' + "Record %d" % x + '\x1b[0m')
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
			cr = int(input('Which is correct? '))
			cr = cr - 1
			ck = d['result']['records'][cr]['catkey']
			break
		except (IndexError, ValueError):
			print('Invalid response.')

	return ck


call_dic = get_json_data(callUrl)
num_results = call_dic['result']['numResults']

# If there are multiple records, prompt for which one is correct
if num_results > 1:
	# From what we've seen, there should only be one record
	if len(call_dic['result']['records']) > 1:
		sys.exit('There\'s more than one record. Script is not designed to handle this case.')
	results_dict = get_json_data(call_dic['result']['records'][0]['jsonLink'])
	catKey = disambiguate_records(results_dict)
else:
	catKey = call_dic['result']['records'][0]['catkey']

catUrl = str("https://search.library.utoronto.ca/details?%s&format=json" % catKey)

os.system("curl \'"+catUrl+"\' | jq .")

### NOTE: SUPER ENVIRONMENT SPECIFIC - GOT TO CHANGE - JUST MAKING DO FOR THIS PROJECT
#outputPath = "/home/jess/CAPTURED/ECSL/"+callDum+"/"

#if os.path.exists(outputPath):
#	print (bcolors.FAIL+"WARNING: "+str(outputPath)+" exists already"+bcolors.ENDC)
#else:
#	print (bcolors.WARNING+str(outputPath)+" does not exist"+bcolors.ENDC)


#call_dic = get_json_data(catUrl)
#print(call_dic['record']['title'])



