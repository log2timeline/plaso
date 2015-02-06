#!/bin/bash
# A small helper script to update the version information.
#
# Copyright 2015 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

VERSION=`grep -e "^__version__ = '" plaso/__init__.py | sed "s/^__version__ = '\([^']*\)'/\1/"`;
DATE_VERSION=`date +"%Y%m%d"`;
DATE_DPKG=`date -R`;
EMAIL_DPKG="Log2Timeline <log2timeline-dev@googlegroups.com>";

sed -i -e "s/^VERSION_DATE.*$/VERSION_DATE = '${DATE_VERSION}'/g" plaso/__init__.py
sed -i -e "s/^\(python-plaso \)([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*-1)/\1(${VERSION}-1)/" config/dpkg/changelog
sed -i -e "s/^\( -- ${EMAIL_DPKG}  \).*$/\1${DATE_DPKG}/" config/dpkg/changelog
