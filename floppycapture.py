### IN PROGRESS
### Python script to walk through floppy disk capture workflow
### Jess, Jan 2018

import sys
import argparse 
import os
import subprocess
import datetime

############### CHANGE THE LIBRARY #############
# For list of library IDs, visit: uoft.me/libs #
################################################ 
lib = "ECSL"

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
	'-d','--descriptor', type=str, help='brief descriptor', required=True)
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
	os.system("dtc -" + drive + " -f"  +callNum+"_stream -i0")
	print "KF in progress..."

########################
#####  THE GOODS  ######
########################

### Open our metadata.txt file
metadata = open('TEMPmetadata.txt','w')
metadata.write("callnumber: " + callNum)
metadata.write("\n" + "Date of Capture: " + date)
metadata.write("\n" + "Label Transcript: " + args.label)

### Open master log file, appendable, create if it doesn't exist
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

picName = callNum + '_' + args.descriptor + '_pic.jpg'
picParameters = " --jpeg 95 -r 1600x1200 --no-banner -d /dev/video1 " + picName
os.system("fswebcam"+ picParameters)
metadata.write ("\n" + "Picture: " + picName)

### Get a preservation stream
#kfStream()


####################
#### END MATTER ####
####################

metadata.close()

### Rename our metadata.txt file
newMetadata = callNum + '_' + args.descriptor + '_metadata.txt'
os.rename('TEMPmetadata.txt', newMetadata)

### Update master log
log.write("\n" + lib +","+ callNum +","+"\""+args.label +"\","+ mediaType)

### Close master log
log.close()
