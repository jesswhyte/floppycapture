### IN PROGRESS
### environment-specific Python3 script to walk through floppy disk capture workflow
### Jess, Jan 2018

import sys
import argparse 
import os
import subprocess
import datetime
import json
import urllib
from urllib.request import urlopen
from collections import OrderedDict

#######################
###### ARGUMENTS ######
#######################

parser = argparse.ArgumentParser(
	description ="get cat data and let you pick a catkey")
parser.add_argument(
	'-c', '--call', type=str,
	help='Call or Collection Number', required=True)

### Array for all args passed to script
args = parser.parse_args()

### Variables
date = datetime.datetime.today().strftime('%Y-%m-%d')
callNum = args.call
callDum=callNum.replace('.','%20')
#catUrl = "https://search.library.utoronto.ca/details?"+catKey+"&format=json"
oneSearchUrl ="https://onesearch.library.utoronto.ca/onesearch/"+callNum+"////ajax?type=all"


#######################
###### FUNCTIONS ######
#######################

def get_json_data(url):
	response = urlopen(url)
	data = response.read().decode()
	return json.loads((data), object_pairs_hook=OrderedDict)

########################
#####  THE GOODS  ######
########################

cat_dic = (get_json_data(oneSearchUrl))
titles = '{"titles": cat_dic ["books"]["result"]["records"]["title"]}'

print(titles)

## delete holdings info (e.g. checkout info) from cat_dic
#del cat_dic["record"]["holdings"]

#getJSON = cat_dic["record"]

#with open('TEMPmetadata.json','w+') as metadata:
#	cat_dic.update(capture_dic)
#	json.dump(cat_dic, metadata)


