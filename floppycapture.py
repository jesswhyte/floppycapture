# Python script to walk through floppy disk capture workflow
# Jess, Jan 2018

import sys
import argparse 
import os

#### CHANGE THE LIBRARY ####
lib = "ECSL"

# Get arguments
parser = argparse.ArgumentParser(
	description ="Script to walk through floppy disk capture workflow")
parser.add_argument(
	'-m', '--mediatype', type=str, help='Use \"3.5\" or \"5.25\"',required=True)
#parser.add_argument(
#	'-n', '--number', type=int, help='Number of disks in collection', required=True)
parser.add_argument(
	'-c', '--call', type=str, help='Call or Collection Number', required=False)
parser.add_argument(
	'-d','--descriptor', type=str, help='descriptor', required=False)
#parser.add_argument(
#	'-l', '--label', type=str, help='Transcript of label', required=False

# Array for all args passed to script
args = parser.parse_args()


# Define variables
mediaType = args.mediatype
#totalDisks = args.number
callNum = args.call
#totalDisks = sys.argv[3]
#transcript = sys.argy [4]

## Functions

def checkMedia():
	if mediaType == "3.5": 
		print mediaType
		metadata.write("\n" + "Media: " + mediaType + " floppy disk")
	elif mediaType == "5.25":
		print mediaType
		metadata.write("\n" + "Media: " + mediaType + " floppy disk")
	else:
		print "\n" + "Incorrect media type entered, please use 3.5 or 5.25"
		raise SystemExit
	print "end of checkmedia function"


#def getDiskId():	
#	if totalDisks == 1
#		diskID = callNum + "_001"		
#	else:
#		metadata.write("\n" + "Call/Coll number: " + callNum + "\n" + "Disk 1 of 1")
#		print "end of getDiskId function"
 	


# Open our metadata.txt file
metadata = open('TEMPmetadata.txt','w')

# Open master log file, appendable, create if it doesn't exist
log = open('log.csv','a+')

# What type of media is it? checkMedia function
checkMedia()


####################
#### END MATTER ####
####################

# Close our files
metadata.close()

# Rename our metadata.txt file
newMetadata = callNum + '_' + args.descriptor + '_metadata.txt'
os.rename('TEMPmetadata.txt', newMetadata)

# Update master log
log.write("\n" + lib + "," + callNum + "," + mediaType + ",")

# Close master log
log.close()
