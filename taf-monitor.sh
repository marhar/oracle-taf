#!/bin/bash

DB=tmpltest

xfile=/tmp/taf-monitor-$$.sql
trap "rm -f $xfile" 0
echo > $xfile prompt connected successfully......
echo >> $xfile exit

while true; do
    tput home
    clr_eol=`tput el`
    (
    date
    for i in 1 2 3; do
        inst=$DB$i
        echo -n $inst: ' '
        sqlplus -L -S taftest/oracle@$inst @$xfile
    done
    ) | sed "s/\$/$clr_eol/"
    tput ed
    sleep 1
done
