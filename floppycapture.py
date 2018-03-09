#!/usr/bin/python3

### IN PROGRESS
### environment-specific Python3 script to walk through floppy disk capture workflow
### Jess, Jan 2018

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
	'-i','--i4',action='store_true',
	help='use flag to default to i4/MFM')
parser.add_argument(
	'-m', '--mediatype', type=str, 
	help='Use \"3.5\" or \"5.25\"',required=True,
	choices=['3.5','5.25'])
parser.add_argument(
	'-c', '--call', type=str,
	help='Call or Collection Number', required=True)
parser.add_argument(
	'-k', '--key', type=str,
	help='Catkey')
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
mediaType = args.mediatype
callNum = args.call
callDum=callNum.replace('.','-')
#removes the DISK[#] identifier needed for callDum, but only after creating callDum
callNum = re.sub(r".DISK\d","",callNum)
catKey = args.key
label = args.transcript
dir = args.dir
callUrl = str(
	"https://search.library.utoronto.ca/search?N=0&Ntx=mode+matchallpartial&Nu=p_work_normalized&Np=1&Ntk=p_call_num_949&format=json&Ntt=%s" % callNum
)
note=args.note

#######################
###### FUNCTIONS ######
#######################

### TODO: rewrite kfStream as subprocess, temp)
def kfStream():
	p = subproc.Popen(
		[
			'dtc',
			"-%s" % drive,
			"-fstreams/%s/%s_stream" % (callDum, callDum),
			'-i0',
			'-t2',
			'-p'
		],stdout=subproc.PIPE,stderr=subproc.PIPE
	)
	output, errors = p.communicate()
	outfile = str("%s%s_capture.log" % (outputPath, callDum))
	errfile = str("%s%s_errors.log" % (outputPath, callDum))
	with open(outfile, 'wb') as f:
		f.write(output)
	if errors:
		with open(errfile, 'wb') as f:
			f.write(errors)

	# os.system(
	# 	"dtc -"+drive+" -fstreams/"+callDum+"/"
	# 	+callDum+"_stream -i0 -t2 -p | tee "
	# 	+outputPath+callDum+"_capture.log")

#takes existing stream, attemps to make image based on given fileSystem [not in use]
def kfImage(fileSystem):
	os.system(
		"dtc -fstreams/"+callDum+"/"
		+callDum+"_stream00.0.raw -i0 -f"+outputPath+callDum+"_disk.img -"
		+fileSystem+" -m1")

#Takes preservation stream + attempts to create i4 or MFM disk image
def kfi4():
	os.system(
		"dtc -"+drive+" -fstreams/"+callDum+"/"
		+callDum+"_stream -i0 -f"+outputPath+callDum+
		"_disk.img -i4 -t1 -l8 -p | tee "+outputPath+callDum+"_capture.log")
	
#get some json from a URL
def get_json_data(url):
	response = urlopen(url)
	data = response.read().decode()
	return json.loads((data), object_pairs_hook=OrderedDict)

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

########################
#####  THE GOODS  ######
########################

### Change working directory
if not os.path.exists(dir):
	os.makedirs(dir)
	
os.chdir(dir)

### Create directory for output if it doesn't exist
outputPath = lib+"/"+callDum+"/"

### JW NOTE: changed to check if os.path exists and then ask whether or not to proceed and how

if os.path.exists(outputPath):
	replacePath = input("Call num path already exists, proceed anyway y/n? ")
	if replacePath.lower() == 'y' or replacePath.lower() == 'yes':
		# because sometimes I want to keep original photo/metadata, but want to try replacing the stream w/ copy
		replaceStream = input("Replace stream/image only y/n? ")
		if replaceStream.lower() == 'y' or replaceStream.lower() == 'yes':
			if args.i4:
				kfi4()
			else:
				kfStream()
				fileSystem = input("Which filesytem? ")
				kfImage(fileSystem)
			sys.exit("Stream/image replaced. Exiting...")
		if replaceStream.lower() == 'n' or replaceStream.lower() =='no':
			print("Replacing "+callDum+" ...")
	if replacePath.lower() == 'n' or replacePath.lower() == 'no':
		sys.exit("Exiting...")

if not os.path.exists(outputPath):
	os.makedirs(outputPath)

print("Searching callNum: "+callNum)

### GET THE TITLE AND OTHER METADATA
## make a dictionary out of the response from catUrl
## extract the title value from title key from that dictionary
## will write later in json dump

if not catKey:
	call_dic = get_json_data(callUrl)
	num_results = call_dic['result']['numResults']

	# If there are multiple records, prompt for which one is correct
	if num_results > 1:
		# From what we've seen, there should only be one record
		if len(call_dic['result']['records']) > 1:
			#JW note: added os.rmdir(dir) to backtrack on fail
			os.rmdir(dir)
			sys.exit('There\'s more than one record. Script is not designed to handle this case.')
		results_dict = get_json_data(call_dic['result']['records'][0]['jsonLink'])
		catKey = disambiguate_records(results_dict)
	else:
		catKey = call_dic['result']['records'][0]['catkey']

catUrl = str("https://search.library.utoronto.ca/details?%s&format=json" % catKey)

cat_dic = get_json_data(catUrl)

### JW NOTE: Temporarily taking out because does not account for year spaces, e.g. T385.L5585.1992 does not pass
#for cn in cat_dic['record']['holdings']['items']:
#	if callNum in cn['callnumber'].replace(' ', '').strip():
#		print('Validation of Call number succeeded.')
#		cnes = 1
#		break
#	else:
#		cnes = 0
#if cnes != 1:
### Adding backtracking on fail...
#	os.rmdir(dir)
#	sys.exit('Failed to validate Call number')


title = cat_dic['record']['title']
imprint = cat_dic['record']['imprint']
catkey = cat_dic['record']['catkey']

### PRINT THE METADATA
## x1b stuff is just to make it show up a different color so it's noticeable
print('\x1b[1;32;40m' + "Using:\nTitle: %s\nImprint: %s\nCatKey: %s" % (title, imprint, catkey) + '\x1b[0m')


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
del cat_dic['record']['holdings']

## write to TEMPmetadata.json for now
with open('TEMPmetadata.json','w+') as metadata:
	cat_dic.update(capture_dic)
	json.dump(cat_dic, metadata)


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

### JW NOTE: ADDED way to update notes at end of process
noteupdate = input("If you would like to update the disk notes (currently: "+note+"), please re-enter, otherwise hit Enter: ")
if noteupdate == "":
	note = note
	print("Note unchanged")
else:
	note = noteupdate
	print("Note has been updated to: "+note)

#convert title to string

log = open('projectlog.csv','a+')

log.write(
	"\n"+lib+","+callNum+","+str(catKey)+","+mediaType+
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
