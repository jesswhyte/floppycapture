#!/bin/bash

# clean up nimbie directory
# do not use if audio CDs

# clean up file names in directory

dir = $1
mkdir $dir/bincue

## get rid of all the white space in the names
for f in $(find $dir -name "*.BIN*" -o -name "*.CUE*" -o -name "*.bin*" -o -name "*.cue*"); do 
	dest="${f//[[:space:]]/.}" && mv -i "$f" "${dest//[^[:alnum:]._-]/}"
done

## if files hidden
#for f in $(find $dir -type f -name "\.*"); do 
#	fn=$(basename $f) && fm=${fn:1} && mv $fn $fm; 
#done

## move all the bin cues to bincue
for f in $(find $dir -name "*.BIN" -o -name "*.CUE" -o -name "*.bin" -o -name "*.cue"); do
	mv -v $f $dir/bincue/
done


# make iso's out of bincues
for f in $(find $dir/bincue/ -name "*.bin" -o -name "*.BIN"); do file=$(echo $f | cut -d "." -f2 | cut -d "/" -f2) && bchunk -v $file.bin $file.cue $dir/$file.iso; done







