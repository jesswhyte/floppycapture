#!/bin/bash

function show_help() {
	echo
	echo -e "USAGE: ./cdcapture.sh -d /CAPTURED-DIR/ -l LIBRARY -c CALLNUM \n"
	echo -e "-l : The library the collection is from."
	echo -e "-d : The directory you want to write to, e.g. /home/bcdadmin/CAPTURED/"
	echo -e "-c : The call number of the item"
 	echo -e "Example:\n./cdcapture.sh -l ECSL -d /home/bcadmin/CAPTURED -c qa76.73.j38.r54.2002x"  
}


OPTIND=1
dir=""
lib=""
callnum=""
calldum=""
drive="/dev/cdrom"


function array_contains() {
  local array="$1[@]"
  local seeking=$2
  local in=1
  for element in "${!array}"; do
    if [[ $element == $seeking ]]; then
      in=0
      break
    fi
  done
  return $in
}

function scandisk {
	### SCAN ####
	tiff="$dir$lib/$calldum/$calldum-original.tiff"
	cropped="$dir$lib/$calldum/$calldum.tiff"
	if [ -e $cropped ]; then
		echo $cropped "exists"
		ls $cropped
	fi
	read -p "Do you want to scan this disk? [y/n] " response
	if [[ "$response" =~ ^([Yy])+$ ]]; then
		echo "about to scan: $tiff"
		scanner="epson2:libusb:001:002"
		read -p "Please put disk on scanner and hit any key when ready"
		scanimage -d "$scanner" --format=tiff --mode col --resolution 300 -x 150 -y 150 >> $tiff
		echo "disk tiff scan complete"
		convert $tiff -crop `convert $tiff -virtual-pixel edge -blur 0x15 -fuzz 15% -trim -format '%[fx:w]x%[fx:h]+%[fx:page.x]+%[fx:page.y]' info:` +repage $cropped
		echo "image cropped"
	fi
}

# Parse arguments
while getopts "h?d:l:c:" opt; do
    case "$opt" in
    h|\?)
        show_help
        ;;
    d)  dir=$OPTARG
        ;;
    c)  callnum=$OPTARG
        ;;
    l)  lib=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))

[ "$1" = "--" ] && shift

garbage="$@"

# Check all required parameters are present
if [ -z "$lib" ]; then
  echo "Library (-l) is required!"
elif [ -z "$dir" ]; then
  echo "directory (-d) is required!"
elif [ -z "$callnum" ]; then
  echo "callnumber (-c) is required!"
elif [ "$garbage" ]; then
  echo "$garbage is garbage."
fi

# Sanity checking
LIBS=(ARCH ART ASTRO CHEM CRIM DENT OPIRG EARTH EAL ECSL FCML FNH GERSTEIN INFORUM INNIS KNOX LAW MDL MATH MC PONTIF MUSIC NEWCOLLEGE NEWMAN OISE PJRC PHYSICS REGIS RCL UTL ROM MPI STMIKES TFRBL TRIN UC UTARMS UTM UTSC VIC)
array_contains LIBS "$lib" && lv=1 || lv=0
if [ $lv -eq 0 ]; then
  echo "$lib is not a valid library name."
  echo -e "Valid libraries:\n${LIBS[*]}"
fi

### Work out callnum ###
calldum1=${callnum^^}
calldum=${calldum1//./-}
echo "using callNum: $calldum"

### CAPTURE DIRECTORY ####

mkdir -p $dir$lib/$calldum


### SCAN ####
scandisk

##capture disk

#eject

read -p "Please insert disk into drive, close and hit any key once drive is ready"

## Display ISO Info
echo "---------------------CD INFO-----------------------"
isoinfo -d -i /dev/cdrom
echo "----------------------------------------------------"

## Get Block size of CD
blocksize=`isoinfo -d -i /dev/cdrom | grep "^Logical block size is:" | cut -d " " -f 5`
if test "$blocksize" = ""; then
        echo catdevice FATAL ERROR: Blank blocksize >&2
        exit
fi

## Get Block count of CD
blockcount=`isoinfo -d -i /dev/cdrom | grep "^Volume size is:" | cut -d " " -f 4`
if test "$blockcount" = ""; then
        echo catdevice FATAL ERROR: Blank blockcount >&2
        exit
fi

echo ""
echo "blocksize is: "$blocksize
echo "blockcount is: "$blockcount
echo ""

dd if=/dev/cdrom of=$dir$lib/$calldum/$calldum.iso bs=$blocksize count=$blockcount status=progress

echo "Checking md5sum of CD..."
md5cd=$(dd if=/dev/cdrom bs=$blocksize count=$blockcount | md5sum | cut -d " " -f1)
echo "CD MD5 is: "$md5cd

echo "Checking md5sum of ISO..."
md5iso=$(cat $dir$lib/$calldum/$calldum.iso | md5sum | cut -d " " -f1)
echo "ISO MD5 is: "$md5iso

if [ "$md5cd" == "$md5iso" ]; then
	echo "checksums MATCH"
	echo "CD MD5: "$md5cd >> $dir$lib/$calldum/$calldum-md5.txt
	echo "ISO MD5: "$md5iso >> $dir$lib/$calldum/$calldum-md5.txt
	
else
	echo "checksums DO NOT MATCH, writing md5fail.txt"
	echo "CD MD5: "$md5cd >> $dir$lib/$calldum/$calldum-md5fail.txt
	echo "ISO MD5: "$md5iso >> $dir$lib/$calldum/$calldum-md5fail.txt
fi

#eject














	






