#!/bin/bash
# Script to update the version information.

VERSION=`grep -e "^__version__ = '" plaso/__init__.py | sed "s/^__version__ = '\([^']*\)'/\1/"`;
DATE_VERSION=`date +"%Y%m%d"`;
# The following date operation mimics 'date -R' since it is not available on Mac OS X.
DATE_DPKG=`date "+%a, %d %b %Y %H:%M:%S %z"`
EMAIL_DPKG="Log2Timeline <log2timeline-dev@googlegroups.com>";

sed -i -e "s/^VERSION_DATE.*$/VERSION_DATE = '${DATE_VERSION}'/g" plaso/__init__.py
sed -i -e "s/^\(python-plaso \)([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*-1)/\1(${VERSION}-1)/" config/dpkg/changelog
sed -i -e "s/^\( -- ${EMAIL_DPKG}  \).*$/\1${DATE_DPKG}/" config/dpkg/changelog
