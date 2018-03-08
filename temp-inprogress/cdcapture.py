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
	description ="Script to walk through floppy disk capture workflow, Jan 2018")
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
        '-d','--dir', type=str,
        help='Start directory, e.g. /home/jess/CAPTURED', required=True)
parser.add_argument(
	'-c', '--call', type=str,
	help='Call or Collection Number', required=False)
parser.add_argument(
	'-k', '--key', type=str,
	help='Catkey', required=False)
parser.add_argument(
	'-t', '--transcript', type=str,
	help='Transcript of label', required=False)
parser.add_argument(
	'-n','--note', type=str,
	help='catalog note', required=False)

## Array for all args passed to script
args = parser.parse_args()

### Variables
drive = "d0"
date = datetime.datetime.today().strftime('%Y-%m-%d')
lib = args.lib
callNum = args.call
callDum=callNum.replace('.','-')
catKey = args.key
label = args.transcript
dir = args.dir
catUrl = "https://search.library.utoronto.ca/details?"+catKey+"&format=json"
note=args.note

#######################
###### FUNCTIONS ######
#######################

#make ISO from CD


#############################################################################################3
####   LEFT OFF HERE ***************###
##############################################################################################
##############################################################################################
##############################################################################################

def cdGrab():
	os.system(
		"genisoimage -o "+callDum+"/"
		+callDum+"_stream -i0 -f"+outputPath+callDum+
		"_disk.img -i4 -t1 -l8 -p | tee "+outputPath+callDum+"_capture.log")
	
#get some json from an URL
def get_json_data(url):
	response = urlopen(url)
	data = response.read().decode()
	return json.loads((data), object_pairs_hook=OrderedDict)

########################
#####  THE GOODS  ######
########################

### Change working directory
if not os.path.exists(dir):
	os.makedirs(dir)
	
os.chdir(dir)

### Create directory for output if it doesn't exist
outputPath = lib+"/"+callDum+"/"

if not os.path.exists(outputPath):
	os.makedirs(outputPath)

if os.path.exists(outputPath):
	print("FC UPDATE: "+outputPath+" is created")

### GET THE TITLE AND OTHER METADATA
## make a dictionary out of the response from catUrl
## extract the title value from title key from that dictionary
## will write later in json dump

cat_dic = (get_json_data(catUrl))

title= cat_dic ["record"]["title"]

### check Media, set drive

if mediaType == "3.5":
	drive = "d0"
elif mediaType == "5.25":
	drive = "d1"

### TAKE A PICTURE
## Note: fswebcam defaults to /dev/video0, if device not found...
## use ls -ltrh /dev/video* to list devices and use 
## flag -d to set device
## use cheese or VTL42 test utility to set focus, if needed

picName = callDum + ".jpg"
picParameters = " --jpeg 95 -r 800x600 --no-banner -S 5 "+outputPath+picName
### TODO: write as subprocess)
os.system("fswebcam"+ picParameters)

### MORE JSON AND METADATA STUFF 
## Create dictionary of capture data
capture_dic = {
	'disk':{
	'CaptureDate': date,
	'media': mediaType+"\" floppy disk",
	'label': label,
	'library': lib,
	'diskpic': picName}
	}

## delete holdings info (e.g. checkout info) from cat_dic
del cat_dic["record"]["holdings"]

## write to TEMPmetadata.json for now
with open('TEMPmetadata.json','w+') as metadata:
	cat_dic.update(capture_dic)
	json.dump(cat_dic, metadata)

### PRINT THE TITLE
##TODO: Consider requiring user to confirm TITLE IS: +title
## x1b stuff is just to make it show up a different color so it's noticeable

print("\x1b[6;30;42m" + "FC UPDATE: title is: " +title + "\x1b[0m")


### KRYOFLUX - GET A PRESERVATION STREAM

## Pause and give user time to put disk in 
go = input("Please insert disk and hit Enter")

## take the stream only if it doesn't already exist
if not os.path.exists("streams/"+callDum+"/"+callDum+"_stream00.0.raw"):
	if args.i4:
		kfi4()
	else:
		kfStream()
		fileSystem = input("Which filesytem? ")
		if not os.path.exists(outputPath+callDum+"_disk.img"):		
			kfImage(fileSystem)

### TODO: write filesystem metadata and verify disk image - Think about if this should be separate...I think it should...

####################
#### END MATTER ####
####################

metadata.close()

### Rename our metadata.txt file
newMetadata = callDum + '.json'
os.rename('TEMPmetadata.json', outputPath+newMetadata)

### Update master log
## TODO: this should really use csv library, I was lazy

log = open('projectlog.csv','a+')

log.write(
	"\n"+lib+","+callNum+","+catKey+","+mediaType+
	",\""+str(title)+"\","+"\""+label+"\",\""+note+"\"")
if os.path.exists(
	outputPath+picName):
	log.write(",pic=OK")
else:
	log.write(",pic=NO")

if os.path.exists(
	outputPath+callDum+"_disk.img"):
	log.write(",img=OK")
else:
	log.write(",img=NO")


### Close master log
log.close()
