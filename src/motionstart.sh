#!/bin/bash 
sleep 10

#set -x	
killall motion
mkdir -p /var/run/motion

#chown -R iotuser /var/run/motion

rte=/opt/data/motion
arch="${rte}`date +%Y%m%d%H%M%S`"
for f in allowed denied removed ; do 
	mkdir -p "${rte}/$f"
	mkdir -p "${arch}/$f"
	echo mv -f "${rte}/${f}"/* "${arch}/${f}/"
	mv -f "${rte}/${f}"/* "${arch}/${f}/"
done
#chown -R iotuser ${rte}
#chown -R iotuser ${arch}

find /opt/data/motion* -empty -type f -exec rm -f {} \;
find /opt/data/motion/ -type f -mtime +2 -exec rm {} \;
find /opt/data/motion2* -type f -empty -exec rm -rf {} \;
find /opt/data/motion2* -type f -empty -exec rm -rf {} \;

#chown iotuser /dev/video0 
# fuser /dev/video0 || su - iotuser -c "cd /home/iotuser; motion"
cd /home/iotuser
fuser /dev/video0 || motion
