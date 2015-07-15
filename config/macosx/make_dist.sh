#!/bin/bash
#
# Copyright 2014 The Plaso Project Authors.
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
#
# Script to make a plaso Mac OS X distribution package.

EXIT_SUCCESS=0;
EXIT_FAILURE=1;

if test ! -d dependencies;
then
  echo "Missing dependencies directory.";

  exit ${EXIT_FAILURE};
fi

if test ! -d config;
then
  echo "Missing config directory.";

  exit ${EXIT_FAILURE};
fi

MACOSX_VERSION=`sw_vers -productVersion | awk -F '.' '{print $1 "." $2}'`;
PLASO_VERSION=`grep -e '^__version' plaso/__init__.py | sed -e "s/^[^=]*= '\([^']*\)'/\1/g"`;
PKG_IDENTIFIER="com.github.log2timeline.plaso";
PKG_FILENAME="../python-plaso-${PLASO_VERSION}.pkg";
DISTDIR="plaso-${PLASO_VERSION}";

if test ! -z $1;
then
  PLASO_VERSION="${PLASO_VERSION}-$1";
fi

rm -rf build dist ${DISTDIR} ../${PKG_FILENAME} ../plaso-${PLASO_VERSION}_macosx-${MACOSX_VERSION}.dmg;

python setup.py bdist

mkdir -p dist/tmp
cd dist/tmp
tar xfvz ../*.tar.gz
cd ../..

mkdir -p dist/tmp/usr/share/doc/plaso
cp AUTHORS ACKNOWLEDGEMENTS LICENSE dist/tmp/usr/share/doc/plaso

pkgbuild --root dist/tmp --identifier ${PKG_IDENTIFIER} --version ${PLASO_VERSION} --ownership recommended ${PKG_FILENAME};

if test ! -f ${PKG_FILENAME};
then
  echo "Missing plaso package: ../python-plaso-${PLASO_VERSION}.pkg file.";

  exit ${EXIT_FAILURE};
fi

mkdir "${DISTDIR}";
cp -r config/licenses "${DISTDIR}";
cp config/macosx/Readme.txt "${DISTDIR}";

sed "s/@VOLUMENAME@/${DISTDIR}/" config/macosx/install.sh.in > "${DISTDIR}/install.sh";
chmod 755 "${DISTDIR}/install.sh";

mkdir "${DISTDIR}/packages";
cp dependencies/*.pkg "${DISTDIR}/packages";
cp ../python-plaso-${PLASO_VERSION}.pkg "${DISTDIR}/packages";

hdiutil create ../plaso-${PLASO_VERSION}_macosx-${MACOSX_VERSION}.dmg -srcfolder "${DISTDIR}/" -fs HFS+;

exit ${EXIT_SUCCESS};

