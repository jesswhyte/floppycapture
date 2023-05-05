#!/usr/bin/env python3

### IN PROGRESS
### Python3 script to walk through floppy disk capture workflow
### uses dtc (kryoflux floppy controller card software)
### Jess, Jan 2018
### post-LSP upgrade changes, 2022/2023

#######################
###### IMPORTS  #######
#######################

import sys
import argparse 
import os
import subprocess
import datetime
import re
import json


#######################
###### ARGUMENTS ######
#######################

parser = argparse.ArgumentParser(
	description ="Script to walk through floppy disk capture workflow")
## listing required arguments
required_group = parser.add_argument_group('Required')
required_group.add_argument(
    '-d','--dir', type=str,
    help='Start directory, e.g. /mnt/data/LIB/', required=True)
required_group.add_argument(
	'-m', '--mediatype', type=str, 
	help='Use \"3.5\" or \"5.25\"',required=True,
	choices=['3.5','5.25'])
required_group.add_argument(
	'-l', '--lib', type=str,
	help='Library', 
	required=True,
	choices=['ARCH','ART','ASTRO','CHEM','CRIM',
	'DENT','OPIRG','EARTH','EAL','ECSL','FCML',
	'FNH','GERSTEIN','INFORUM','INNIS','KNOX',
	'LAW','MDL','MATH','MC','PONTIF','MUSIC',
	'NEWCOLLEGE','NEWMAN','OISE','PJRC','PHYSICS',
	'REGIS','RCL','UTL','ROM','MPI','STMIKES',
	'TFRBL','TRIN','UC','UTARMS','UTM','UTSC','VIC'])
required_group.add_argument(
	'-c', '--collection', type=str,
	help='use coll/accession ID when processing archival collections, for library projects, make a project ID or use ticket #', )

## creating an argument group = Archival
archival_group = parser.add_argument_group('For archival content')
archival_group.add_argument(
    '-A', '--archival', action='store_true',
    help='use -A archival flag for processing disks from archival collections or without call numbers. Requires the use of -c and -k')
archival_group.add_argument(
	'-k', '--diskID',type=str,
	help='e.g. 0001, 0002, 0003. Required when using -A')
## listing optional arguments
parser.add_argument(
	'-i','--i4',action='store_true',
	help='use -i flag to default to i4/MFM image choice')
parser.add_argument(
	'-b', '--barcode', type=str,
	help='barcode')
parser.add_argument(
	'-M', '--MMSID', type=str,
	help='MMSID')
parser.add_argument(
	'--multiple', action='store_true',
	help='use --multiple to indicate there are multiple discs for this object')
parser.add_argument(
	'-t', '--transcript', type=str,
	help='Transcript of label, please put in single quotations and avoid commas', required=False)
parser.add_argument(
	'-n','--note', type=str,
	help='capture or processing notes', required=False)

## Array for all args passed to script
args = parser.parse_args()
if args.archival and not args.diskID:
    parser.error('The -k diskID argument is required when using the -A flag.')
    
if args.archival and (args.barcode or args.MMSID):
    parser.error('The -b <barcode> and -M <MMSID> arguments are not allowed when using the -A flag.')

if args.diskID and (args.barcode or args.MMSID):
	parser.error('You have provided a -k <diskID> AND a barcode or MMSID.')

###############################
########## VARIABLES ##########
###############################

drive = "d0"
date = datetime.datetime.today().strftime('%Y-%m-%d')
collection = args.collection
mediaType = args.mediatype
dir = args.dir
if args.note:
	note=args.note
else:
	note=""
if args.transcript:
	label = args.transcript
else:
	label = "no disk label"
yes_string = ["y", "yes", "Yes", "YES"]
no_string = ["n", "no", "No", "NO"]
diskID=""

## Getting to a diskID
# then check if a barcode is provided:
print()
if args.barcode:
    output = subprocess.run(['bash', 'barcode-pull.sh', '-b', args.barcode, '-f'], stdout=subprocess.PIPE)
    print(f'Using barcode: {args.barcode}')
    output_json = json.loads(output.stdout.decode('utf-8'))
    diskID = output_json['holding_data']['permanent_call_number']
    print(f'callNumber = {diskID}')
# then an MMSID: 
if args.MMSID:
    output = subprocess.run(['bash', 'mmsid-pull.sh', '-m', args.MMSID, '-f'], stdout=subprocess.PIPE)
    print(f'Using MMSID: {args.MMSID}')
    output_json = json.loads(output.stdout.decode('utf-8'))
    diskID = output_json['delivery']['bestlocation']['callNumber']
    print(f'callNumber = {diskID}')
elif args.diskID:
    print(f'No barcode or MMSID provided.')
    diskID = args.diskID

## clean up diskID, strip spaces and weird characters, remove any trailing periods, etc.: 
diskID = diskID.replace(' ', '-').replace('.', '-').upper().replace('--', '-').replace('"', '')
diskID = diskID.strip('-')
    
if args.multiple:
    print()
    disknum = input('Multiple discs: Which Disc # is this, e.g. 001, 002, 003? ')
    print()
    diskID = f'{diskID}-DISK_{disknum}'
    
print(f'collection = {collection}')
print(f'diskID = {diskID}')
print(f'output directory = {dir}')
print()


#################################
########## CLASS STUFF ##########
#################################

# font colors, visit https://gist.github.com/vratiu/9780109 for a nice guide to the color codes
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

### TODO: rewrite kfStream as subprocess, temp)
def kfStream():
	os.system(
		"dtc -"+drive+" -fstreams/"+diskID+"/"
	 	+diskID+"_stream -i0 -i4 -i9 -i2 -t2 -l8 -p | tee "
		+outputPath+diskID+"_capture.log")

#takes existing stream, attemps to make image based on given fileSystem 
def kfImage(fileSystem):
	os.system(
		"dtc -fstreams/"+diskID+"/"
		+diskID+"_stream00.0.raw -i0 -f"+outputPath+diskID+"_disk.img -"
		+fileSystem+" -m1")

#Takes preservation stream + attempts to create i4 or MFM disk image
def kfi4():
	os.system(
		"dtc -"+drive+" -fstreams/"+diskID+"/"
		+diskID+"_stream -i0 -f"+outputPath+diskID+
		"_disk.img -i4 -t1 -l8 -p | tee "+outputPath+diskID+"_capture.log")


########################
#####  THE GOODS  ######
########################

### check Media, set drive
if mediaType == "3.5":
	drive = "d0"
elif mediaType == "5.25":
	drive = "d1"

### Change working directory
if not os.path.exists(dir):
	os.makedirs(dir)
	
os.chdir(dir)

### Create directory for output if it doesn't exist
outputPath = collection+"/"+diskID+"/"

### JW NOTE: Check if os.path exists and then ask whether or not to proceed and how

if os.path.exists(outputPath):
	replacePath = input(bcolors.INPUT+"Path already exists, proceed anyway? [y/n]"+bcolors.ENDC)
	if replacePath.lower() in yes_string:
		# replaceStream only an option, because sometimes I want to keep original photo/metadata, but want to try 			# replacing what might have been a previously unsuccessful capture, e.g. if there is another copy of disk
		replaceStream = input(bcolors.INPUT+"Replace stream/image **ONLY** (i.e. no photography)? [y/n]"+bcolors.ENDC)
		if replaceStream.lower() in yes_string:
			go = input(bcolors.INPUT+"Please insert disk and hit Enter"+bcolors.ENDC)
			if args.i4:
				kfi4()
			else:
				kfStream()
				fileSystem = input(bcolors.INPUT+"Which filesytem? "+bcolors.ENDC)
				kfImage(fileSystem)
			sys.exit("-Stream/image replaced. No other entries updated. Exiting...")
		if replaceStream.lower() in no_string:
			replaceStream == 'no'
			print(bcolors.OKGREEN+"Replacing "+diskID+" ..."+bcolors.ENDC)
	if replacePath.lower() in no_string:
		sys.exit("-No entries updated and files created. Exiting...")

if not os.path.exists(outputPath):
	os.makedirs(outputPath)

### CAMERA - TAKE A PICTURE - VERY ENV SPECIFIC TO MY CAMERA
#print ("Camera is not available at this time")

picName = diskID + ".jpg"
PicPath = outputPath + picName
#Force overwrite the image file, and slient the output of the photo taking script by gphoto2 in the terminal. Updated in Jan 2023
picParameters = " --wait-event=1s --set-config eosremoterelease='Press 1' --wait-event=1s --set-config eosremoterelease='Press 2' --wait-event=100ms --set-config eosremoterelease='Release 2' --set-config eosremoterelease='Release 1' --wait-event-and-download=5s  --filename "+outputPath+picName+" --force-overwrite " + "> /dev/null" 

photoPrompt = input("Do you want to photograph the disk (Warning: requires device connected)? [y/n]")

## Modified version based on Dec 2022 to fit in the new picParameters. Updated in Jan 2023
if photoPrompt in yes_string:
	if os.path.exists(PicPath):
		replacephotopath = input(bcolors.INPUT+"Photo already exists, proceed anyway? [y/n]"+bcolors.ENDC)
		if replacephotopath in yes_string:
			gopic = input(bcolors.INPUT+"Please place disk for picture and hit Enter"+bcolors.ENDC)
			print("Wait please...taking picture...")
			os.system("gphoto2"+picParameters) #gphoto2 command
			if os.path.exists(PicPath):
				print("-Pic: %s is captured" % (PicPath))
		else:
			print("No photo is taken/modified")
	else:
		gopic = input(bcolors.INPUT+"Please place disk for picture and hit Enter"+bcolors.ENDC)
		print("Wait please...taking picture...")
		os.system("gphoto2"+picParameters) #gphoto2 command
		if os.path.exists(PicPath):
			print("-Pic: %s is captured" % (PicPath))
else:
	print("No photo is taken/modified")

### Double check pic worked and warn if it didn't (Updated in Jan 2023)
if not os.path.exists(PicPath):
	print(bcolors.FAIL+"-Pic: %s NOT TAKEN. CHECK CAMERA, CONTINUING" % (PicPath))


### KRYOFLUX - GET A PRESERVATION STREAM

## Pause and give user time to put disk in 
go = input(bcolors.INPUT+"Please insert disk and hit Enter"+bcolors.ENDC)

## take the stream only if it doesn't already exist
## note: streams do not go in diskID directory
if os.path.exists("streams/"+diskID+"/"+diskID+"_stream00.0.raw"):
	replaceStream = input(bcolors.INPUT+"streams/"+diskID+"/"+diskID+"_stream00.0.raw exists, replace? [y/n]"+bcolors.ENDC)
	if replaceStream.lower() in yes_string:
		if args.i4:
			kfi4()
		else:
			kfStream()
			fileSystem = input(bcolors.INPUT+"Which filesytem? "+bcolors.ENDC)
			kfImage(fileSystem)		
	else:
		# if replaceStream=N, still ask if user wants to update metadata/master log		
		replaceMeta = input(bcolors.INPUT+"replace metadata and create new log entry? [y/n]"+bcolors.ENDC)
		if replaceMeta.lower() in no_string:
			# if replaceMeta=N, close out and exit, otherwise carry on
			metadata.close()
			sys.exit ("-Exiting...")
else:
	if args.i4:
		# take preservation stream and MFM image at same time		
		kfi4()
	else:
		# take preservation stream, then ask which filesystem, e.g. i9 or i4, etc.		
		kfStream()
		fileSystem = input(bcolors.INPUT+"Which filesytem? "+bcolors.ENDC)
		if not os.path.exists(outputPath+"_disk.img"):	
			# create image from stream, based on provided filesystem	
			kfImage(fileSystem)

#########################################
#### END MATTER and METADATA UPDATES ####
#########################################


### Update master log


## User asked if they'd like to update the notes they entered
noteupdate = input(bcolors.INPUT+"If you would like to update the disk notes (currently: "+bcolors.OKGREEN+str(note)+bcolors.ENDC+bcolors.INPUT+"), please re-enter, otherwise hit Enter: "+bcolors.ENDC)
if noteupdate:
	note = noteupdate
	print("-Note has been updated to: " + bcolors.OKGREEN + str(note) + bcolors.ENDC)
else:
	note = "No-notes" #Changed to "No-notes" for better clarity
	print("-Note unchanged...")
	
## Open and update the masterlog - projectlog.csv
log = open('projectlog.csv','a+')
print("-Updating log...")

log.write(
	"\n"+collection+","+diskID+","+mediaType+
	","+"\""+label+"\",\""+str(note)+"\"")
if os.path.exists(
	outputPath+diskID+"_disk.img"):
	log.write(",img=OK")
else:
	log.write(",img=NO")
log.write(","+date)

### Close master log
log.close()

sys.exit ("-Exiting...to extract logical files from your disk images and generate .csv manifests, please run disk-img-extraction.sh on collection directory")


