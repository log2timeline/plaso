#!/bin/sh
# Script to run tests

# Set the following environment variables to build libyal with gettext.
export CPPFLAGS="-I/usr/local/include -I/usr/local/opt/gettext/include ${CPPFLAGS}";
export LDFLAGS="-L/usr/local/lib -L/usr/local/opt/gettext/lib ${LDFLAGS}";

# Set the following environment variables to build pycrypto and yara-python.
export CPPFLAGS="-I/usr/local/opt/openssl@1.1/include ${CPPFLAGS}";
export LDFLAGS="-L/usr/local/opt/openssl@1.1/lib ${LDFLAGS}";

# Set the following environment variables to ensure tox can find Python 3.11.
export PATH="/usr/local/opt/python@3.11/bin:${PATH}";

tox -e py311
