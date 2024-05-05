#!/usr/bin/env bash
#
# Script to run nsrlsvr on an Ubuntu Jenkins instance with Docker.

AUXILIARY_DATA_PATH="/media/auxiliary";

# Exit on error.
set -e

sudo apt-get install -y curl unzip

cd config/end_to_end;

mkdir -p data;

if [ -f "${AUXILIARY_DATA_PATH}/nsrlsvr/NSRLFile.txt" ];
then
	# Note that NSRLFile.txt is approximate 4 GiB in size.
	cp -f "${AUXILIARY_DATA_PATH}/nsrlsvr/NSRLFile.txt" data/
fi

if [ ! -f data/NSRLFile.txt ];
then
	if [ -f "${AUXILIARY_DATA_PATH}/nsrlsvr/rds_modernm.zip" ];
	then
		# Note that this is an older rds_modernm.zip that is approximate 2 GiB in size.
		cp -f "${AUXILIARY_DATA_PATH}/nsrlsvr/rds_modernm.zip" data/
	fi

	if [ ! -f data/rds_modernm.zip ];
	then
		# Download the minimum modern RDS hash set.
		# Note that rds_modernm.zip is approximate 18 GiB in size.
		curl -o data/rds_modernm.zip https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS/rds_2024.03.1/RDS_2024.03.1_modern_minimal.zip
	fi

	if [ ! -f data/rds_modernm.zip ];
	then
		echo "Missing: rds_modernm.zip";

		exit 1
	fi

	unzip -x data/rds_modernm.zip data/rds_modernm/NSRLFile.txt

	mv data/rds_modernm/NSRLFile.txt data/
fi

if [ ! -f data/NSRLFile.txt ];
then
	echo "Missing: NSRLFile.txt";

	exit 1
fi

docker build -f nsrlsvr.Dockerfile --force-rm --no-cache -t log2timeline/nsrlsvr . ;

# Update the nsrlsvr hashes.txt file from NSRLFile.txt
docker run -v "${PWD}/data:/data:z" log2timeline/nsrlsvr /bin/bash -c "/usr/bin/python3 /usr/bin/nsrlupdate /data/NSRLFile.txt";

# Preserver the intermediate container so we don't have to rebuild hashes.txt
docker commit `docker ps -lq` | cut -c8- > nsrlsvr.container

