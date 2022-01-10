#!/usr/bin/env bash
#
# Script to install OpenSearch on Ubuntu

# Exit on error.
set -e

OPENSEARCH_VERSION="1.2.2";

sudo apt-get update
sudo apt-get install -y wget

# TODO: update /etc/sysctl.conf
# vm.max_map_count=262144

adduser opensearch

# Download OpenSearch

wget -q https://artifacts.opensearch.org/releases/bundle/opensearch/${OPENSEARCH_VERSION}/opensearch-${OPENSEARCH_VERSION}-linux-x64.tar.gz

# Install OpenSearch

tar xfv ${PWD}/opensearch-${OPENSEARCH_VERSION}-linux-x64.tar.gz

# Install the OpenSearch Python bindings

sudo apt-get install -y python3-opensearch

# Start OpenSearch

cd opensearch-${OPENSEARCH_VERSION}

echo "Starting OpenSearch";

su -c './opensearch-tar-install.sh -Eplugins.security.disabled=true' opensearch &
