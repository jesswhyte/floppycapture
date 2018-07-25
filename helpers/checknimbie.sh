#!/bin/bash -i

function show_help() {
	echo
	echo -e "USAGE: ./cdcapture.sh -d /CAPTURED-DIR/ -l LIBRARY -c CALLNUM \n"
	echo -e "-l : The library the collection is from."
	echo -e "-d : The directory you want to write to, e.g. /home/bcdadmin/CAPTURED/"
	echo -s "-s : The source directory for iso files"
	#echo -e "-c : The call number of the item"
 	echo -e "Example:\n./checknimbie.sh -l ECSL -d /home/bcadmin/CAPTURED -c qa76.73.j38.r54.2002x"  
}


OPTIND=1
dir=""
lib=""
source=""
callnum=""
calldum=""
answer="y"
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
		eject
		read -p "Please put disk on scanner and hit any key when ready"
		read -p "Ready?" 
		scanimage -d "$scanner" --format=tiff --mode col --resolution 300 -x 150 -y 150 >> $tiff
		echo "disk tiff scan complete"
		convert $tiff -crop `convert $tiff -virtual-pixel edge -blur 0x15 -fuzz 15% -trim -format '%[fx:w]x%[fx:h]+%[fx:page.x]+%[fx:page.y]' info:` +repage $cropped
		echo "image cropped"
	fi
}

function checkmd5 {
	echo "Checking md5sum of ISO..." $iso
	md5iso=$(md5 $iso | md5sum | cut -d " " -f1)
	echo "ISO MD5 is: "$md5iso
	echo "Checking md5sum of CD..."
	md5cd=$(dd if=/dev/cdrom bs=$blocksize count=$blockcount | md5sum | cut -d " " -f1)
	echo "CD MD5 is: "$md5cd
	if [ "$md5cd" == "$md5iso" ]; then
		echo "Checksums MATCH...moving file"
		mkdir -p $dir$lib/$calldum
		mv -v $iso $dir$lib/$calldum/$calldum.iso	
	else 
		echo "Checksums DO NOT MATCH"
		echo "you will need to manually create"
	fi
}	


# Parse arguments
while getopts "h?d:l:s:" opt; do
    case "$opt" in
    h|\?)
        show_help
        ;;
    d)  dir=$OPTARG
        ;;
   # c)  callnum=$OPTARG
    #    ;;
    l)  lib=$OPTARG
        ;;
    s)  source=$OPTARG
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
#elif [ -z "$callnum" ]; then
#  echo "callnumber (-c) is required!"
elif [ -z "$source" ]; then
  echo "source (-s) is required!"
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

### 


### GET VOLUME NAMES OF NIMBIE ISO FILES ###
rm volumeIDs-temp.txt

for iso in $(find $source -name "*.iso" -o -name "*.ISO" -type f); do
	#echo "checking: "$iso
	#isoinfo -d -i $iso
	isoID=$(isoinfo -d -i $iso | grep "^Volume id:" | cut -d " " -f 3)
	isoBC=$(isoinfo -d -i $iso | grep "^Volume size is:" | cut -d " " -f 4)
	echo $iso,$isoID,$isoBC >> volumeIDs-temp.txt
done	
	

while read -s -p "Do you wish to check a disk y/n? " ANSWER && [ "$ANSWER" = "y" ] ; do

	##capture disk

	### Work out callnum ###
	echo ""
	echo -n "Enter call number: "
	read callnum
	calldum1=${callnum^^}
	calldum=${calldum1//./-}
	echo "using callNum: $calldum"
	
	### Insert Disk ###	
	#eject

	read -p "Please insert disk into drive"
	read -p "Please hit Enter once disc is LOADED"
	
	# get CD INFO
	cdinfo=$(isoinfo -d -i /dev/cdrom)
	volumeCD=$(echo "$cdinfo" | grep "^Volume id:" | cut -d " " -f 3)
	#get blockcount/volume size of CD
	blockcount=$(echo "$cdinfo" | grep "^Volume size is:" | cut -d " " -f 4)
	if test "$blockcount" = ""; then
        	echo catdevice FATAL ERROR: Blank blockcount >&2
        	exit
	fi
	

	#get blocksize of CD
	blocksize=$(echo "$cdinfo" | grep "^Logical block size is:" | cut -d " " -f 5)
	if test "$blocksize" = ""; then
       		echo catdevice FATAL ERROR: Blank blocksize >&2
        	exit
	fi

	#echo back of CD INFO
	echo ""
	echo "Volume label for CD is: "$volumeCD
	echo "Volume size for CD is: "$blockcount
	echo ""


	#Check against ISO
	echo "Checking List of ISO's..."
	count=$(grep -c $volumeCD volumeIDs-temp.txt)
	if (( $count == 0 )) ; then
		echo "no results found..check manually"
		read -p "Enter ISO location if known (enter n if not known): " response
		if [[ "$response" != "n" ]]; then
			"$response" = $iso
			read -p "Check md5 checksums [y/n]: " md5response
			if [[ "$md5response" != "y" ]]; then
				mkdir -p $dir$lib/$calldum
				mv -iv $response $dir$lib/$calldum/$calldum.iso
			else			
				checkmd5
			fi
		fi
		
	elif (( $count > 1 )) ; then #tip: use (()) when comparing #'s
		echo "more than one result found..."	
		grep $volumeCD volumeIDs-temp.txt
		echo "checking size..."
		bcount=$(grep -c $blockcount volumeIDs-temp.txt)
		if (( $bcount > 1 )) ; then 
			echo "more than one size result found.."
			echo "you will need to manually check and create iso"
			read -p "Enter ISO location if known (enter n if not known): " response
			if [[ "$response" != "n" ]]; then
				"$response" = $iso
				read -p "Check md5 checksums [y/n]: " md5response
				if [[ "$md5response" != "y" ]]; then
					mkdir -p $dir$lib/$calldum
					mv -iv $response $dir$lib/$calldum/$calldum.iso
				else			
					checkmd5
				fi
			fi
			
		else
			grep $blockcount volumeIDs-temp.txt | while read -r line;  do
				isosize=$(echo $line | cut -d "," -f 3)
				echo "ISO Size is :"$isosize
				iso=$(echo $line | cut -d "," -f 1)
				echo "ISO is: "$iso
				read -p "Check md5 checksums [y/n]: " md5response
				if [[ "$md5response" != "y" ]]; then
					mkdir -p $dir$lib/$calldum
					mv -iv $iso $dir$lib/$calldum/$calldum.iso
				else			
					checkmd5
				fi
				
			done		
		fi		
			
	else
		grep $volumeCD volumeIDs-temp.txt | while read -r line; do
			iso=$(echo $line | cut -d "," -f 1)
			echo "MATCH FOUND: "$line
			echo "Copying ISO to new location..."
			if [ -e $dir$lib/$calldum/$calldum.iso ]; then
				echo "ISO already exists"
				echo "not moving"
			else	
				mkdir -p $dir$lib/$calldum
				mv -iv $iso $dir$lib/$calldum/$calldum.iso
			fi			
			
		done	
	fi
	scandisk

done

