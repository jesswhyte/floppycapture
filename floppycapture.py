### IN PROGRESS
### environment-specific Python3 script to walk through floppy disk capture workflow
### Jess, Jan 2018

import sys
import argparse 
import os
import subprocess
import datetime

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
	'-m', '--mediatype', type=str, 
	help='Use \"3.5\" or \"5.25\"',required=True,
	choices=['3.5','5.25'])
#parser.add_argument(
#	'-n', '--number', type=int, help='Number of disks in collection', required=True)
parser.add_argument(
	'-c', '--call', type=str,
	help='Call or Collection Number', required=False)
parser.add_argument(
	'-t', '--transcript', type=str,
	help='Transcript of label', required=False)

### Array for all args passed to script
args = parser.parse_args()

### Define variables
drive = "d0"
date = datetime.datetime.today().strftime('%Y-%m-%d')
lib = args.lib
mediaType = args.mediatype
#totalDisks = args.number
callNum = args.call
label = args.transcript
dir = args.dir

#######################
###### FUNCTIONS ######
#######################

#def getDiskId():
#	if totalDisks == 1
#		diskID = callNum + "_001"
#	else:
#		metadata.write(
#			"\n"+"Call/Coll number: "+callNum+"\n"+"Disk 1 of 1")
#		print "end of getDiskId function"

### TO DO: rewrite kfStream in subprocess, temp)
def kfStream():
	os.system(
		"dtc -"+drive+" -fstreams/"+callNum+"/"
		+callNum+"_stream -i0 -i4 -i9 -p | tee "
		+outputPath+callNum+"_capture.log")
	print("FC UPDATE: KF in progress...")

### TO DO: Rewrite kfImage based on stdout, e.g. MFM = OK
def kfImage(fileSystem):
	os.system(
		"dtc -fstreams/"+callNum+"/"
		+callNum+"_stream00.0.raw -i0 -f"+outputPath+callNum+"_disk.img -"
		+fileSystem+" -m1")

########################
#####  THE GOODS  ######
########################

### Change working directory
os.chdir(dir)

### Create directory for output
outputPath = lib+"/"+callNum+"/"

if not os.path.exists(outputPath):
	os.makedirs(outputPath)

if os.path.exists(outputPath):
	print("FC UPDATE: "+outputPath+" is created")

### Get title
getTitle = subprocess.getoutput(
	"curl -s https://onesearch.library.utoronto.ca/onesearch/"
	+callNum+"////ajax? | jq .books.result.records[0].title")
print("FC UPDATE: title is: " +str(getTitle))

### check Media, set drive

if mediaType == "3.5":
	drive = "d0"
elif mediaType == "5.25":
	drive = "d1"

### Take a Picture
### Note: fswebcam defaults to /dev/video0, if device not found...
### use ls -ltrh /dev/video* to list devices and use 
### flag -d to set device
### use cheese or VTL42 test utility to set focus, if needed

picName = callNum + "_pic.jpg"
picParameters = " --jpeg 95 -r 1600x1200 --no-banner "+outputPath+picName
os.system("fswebcam"+ picParameters)

### Get JSON & write metadata 
metadata = open('TEMPmetadata.txt','w')

getJSON = subprocess.getoutput(
	"curl -s https://onesearch.library.utoronto.ca/onesearch/"
	+callNum+"////ajax? | jq '.books.result.records[0]|del(.covers,.holdings)'")

metadata.write(getJSON)
metadata.write("\n\n\n-------DISK INFO------\n")
metadata.write("\n" + "Call Number: " +callNum)
metadata.write("\n" + "Date of Disk Capture: " +date)
metadata.write("\n" + "Disk Label Transcript: \"" +label+"\"")
metadata.write("\n" + "Media: "+mediaType+"\" floppy disk")

### Check if pic successful
if os.path.exists(outputPath+picName):
	print("FC UPDATE: picture exists")
	metadata.write ("\n" + "Picture: " + picName)

### Get a preservation stream
go = input("Please insert disk and hit Enter")

##### take the stream only if it doesn't already exist
if not os.path.exists("streams/"+callNum+"/"+callNum+"_stream00.0.raw"):
	kfStream()

### Convert stream to image and test
fileSystem = input("Which filesytem?")

kfImage(fileSystem)

### TO DO: write filesystem metadata and verify disk image

####################
#### END MATTER ####
####################

metadata.close()

### Rename our metadata.txt file
newMetadata = callNum + '_metadata.txt'
os.rename('TEMPmetadata.txt', outputPath+newMetadata)

### Update master log
log = open('projectlog.csv','a+')

log.write(
	"\n"+lib+","+callNum+","+mediaType+
	","+str(getTitle)+","+"\""+label+"\"")
if os.path.exists(
	outputPath+picName):
	log.write(",Y")
if os.path.exists(
	outputPath+"/streams/"+callNum+"/"
                +callNum+"_stream"):
	log.write(",stream")
### Close master log
log.close()
