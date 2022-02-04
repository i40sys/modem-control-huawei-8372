#!/bin/bash
set -euo pipefail
IFS=$'\n\t'


datas=$(lsusb | grep -i hua | awk '/Bus/ {print $6}' | tr ":" "\n")
counter=0
for line in $datas
do
        counter=$((counter+1))
        if [ $counter = 1 ]
                then
                        VENDOR=$(echo "$line")
        fi

        if [ $counter = 2 ]
                then
                       PRODUCT=$(echo "$line")
        fi
done


for DIR in $(find /sys/bus/usb/devices/ -maxdepth 1 -type l); do
  if [[ -f $DIR/idVendor && -f $DIR/idProduct &&
        $(cat $DIR/idVendor) == $VENDOR && $(cat $DIR/idProduct) == $PRODUCT ]]; then
    echo found $DIR
    echo 0 > $DIR/authorized
    sleep 1.5
    echo 1 > $DIR/authorized
  fi
done