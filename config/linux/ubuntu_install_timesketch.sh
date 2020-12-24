#!/usr/bin/env bash
#
# Script to install Timesketch on Ubuntu from the GIFT PPA.

# Exit on error.
set -e

# Install and configure Elasticsearch 7
./config/linux/ubuntu_install_elasticsearch7.sh

# Install and configure PostgreSQL
sudo apt-get install -y postgresql python3-psycopg2

sudo sed '$a local   all             timesketch                              md5' -i /etc/postgresql/*/main/pg_hba.conf

sudo /etc/init.d/postgresql restart

sudo -u postgres createuser -d -R -S timesketch
sudo -u postgres psql -c "ALTER USER timesketch WITH PASSWORD 'tse2etest';"

sudo -u postgres createdb -O timesketch timesketch

# Install and configure Timesketch
sudo add-apt-repository universe
sudo apt-get update

sudo apt-get install -y python3-timesketch timesketch-data timesketch-server

sudo mkdir /etc/timesketch
sudo cp /usr/share/timesketch/timesketch.conf /etc/timesketch

# Note the user running psort will need access to timesketch.conf
sudo chmod 600 /etc/timesketch/timesketch.conf

SECRET_KEY=`openssl rand -base64 32`;
sudo sed "s?SECRET_KEY = .*?SECRET_KEY = '${SECRET_KEY}'?" -i /etc/timesketch/timesketch.conf

sudo sed "s?[<]USERNAME[>]:[<]PASSWORD[>]?timesketch:tse2etest?" -i /etc/timesketch/timesketch.conf

sudo service timesketch start
sudo systemctl enable timesketch

tsctl add_user -u test -p test
