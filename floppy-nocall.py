#!/usr/bin/env python3

### IN PROGRESS
### Python3 script to walk through floppy disk capture workflow
### uses dtc (kryoflux floppy controller card software)
### Jess, Jan 2018

#######################
###### IMPORTS  #######
#######################

import sys
import argparse 
import os
import subprocess as subproc
import datetime
import re


#######################
###### ARGUMENTS ######
#######################

parser = argparse.ArgumentParser(
	description ="Script to walk through floppy disk capture workflow, Jan 2018")
parser.add_argument(
	'-c', '--collection', type=str,
	help='collection/accession/box/whatever', 
	required=True)
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
	'-t', '--transcript', type=str,
	help='Transcript of label, please put in single quotations and avoid commas', required=False)
parser.add_argument(
	'-n','--note', type=str,
	help='capture notes', required=False)
parser.add_argument(
	'-k', '--key',type=str,
	help='diskID',required=True)

## Array for all args passed to script
args = parser.parse_args()

###############################
########## VARIABLES ##########
###############################

drive = "d0"
date = datetime.datetime.today().strftime('%Y-%m-%d')
collection = args.collection
mediaType = args.mediatype
key = args.key
dir = args.dir
note=args.note
if args.transcript:
	label = args.transcript
else:
	label = "no disk label"

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
		"dtc -"+drive+" -fstreams/"+key+"/"
	 	+key+"_stream -i0 -i4 -i9 -i2 -t2 -l8 -p | tee "
		+outputPath+key+"_capture.log")

#takes existing stream, attemps to make image based on given fileSystem 
def kfImage(fileSystem):
	os.system(
		"dtc -fstreams/"+key+"/"
		+key+"_stream00.0.raw -i0 -f"+outputPath+key+"_disk.img -"
		+fileSystem+" -m1")

#Takes preservation stream + attempts to create i4 or MFM disk image
def kfi4():
	os.system(
		"dtc -"+drive+" -fstreams/"+key+"/"
		+key+"_stream -i0 -f"+outputPath+key+
		"_disk.img -i4 -t1 -l8 -p | tee "+outputPath+key+"_capture.log")


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
outputPath = collection+"/"+key+"/"

### JW NOTE: Check if os.path exists and then ask whether or not to proceed and how

if os.path.exists(outputPath):
	replacePath = input(bcolors.INPUT+"path already exists, proceed anyway y/n? "+bcolors.ENDC)
	if replacePath.lower() == 'y' or replacePath.lower() == 'yes':
		# replaceStream only an option, because sometimes I want to keep original photo/metadata, but want to try 			# replacing what might have been a previously unsuccessful capture, e.g. if there is another copy of disk
		replaceStream = input(bcolors.INPUT+"Replace stream/image **ONLY** y/n? "+bcolors.ENDC)
		if replaceStream.lower() == 'y' or replaceStream.lower() == 'yes':
			go = input(bcolors.INPUT+"Please insert disk and hit Enter"+bcolors.ENDC)
			if args.i4:
				kfi4()
			else:
				kfStream()
				fileSystem = input(bcolors.INPUT+"Which filesytem? "+bcolors.ENDC)
				kfImage(fileSystem)
			sys.exit("-Stream/image replaced. No other entries updated. Exiting...")
		if replaceStream.lower() == 'n' or replaceStream.lower() =='no':
			replaceStream == 'no'
			print(bcolors.OKGREEN+"Replacing "+key+" ..."+bcolors.ENDC)
	if replacePath.lower() == 'n' or replacePath.lower() == 'no':
		sys.exit("-No entries updated. Exiting...")

if not os.path.exists(outputPath):
	os.makedirs(outputPath)

### CAMERA - TAKE A PICTURE - VERY ENV SPECIFIC TO MY CAMERA
#print ("Camera is not available at this time")

photoPrompt = input("Do you want to photograph the disk? (Warning: requires device connected) [y/n]")

if photoPrompt == "y":
	picName = key + ".jpg"

	# old picParameters when using gphoto2:
	#picParameters = " --capture-image-and-download --debug --filename="+outputPath+picName
	## old picParameters when using ffmpeg:
	#picParameters = " -f video4linux2 -s 1600x1200 -i /dev/video0 -ss 0:0:6 -frames 1 -hide_banner -loglevel panic "+outputPath+picName
	
#	picParameters = " --jpeg 95 -r 1600x1200 --no-banner -S 55 --set sharpness=1 "+outputPath+picName
		
## new picParameters, testing out gphoto suggested hack Dec 2022
	print("gphoto is going to output a lot of information, sorry...")
	picParameters = " --wait-event=1s --set-config eosremoterelease='Press 1' --wait-event=1s --set-config eosremoterelease='Press 2' --wait-event=100ms --set-config eosremoterelease='Release 2' --set-config eosremoterelease='Release 1' --wait-event-and-download=5s --filename "+outputPath+picName

	gopic = input(bcolors.INPUT+"Please place disk for picture and hit Enter"+bcolors.ENDC)

	print("Wait please...taking picture...")
	

#	os.system("fswebcam"+ picParameters) ###old fswebcam command
	
	#Pic command, using gphoto2
	os.system("gphoto2"+picParameters) #gphoto2 command
	
#old Pic Command, using ffmpeg
	#os.system("ffmpeg"+picParameters) #ffmpeg command

### Double check pic worked and warn if it didn't:
	if os.path.exists(
		outputPath+picName):
		print("-Pic: %s%s taken" % (outputPath,picName))
	else:
		print(bcolors.FAIL+"-Pic: %s%s NOT TAKEN. CHECK CAMERA, CONTINUING" % (outputPath,picName))


### KRYOFLUX - GET A PRESERVATION STREAM

## Pause and give user time to put disk in 
go = input(bcolors.INPUT+"Please insert disk and hit Enter"+bcolors.ENDC)

## take the stream only if it doesn't already exist
## note: streams do not go in diskID directory
if os.path.exists("streams/"+key+"/"+key+"_stream00.0.raw"):
	replaceStream = input(bcolors.INPUT+"streams/"+key+"/"+key+"_stream00.0.raw exists, replace y/n? "+bcolors.ENDC)
	if replaceStream.lower() == 'y' or replaceStream.lower() == 'yes':
		if args.i4:
			kfi4()
		else:
			kfStream()
			fileSystem = input(bcolors.INPUT+"Which filesytem? "+bcolors.ENDC)
			kfImage(fileSystem)		
	else:
		# if replaceStream=N, still ask if user wants to update metadata/master log		
		replaceMeta = input(bcolors.INPUT+"replace metadata and create new log entry y/n? "+bcolors.ENDC)
		if replaceMeta.lower() == 'n' or replaceMeta.lower() == 'no':
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
noteupdate = input(bcolors.INPUT+"If you would like to update the disk notes (currently: "+bcolors.OKGREEN+str(note)+bcolors.ENDC+bcolors.INPUT+"), please re-enter, otherwise hit Enter (Note: input `i4` for MFM format and `i9` for Apple DOS 400k/800k format) : "+bcolors.ENDC)
if noteupdate:
	note = noteupdate
	print("-Note has been updated to: " + bcolors.OKGREEN + str(note) + bcolors.ENDC)
else:
	note = "No-transcript"
	print("-Note unchanged...")
	
## Open and update the masterlog - projectlog.csv
log = open('projectlog.csv','a+')
print("-Updating log...")

log.write(
	"\n"+collection+","+key+","+mediaType+
	","+"\""+label+"\",\""+str(note)+"\"")
if os.path.exists(
	outputPath+key+"_disk.img"):
	log.write(",img=OK")
else:
	log.write(",img=NO")
log.write(","+date)

### Close master log
log.close()

sys.exit ("-Exiting...to extract logical files from your disk images and generate .csv manifests, please run disk-img-extraction.sh on collection directory")


