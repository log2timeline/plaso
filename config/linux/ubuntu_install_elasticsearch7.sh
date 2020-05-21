#!/usr/bin/env bash
#
# Script to install Elasticsearch 7 on Ubuntu

# Exit on error.
set -e

sudo apt-get update
sudo apt-get install -y apt-transport-https

# Add the Elasticseach repository key
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -

# Add the Elasticseach repository
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list

sudo apt-get update

# Install Elasticsearch 7
sudo apt-get install -y elasticsearch

sudo service elasticsearch start
sudo systemctl enable elasticsearch

# Install the Elasticsearch 7 Python bindings
sudo apt-get install -y python3-elasticsearch
