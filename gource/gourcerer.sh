#!/bin/bash

#loop through directories and ...

touch combined1.txt
rm combined*
rm log*

c=1
for d in */ ; do
	#echo "Now updating git repo for $d..."
	#cd $d
	#git pull
	#cd ..

	filename="log$c.txt"
	echo "Gourcing log$c.txt from $d"
	gource --output-custom-log log$c.txt $d
	sed -i "s#|\/#|\/$d#g" log$c.txt

	if [ $c > 1 ] 
	then
		((e=$c+1))
		echo "$filename and combined$c.txt >> combined$e.txt"
		cat $filename combined$c.txt | sort -n > combined$e.txt
	else
		echo "$filename and combined1.txt >> combined2.txt"
		cat $filename combined1.txt | sort -n > combined2.txt
	fi
	echo
	((c=$c+1))
done

