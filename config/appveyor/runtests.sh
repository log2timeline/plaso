#!/bin/sh
# Script to run tests

# Set the following environment variables to build libyal with gettext.
export CFLAGS="-I/usr/local/include -I/usr/local/Cellar/gettext/0.21.1/include ${CFLAGS}";
export LDFLAGS="-L/usr/local/lib -L/usr/local/Cellar/gettext/0.21.1/lib ${LDFLAGS}";

# Set the following environment variables to build pycrypto and yara-python.
export CFLAGS="-I/usr/local/opt/openssl@1.1/include ${CFLAGS}";
export LDFLAGS="-L/usr/local/opt/openssl@1.1/lib ${LDFLAGS}";

# Set the following environment variables to ensure tox can find Python 3.11.
export PATH="/usr/local/opt/python@3.11/bin:${PATH}";

tox -e py311
