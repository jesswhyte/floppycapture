#!/usr/bin/env python3

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

parser = argparse.ArgumentParser(description="Script to walk through floppy disk capture workflow")
# listing required arguments
required_group = parser.add_argument_group('Required')
required_group.add_argument('-d', '--dir', type=str, help='Start directory, e.g. /mnt/data/LIB/', required=True)
required_group.add_argument('-m', '--mediatype', type=str, help='Use "3.5" or "5.25"', required=True, choices=['3.5', '5.25'])
required_group.add_argument('-l', '--lib', type=str, help='Library', required=True, choices=['ARCH', 'ART', 'ASTRO', 'CHEM', 'CRIM', 'DENT', 'OPIRG', 'EARTH', 'EAL', 'ECSL', 'FCML', 'FNH', 'GERSTEIN', 'INFORUM', 'INNIS', 'KNOX', 'LAW', 'MDL', 'MATH', 'MC', 'PONTIF', 'MUSIC', 'NEWCOLLEGE', 'NEWMAN', 'OISE', 'PJRC', 'PHYSICS', 'REGIS', 'RCL', 'UTL', 'ROM', 'MPI', 'STMIKES', 'TFRBL', 'TRIN', 'UC', 'UTARMS', 'UTM', 'UTSC', 'VIC'])
required_group.add_argument('-c', '--collection', type=str, help='use coll/accession ID when processing archival collections, for library projects, make a project ID or use ticket #')

# creating an argument group = Archival
archival_group = parser.add_argument_group('For archival content')
archival_group.add_argument('-A', '--archival', action='store_true', help='use -A archival flag for processing disks from archival collections or without call numbers. Requires the use of -c and -k')
archival_group.add_argument('-k', '--diskID', type=str, help='e.g. 0001, 0002, 0003. Required when using -A')

# listing optional arguments
parser.add_argument('-i', '--itype', type=str, help='use -i flag to indicate i type, e.g. i 4 = MFM, i 9 = Apple 400/800k, optional')
parser.add_argument('-b', '--barcode', type=str, help='barcode')
parser.add_argument('-M', '--MMSID', type=str, help='MMSID')
parser.add_argument('--multiple', action='store_true', help='use --multiple to indicate there are multiple discs for this object')
parser.add_argument('-t', '--transcript', type=str, help='Transcript of label, please put in single quotations and avoid commas', required=False)
parser.add_argument('-n', '--note', type=str, help='capture or processing notes', required=False)

## Array for all args passed to script
args = parser.parse_args()

# Check required arguments
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
note = args.note or ""
label = args.transcript or "no disk label"
yes_string = ["y", "yes", "Yes", "YES"]
no_string = ["n", "no", "No", "NO"]
diskID = ""
itype = args.itype

## Getting to a diskID
# then check if a barcode is provided:
print()
if args.barcode:
    output = subprocess.run(['bash', 'barcode-pull.sh', '-b', args.barcode, '-f'], stdout=subprocess.PIPE)
    print(f'Using barcode: {args.barcode}')
    output_json = json.loads(output.stdout.decode('utf-8'))
    diskID = output_json['holding_data']['permanent_call_number']
    print(f'callNumber = {diskID}')
elif args.MMSID:
    output = subprocess.run(['bash', 'mmsid-pull.sh', '-m', args.MMSID, '-f'], stdout=subprocess.PIPE)
    print(f'Using MMSID: {args.MMSID}')
    output_json = json.loads(output.stdout.decode('utf-8'))
    diskID = output_json['delivery']['bestlocation']['callNumber']
    print(f'callNumber = {diskID}')

# Clean up diskID
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

def kfStream():
    os.system(
        f"dtc -{drive} -fstreams/{diskID}/{diskID}_stream -i0 -i4 -i9 -i2 -t2 -l8 -p | tee {outputPath}{diskID}_capture.log")

# Takes an existing stream and attempts to make an image based on the given fileSystem
def kfImage(fileSystem):
    os.system(
        f"dtc -fstreams/{diskID}/{diskID}_stream00.0.raw -i0 -f{outputPath}{diskID}_disk.img -{fileSystem} -m1")

# Takes a preservation stream and attempts to create an i4 or MFM disk image
def kfi():
    os.system(
        f"dtc -{drive} -fstreams/{diskID}/{diskID}_stream -i0 -f{outputPath}{diskID}_disk.img -i{itype} -t1 -l8 -p | tee {outputPath}{diskID}_capture.log")


########################
#####  THE GOODS  ######
########################

# Check media type and set drive
drive = "d0" if mediaType == "3.5" else "d1"

# Check if output directory already exists
if os.path.exists(outputPath):
    replacePath = input(f"{bcolors.INPUT}Path already exists, proceed anyway? [y/n]{bcolors.ENDC}")
    if replacePath.lower() not in yes_string:
        sys.exit("-No entries updated and files created. Exiting...")

    replaceStream = input(f"{bcolors.INPUT}Replace stream/image **ONLY** (i.e. no photography)? [y/n]{bcolors.ENDC}")
    if replaceStream.lower() in yes_string:
        go = input(f"{bcolors.INPUT}Please insert disk and hit Enter{bcolors.ENDC}")
        if args.itype:
            kfi()
        else:
            kfStream()
            fileSystem = input(f"{bcolors.INPUT}Which filesystem? {bcolors.ENDC}")
            kfImage(fileSystem)
        sys.exit("-Stream/image replaced. No other entries updated. Exiting...")

    print(f"{bcolors.OKGREEN}Replacing {diskID} ...{bcolors.ENDC}")


### CAMERA - TAKE A PICTURE - VERY ENV SPECIFIC TO MY CAMERA
picName = diskID + ".jpg"
PicPath = outputPath + picName

# Force overwrite the image file and silence the output of the photo taking script by gphoto2 in the terminal.
picParameters = " --wait-event=1s --set-config eosremoterelease='Press 1' --wait-event=1s --set-config eosremoterelease='Press 2' --wait-event=100ms --set-config eosremoterelease='Release 2' --set-config eosremoterelease='Release 1' --wait-event-and-download=5s  --filename " + outputPath + picName + " --force-overwrite > /dev/null"

photoPrompt = input("Do you want to photograph the disk (Warning: requires device connected)? [y/n]")

if photoPrompt in yes_string:
    if os.path.exists(PicPath):
        replacePhotoPath = input(f"{bcolors.INPUT}Photo already exists, proceed anyway? [y/n]{bcolors.ENDC}")
        if replacePhotoPath in yes_string:
            go = input(f"{bcolors.INPUT}Please place disk for picture and hit Enter{bcolors.ENDC}")
            print("Wait please...taking picture...")
            os.system("gphoto2" + picParameters)  # gphoto2 command
            if os.path.exists(PicPath):
                print(f"-Pic: {PicPath} is captured")
        else:
            print("No photo is taken/modified")
    else:
        go = input(f"{bcolors.INPUT}Please place disk for picture and hit Enter{bcolors.ENDC}")
        print("Wait please...taking picture...")
        os.system("gphoto2" + picParameters)  # gphoto2 command
        if os.path.exists(PicPath):
            print(f"-Pic: {PicPath} is captured")
else:
    print("No photo is taken/modified")

# Double check pic worked and warn if it didn't
if not os.path.exists(PicPath):
    print(f"{bcolors.FAIL}-Pic: {PicPath} NOT TAKEN. CHECK CAMERA, CONTINUING{bcolors.ENDC}")

### KRYOFLUX - GET A PRESERVATION STREAM

# Pause and give user time to put disk in
go = input(f"{bcolors.INPUT}Please insert disk and hit Enter{bcolors.ENDC}")

# Take the stream only if it doesn't already exist
# Note: streams do not go in the diskID directory
streamPath = f"streams/{diskID}/{diskID}_stream00.0.raw"
if os.path.exists(streamPath):
    replaceStream = input(f"{bcolors.INPUT}{streamPath} exists, replace? [y/n]{bcolors.ENDC}")
    if replaceStream.lower() in yes_string:
        if args.itype:
            kfi()
        else:
            kfStream()
            fileSystem = input(f"{bcolors.INPUT}Which filesystem? {bcolors.ENDC}")
            kfImage(fileSystem)
    else:
        replaceMeta = input(f"{bcolors.INPUT}Replace metadata and create a new log entry? [y/n]{bcolors.ENDC}")
        if replaceMeta.lower() in no_string:
            metadata.close()
            sys.exit("-Exiting...")
else:
    if args.itype:
        # Take preservation stream and MFM image at the same time
        kfi()
    else:
        # Take preservation stream, then ask which filesystem (e.g., i9 or i4)
        kfStream()
        fileSystem = input(f"{bcolors.INPUT}Which filesystem? {bcolors.ENDC}")
        if not os.path.exists(outputPath + "_disk.img"):
            # Create image from stream based on the provided filesystem
            kfImage(fileSystem)

#########################################
#### END MATTER and METADATA UPDATES ####
#########################################

noteupdate = input(f"{bcolors.INPUT}If you would like to update the disk notes (currently: {bcolors.OKGREEN}{note}{bcolors.ENDC}{bcolors.INPUT}), please re-enter, otherwise hit Enter: {bcolors.ENDC}")
if noteupdate:
    note = noteupdate
    print(f"-Note has been updated to: {bcolors.OKGREEN}{note}{bcolors.ENDC}")
else:
    note = "No-notes"  # Changed to "No-notes" for better clarity
    print("-Note unchanged...")

# Open and update the masterlog - projectlog.csv
with open('projectlog.csv', 'a+') as log:
    print("-Updating log...")
    log.write(f"\n{collection},{diskID},{mediaType},\"{label}\",\"{str(note)}\"")
    log.write(",img=OK" if os.path.exists(outputPath + diskID + "_disk.img") else ",img=NO")
    log.write(f",{date}")

sys.exit("-Exiting...to extract logical files from your disk images and generate .csv manifests, please run disk-img-extraction.sh on the collection directory")
