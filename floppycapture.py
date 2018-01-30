### IN PROGRESS
### Python script to walk through floppy disk capture workflow
### Jess, Jan 2018

import sys
import argparse 
import os
import subprocess
from subprocess import check_output
import datetime

############### CHANGE THE LIBRARY #############
# For list of library IDs, visit: uoft.me/libs #
################################################ 
lib = "ECSL"

############## CHANGE THE WORK PATH ############
#     Change the working path here 	       #
################################################ 
os.chdir("/home/jess/CAPTURED/")

### Get arguments
parser = argparse.ArgumentParser(
	description ="Script to walk through floppy disk capture workflow, Jan 2018")
parser.add_argument(
	'-m', '--mediatype', type=str, help='Use \"3.5\" or \"5.25\"',required=True,
	choices=['3.5','5.25'])
#parser.add_argument(
#	'-n', '--number', type=int, help='Number of disks in collection', required=True)
parser.add_argument(
	'-c', '--call', type=str, help='Call or Collection Number', required=False)
parser.add_argument(
	'-d','--descriptor', type=str, help='brief descriptor', required=False)
parser.add_argument(
	'-l', '--label', type=str, help='Transcript of label', required=False)

### Array for all args passed to script
args = parser.parse_args()


### Define variables
drive = "d0"
date = datetime.datetime.today().strftime('%Y-%m-%d')
mediaType = args.mediatype
#totalDisks = args.number
callNum = args.call
label = args.label

#######################
###### FUNCTIONS ######
#######################

#def getDiskId():	
#	if totalDisks == 1
#		diskID = callNum + "_001"		
#	else:
#		metadata.write("\n" + "Call/Coll number: " + callNum + "\n" + "Disk 1 of 1")
#		print "end of getDiskId function"
 	
def kfStream():
	os.system("dtc -"+drive+" -f/streams/"+callNum+"/"+callNum+"_stream -i0 -p")
	print "FC UPDATE: KF in progress..."


########################
#####  THE GOODS  ######
########################

### Create directory for output
outputPath = lib+"/"+callNum+"/"

if not os.path.exists(outputPath):
	os.makedirs(outputPath)

#verify output directory created
if os.path.exists(outputPath):
	print outputPath+" is created"

### Open our metadata.txt file
metadata = open('TEMPmetadata.txt','w')
metadata.write("Callnumber: " + callNum)
metadata.write("\n" + "Date of Capture: " + date)
metadata.write("\n" + "Label Transcript: " + label)

### Get title

os.system("curl https://onesearch.library.utoronto.ca/onesearch/"+callNum+"////ajax? | jq .books.result.records[0].title")



### Open master log file, appendable, create if it doesn't exist, opens in CAPTURED
log = open('projectlog.csv','a+')

### check Media 
if mediaType == "3.5": 
	metadata.write("\n" + "Media: " + mediaType + " floppy disk")
	drive = "d0"
elif mediaType == "5.25":
	metadata.write("\n" + "Media: " + mediaType + " floppy disk")
	drive = "d1"
else:
	print "\n" + "Incorrect media type entered, please use 3.5 or 5.25"
	raise SystemExit

### Take a Picture
### Note: fswebcam defaults to /dev/video0, if device not found...
### use ls -ltrh /dev/video* to list devices and use 
### flag -d to set device
### use cheese or VTL42 test utility to set focus, if needed

picName = callNum + "_pic.jpg"
picParameters = " --jpeg 95 -r 1600x1200 --no-banner "+outputPath+picName
os.system("fswebcam"+ picParameters)

### Check if pic successful
###################################################################TO DO

if os.path.exists(outputPath+picName):
	print "FC UPDATE: picture exists"
	metadata.write ("\n" + "Picture: " + picName)

### Get a preservation stream
#kfStream()


####################
#### END MATTER ####
####################

metadata.close()

### Rename our metadata.txt file
newMetadata = callNum + '_metadata.txt'
os.rename('TEMPmetadata.txt', outputPath+newMetadata)

### Update master log
log.write("\n"+lib+","+callNum+","+mediaType)
log.write(","+picName+","+label)

### Close master log
log.close()
