#!/usr/bin/env python3

#IN PROGRESS
### environment-specific Python3 script to walk through floppy disk capture workflow for gen collections items (i.e. items with callNum)
### uses qtv4l document scanner (need ffmpeg) 
### uses dtc (kryoflux floppy controller card software)
### Jess Whyte and Andy Foster, Jan 2018

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
import csv
#import pandas as pd
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
    help='output directory, e.g. /mnt/data/DISK-9999', required=True)
parser.add_argument(
	'-i','--i4',action='store_true',
	help='use flag to default to i4/MFM')
parser.add_argument(
	'-m', '--mediatype', type=str, 
	help='Use \"3.5\" or \"5.25\"',required=True,
	choices=['3.5','5.25'])
parser.add_argument(
	'--multiple', action='store_true',
	help='Multiple discs')
parser.add_argument('--journal', help='Journal or series', action='store_true')
parser.add_argument(
	'-c', '--call', type=str,
	help='Call or Collection Number')
parser.add_argument(
	'-b', '--barcode', type=str,
	help='barcode')
parser.add_argument(
	-'M', '--MMSID', type=str,
	help='MMSID'
)
#parser.add_argument(
#	'-t', '--transcript', type=str,
#	help='Transcript of label', required=False)
#parser.add_argument(
#	'-n','--note', type=str,
#	help='catalog note', required=False)

## Array for all args passed to script
args = parser.parse_args()

if not args.lib:
    print('Library or archive (-l) is required!')
    exit()

if not args.dir:
    print('Output directory (-o) is required!')
    exit()

if args.multiple:
    print()
    disknum = input('Multiple discs: Which Disc # is this, e.g. 001, 002, 003? ')
    print()

###############################
########## VARIABLES ##########
###############################

drive = "d0"
note = ""
date = datetime.datetime.today().strftime('%Y-%m-%d')
lib = args.lib
mediaType = args.mediatype
diskID = "" 

callNum = re.sub(r".DISK\w","",callNum) # removes the DISK[#] identifier needed for callDum, but only after creating callDum
catKey = args.key
#label = args.transcript
dir = args.dir
yes_string = ["y", "yes", "Yes", "YES"]
no_string = ["n", "no", "No", "NO"]

if args.barcode:
    output = subprocess.run(['bash', 'barcode-pull.sh', '-b', args.barcode, '-f'], stdout=subprocess.PIPE)
    print(f'Using barcode: {args.barcode}')
    if args.journal:
        print('JOURNAL OR SERIES identified by -J. Using item_data.alternative_call_number')
        diskID = subprocess.check_output(['jq', '-r', '.item_data.alternative_call_number', 'tmp.json']).decode('utf-8').strip()
    else:
        diskID = subprocess.check_output(['jq', '-r', '.holding_data.permanent_call_number', 'tmp.json']).decode('utf-8').strip()
    print(f'callNumber={diskID}')
elif args.MMSID:
    output = subprocess.run(['bash', 'mmsid-pull.sh', '-m', args.MMSID, '-f'], stdout=subprocess.PIPE)
    print(f'Using MMSID: {args.MMSID}')
    diskID = subprocess.check_output(['jq', '-r', '.delivery.bestlocation.callNumber', 'tmp.json']).decode('utf-8').strip()
    print(f'callNumber={diskID}')
elif args.diskID:
    print(f'Using: {args.diskID}')
    diskID = args.diskID

diskID = diskID.replace(' ', '-').replace('.', '-').upper().replace('--', '-').replace('"', '')
print(f'diskID={diskID}')

if disknum:
    diskID = f'{diskID}-DISK_{disknum}'

#note=args.note

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

def checkStream():
	if os.path.exists("streams/"+callDum+"/"+callDum+"_stream00.0.raw"):
		replaceStream = input(bcolors.INPUT+"streams/"+callDum+"/"+callDum+"_stream00.0.raw exists, replace stream y/n? "+bcolors.ENDC)
		if replaceStream.lower() == 'y' or replaceStream.lower() == 'yes':
			if args.i4:
				kfi4()
			else:
				kfStream()
				fileSystem = input(bcolors.INPUT+"Which filesytem? "+bcolors.ENDC)
				kfImage(fileSystem)		
		else:
			# if replaceStream=N, still ask if user wants to update metadata/master log
			replaceImg = input(bcolors.INPUT+"replace disk image y/n? "+bcolors.ENDC)
			if replaceImg.lower() == 'y':
				fileSystem = input(bcolors.INPUT+"Which filesytem? "+bcolors.ENDC)
				kfImage(fileSystem)		
			else:
				sys.exit()
			
	else:
		print("stream does not exist")	
		if args.i4:
		# take preservation stream and MFM image at same time		
			kfi4()
		else:
			# take preservation stream, then ask which filesystem, e.g. i9 or i4, etc.		
			kfStream()
			fileSystem = input(bcolors.INPUT+"Which filesytem? "+bcolors.ENDC)
			kfImage(fileSystem)

# takes stream only, reverted back to os.system for easier reading of output on screen 
def kfStream():
	go = input(bcolors.INPUT+"Please insert disk and hit Enter"+bcolors.ENDC)
	#command below explained: 
	#-i0 = take stream, 
	#-i4 -i9 flags say test stream against apple 400/800k and mfm, but don't actually make img
	#-t2 = make two attempts or passes
	#-p = force creation of directories in path
	#-l8 = restrict output to formatting info only
	# | tee = also output to a log, please
	os.system(
	 	"dtc -"+drive+" -fstreams/"+callDum+"/"
	 	+callDum+"_stream -i0 -i4 -i9 -t2 -l8 -p | tee "
	 	+outputPath+callDum+"_capture.log")
	os.system('spd-say "boop"')

#takes existing stream, attemps to make image based on given fileSystem 
def kfImage(fileSystem):
	outputPath = lib+"/"+callDum+"/"
	os.system(
		"dtc -fstreams/"+callDum+"/"
		+callDum+"_stream00.0.raw -i0 -f"+outputPath+callDum+"_disk.img -"
		+fileSystem+" -m1")
	os.system('spd-say "boop"')

#Takes preservation stream + attempts to create i4 aka MFM disk image
def kfi4():
	go = input(bcolors.INPUT+"Please insert disk and hit Enter"+bcolors.ENDC)
	os.system(
		"dtc -"+drive+" -fstreams/"+callDum+"/"
		+callDum+"_stream -i0 -f"+outputPath+callDum+
		"_disk.img -i4 -t1 -l8 -p | tee "+outputPath+callDum+"_capture.log")
	os.system('spd-say "boop"')
	
#get some json from a URL
def get_json_data(url):
	response = urlopen(url)
	data = response.read().decode()
	return json.loads((data), object_pairs_hook=OrderedDict)

# For when there are multiple cat keys for a call number
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

# update the notes
def updateNoteLong():
	global note
	print("\nDISK NOTES")
	print("Note currently set to: \""+bcolors.OKGREEN+note+bcolors.ENDC+"\"")
	print("TIP: Notes are for noting catalog flags or imaging failures")
	print("TIP: Try to be brief and consistent")
	print("TIP: If the resource is \"stand-alone\", please change the note")
	noteupdate = input(bcolors.INPUT+"If you would like to CHANGE the disk notes, please do so now, otherwise hit Enter: "+bcolors.ENDC)
	if noteupdate == "":
		note = str(note)
		print("Note unchanged...")
	else:
		note = noteupdate
		print("Note has been changed to: " + bcolors.OKGREEN + note + bcolors.ENDC)

def updateNote():
	global note
	noteupdate = input(bcolors.INPUT+"If you would like to ADD to the disk notes, please do so, otherwise hit Enter: "+bcolors.ENDC)
	if noteupdate == "":
		note = str(note)
		print("Note unchanged...")
	else:
		note = note + " -- " + noteupdate
		print("Note has been changed to: " + bcolors.OKGREEN + note + bcolors.ENDC)


########################
#####  THE GOODS  ######
########################

### Change working directory to -d flag setting
if not os.path.exists(dir):
	os.makedirs(dir)
os.chdir(dir)

### Check media flag (-m), set drive
if mediaType == "3.5":
	drive = "d0"
elif mediaType == "5.25":
	drive = "d1"

### Check if disk image path already exists (note: looks to CAPTURED/LIB/CALLDUM/ ***NOT*** /CAPTURED/STREAMS/)
### TO DO: should be adapted to check *all* /LIB/CALLDUM/ paths? to avoid dupes across libraries?
### Check if entry exists in project log


with open('projectlog.csv','a+') as inlog:
	reader=csv.reader(inlog)
	for row in reader:
		if not (row):
			continue
		else:
			if callDum == row[1]:
				print(bcolors.INPUT+"log entry exists for that Call Number:"+bcolors.ENDC)	
				print(row)
				replacePath = input(bcolors.INPUT+"Proceed anyway y/n? "+bcolors.ENDC)
				if replacePath.lower() == 'y' or replacePath.lower() == 'yes':
					# replaceStreamOnly is an input option, because sometimes I want to keep original photo/metadata, but want to try 			
					# replacing what might have been a previously unsuccessful capture, e.g. if there is another copy of disk
					replaceStreamOnly = input(bcolors.INPUT+"Replace stream/image **ONLY** - no metadata - y/n? "+bcolors.ENDC)
					if replaceStreamOnly.lower() == 'y' or replaceStreamOnly.lower() == 'yes':
						checkStream()
						sys.exit("Stream/image replaced. No other entries updated. Exiting...")
					if replaceStreamOnly.lower() == 'n' or replaceStreamOnly.lower() =='no':
						print(bcolors.OKGREEN+"Replacing "+callDum+" ..."+bcolors.ENDC)
				if replacePath.lower() == 'n' or replacePath.lower() == 'no': 
					sys.exit("No entries updated. Exiting...")	
						
inlog.close()			
			

outputPath = lib+"/"+callDum+"/"

if os.path.exists(outputPath):
	print("WARNING: outputPath already exists")

### Communicate we're going to search the callNum as given...
print("Searching callNum: "+callNum+"...")

### GET THE TITLE AND OTHER METADATA

### do a catcall based on -k catkey or -c callNum

if not catKey: #get that catkey
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

os.system("curl \'"+catUrl+"\' | jq .") # display json output from callNum

correctRecord = input(bcolors.INPUT+"Is this the correct record (n to exit)? "+bcolors.ENDC) #ask if this is the correct record

if correctRecord.lower() == 'n' or correctRecord.lower() == 'no':
	sys.exit("No entries updated. Exiting...")
else:
	try:	
		os.makedirs(outputPath)
	except:
		print("Error making directory, likely exists")


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

print("\nDISK LABEL TRANSCRIPTION")
print("TIP: Avoid duplicating information from cat record (e.g. authors, publishers, ISBNs, etc.)")
print("TIP: Avoid quotes please")
print("EXAMPLE: Functions - Programs - Chapter Code - Nodal Demo -- Software to accompany Applied Electronic Engineering with Mathematica -- Requires MATLAB Version 2+ and DOS 2.x")
label=input(bcolors.INPUT+"Please enter the disk label transcription: "+bcolors.ENDC)


### update note (set to default as supplementary)

updateNoteLong()

### TAKE A PICTURE
# Note: fswebcam defaults to /dev/video0, if device not found...
# use ls -ltrh /dev/video* to list devices and use 
# flag -d to set device
# use VTL42 test utility to set focus and white balance, if needed

### NOTE Mar 10 2018 - Trying out ffmpeg instead of fswebcam, fswebcam commands commented out
# TODO: write as subprocess, once choose b/w ffmpeg and fswebcam
#fswebcampicParameters = " --jpeg 95 -r 1600x1200 --no-banner -S 5 "+outputPath+picName ##old fswebcam command
#os.system("fswebcam"+ picParameters) ###old fswebcam command

picName = callDum + ".jpg"

picParameters = " -f video4linux2 -s 1600x1200 -i /dev/video0 -ss 0:0:6 -frames 1 -hide_banner -loglevel panic "+outputPath+picName

gopic = input(bcolors.INPUT+"Please place disk for picture and hit Enter"+bcolors.ENDC)

print("Wait please...taking picture...")
os.system("ffmpeg"+picParameters)

### Double check pic worked and warn if it didn't:
if os.path.exists(
	outputPath+picName):
	print("-Pic: %s%s taken" % (outputPath,picName))
else:
	print(bcolors.FAIL+"-Pic: %s%s NOT TAKEN. CHECK CAMERA + FFMPEG SETTINGS" % (outputPath,picName))

### ADD JSON METADATA ABOUT CAPTURE PROCESS 
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

## take the stream only if it doesn't already exist

checkStream()



#########################################
#### END MATTER and METADATA UPDATES ####
#########################################

metadata.close()

## User asked if they'd like to update the notes they entered
updateNote()

replaceMeta = input(bcolors.INPUT+"replace metadata and create new log entry y/n? "+bcolors.ENDC)
if replaceMeta.lower() == 'n' or replaceMeta.lower() == 'no':
	# if replaceMeta=N, close out and exit, otherwise carry on
	#metadata.close()
	sys.exit ("-Exiting...")

### Rename our metadata.txt file
newMetadata = callDum + '.json'
os.rename('TEMPmetadata.json', outputPath + newMetadata)
print("Updated metadata file: "+ outputPath + newMetadata)

### Update master log
## TODO: this should really use csv library, I was lazy


## Open and update the masterlog - projectlog.csv
log = open('projectlog.csv','a+')
print("Updating log...")

log.write(
	"\n"+lib+","+callDum+","+str(catKey)+","+mediaType+
	",\""+str(title)+"\",\""+label+"\",\""+note+"\"")
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
log.write(","+date)

### Close master log
log.close()

sys.exit ("Exiting...")



