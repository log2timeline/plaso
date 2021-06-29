#!/usr/bin/env bash
#
# Script to install nsrlsvr on Ubuntu from the GIFT PPA.

AUXILIARY_DATA_PATH="/media/auxiliary";

# Exit on error.
set -e

# Install and configure nsrlsvr
sudo add-apt-repository ppa:gift/dev -y
sudo apt-get update -q
sudo apt-get install -y curl net-tools nsrlsvr-server unzip

sudo mkdir -p /var/share/nsrlsvr

if [ -f "${AUXILIARY_DATA_PATH}/nsrlsvr/hashes.txt" ];
then
	cp -f "${AUXILIARY_DATA_PATH}/nsrlsvr/hashes.txt" /var/share/nsrlsvr;
fi

# Have nsrlupdate generate /var/share/nsrlsvr/hashes.txt
if [ ! -f /var/share/nsrlsvr/hashes.txt ];
then
	if [ -f "${AUXILIARY_DATA_PATH}/nsrlsvr/NSRLFile.txt" ];
	then
		cp -f "${AUXILIARY_DATA_PATH}/nsrlsvr/NSRLFile.txt" .
	fi

	if [ ! -f NSRLFile.txt ];
	then
		if [ -f "${AUXILIARY_DATA_PATH}/nsrlsvr/rds_modernm.zip" ];
		then
			cp -f "${AUXILIARY_DATA_PATH}/nsrlsvr/rds_modernm.zip" .
		fi

		if [ ! -f rds_modernm.zip ];
		then
			# Download the minimum RDS hash set.
			# Note that rds_modernm.zip is approximate 2 GiB in size.
			curl -o rds_modernm.zip https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS/current/rds_modernm.zip
		fi
		# Note that NSRLFile.txt is approximate 4 GiB in size.
		unzip -x rds_modernm.zip rds_modernm/NSRLFile.txt
	fi
	# Build the nsrlsvr hashes.txt file
	sudo mkdir -p /usr/share/nsrlsvr
	sudo touch /usr/share/nsrlsvr/hashes.txt
	sudo /usr/bin/python3 /usr/bin/nsrlupdate rds_modernm/NSRLFile.txt
fi

# For the sake of verbosity have nsrlsvr test its set up first
time sudo /usr/bin/nsrlsvr --dry-run

# Run nsrlsvr listening on port 9120
sudo /usr/bin/nsrlsvr -p 9120

