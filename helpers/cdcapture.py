### IN PROGRESS
### environment-specific Python3 script to walk through cd-rom capture
### Jess, Jan 2018

import sys
import argparse 
import os
import subprocess
import datetime
import json
import urllib
from urllib.request import urlopen # pip install requests
from collections import OrderedDict

#######################
###### ARGUMENTS ######
#######################

parser = argparse.ArgumentParser(
	description ="Script for CD-ROM workflow, Jan 2018")
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
        help='Start directory, e.g. /home/bcadmin/CAPTURED', required=True)
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
drive = "/dev/cdrom"
date = datetime.datetime.today().strftime('%Y-%m-%d')
lib = args.lib
callNum = args.call
callDum=callNum.replace('.','-')
catKey = args.key
label = args.transcript
dir = args.dir
note=args.note

#######################
###### FUNCTIONS ######
#######################

# scan CD

def runScanner():
	scanner="epson2:libusb:001:003"
	tiff=str(outputPath+callDum+".tiff")
	go = input("Please place disk on scanner and hit Enter")
	subprocess.call('scanimage -d "epson2:libusb:001:003" --format=tiff --mode col --resolution 300 -x 150 -y 150 > '+tiff, shell=True)
	
def cropImage():
	print("cropping image...")
	os.system("pwd")
	tiff=str(outputPath+callDum+".tiff")
	os.system("ls "+tiff)
	print(str(tiff))
	croppedImage=str(outputPath+callDum+"_trim.jpg")
	
	output=subprocess.check_output('convert',tiff,'-virtual-pixel edge','-blur 0x15','-fuzz 15%','-trim','-format "%[fx:w]x%[fx:h]+%[fx:page.x]+%[fx:page.y]"', shell=True)

	subprocess.call("convert "+output+" -trim +repage "+croppedImage, shell=True)

###NOTE TO JESS: try running the internal command first and then capture the output and run the second subprocess on that command####

########################
#####  THE GOODS  ######
########################

### Change working directory
if not os.path.exists(dir):
	os.makedirs(dir)
	
os.chdir(dir)
os.system("pwd")

### Create directory for output if it doesn't exist
outputPath = lib+"/"+callDum+"/"

if os.path.exists(outputPath):
	replacePath = input("That disk output path already exists, proceed anyway y/n? ")
	if replacePath.lower() == 'y' or replacePath.lower() == 'yes':
		runScanner()
	if replacePath.lower() == 'n' or replacePath.lower() == 'no':
		sys.exit("-No disks updated. Exiting...")

if not os.path.exists(outputPath):
	os.makedirs(outputPath)



#runScanner()
cropImage()


