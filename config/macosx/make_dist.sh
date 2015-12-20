#!/bin/bash
#
# Script to make a plaso Mac OS X distribution package.

EXIT_SUCCESS=0;
EXIT_FAILURE=1;

MACOSX_VERSION=`sw_vers -productVersion | awk -F '.' '{print $1 "." $2}'`;
PLASO_VERSION=`grep -e '^__version' plaso/__init__.py | sed -e "s/^[^=]*= '\([^']*\)'/\1/g"`;
PKG_IDENTIFIER="com.github.log2timeline.plaso";
PKG_FILENAME="../python-plaso-${PLASO_VERSION}.pkg";
DEPSDIR="../l2tdevtools/build";
DISTDIR="plaso-${PLASO_VERSION}";

if test ! -d ${DEPSDIR};
then
  echo "Missing dependencies directory: ${DEPSDIR}.";

  exit ${EXIT_FAILURE};
fi

if test ! -d config;
then
  echo "Missing config directory.";

  exit ${EXIT_FAILURE};
fi

if test -z "$1";
then
  DIST_VERSION="${PLASO_VERSION}";
else
  DIST_VERSION="${PLASO_VERSION}-$1";
fi

DISTFILE="../plaso-${DIST_VERSION}-macosx-${MACOSX_VERSION}.dmg";

rm -rf build dist tmp ${DISTDIR} ${PKG_FILENAME} ${DISTFILE};

python setup.py install --root=$PWD/tmp --install-data=/usr/local 

mkdir -p tmp/usr/local/share/doc/plaso
cp AUTHORS ACKNOWLEDGEMENTS LICENSE tmp/usr/local/share/doc/plaso

for PY_FILE in tmp/usr/local/bin/*.py;
do
  SH_FILE=${PY_FILE/.py/.sh};
  cat > ${SH_FILE} << EOT
#!/bin/sh
PYTHONPATH=/Library/Python/2.7/site-packages/ \${0/.sh/.py};
EOT
  chmod a+x ${SH_FILE};
done

pkgbuild --root tmp --identifier ${PKG_IDENTIFIER} --version ${PLASO_VERSION} --ownership recommended ${PKG_FILENAME};

if test ! -f ${PKG_FILENAME};
then
  echo "Missing plaso package file: ${PKG_FILENAME}";

  exit ${EXIT_FAILURE};
fi

mkdir ${DISTDIR};

cp config/macosx/Readme.txt ${DISTDIR}/;

sed "s/@VOLUMENAME@/${DISTDIR}/" config/macosx/install.sh.in > ${DISTDIR}/install.sh;
chmod 755 ${DISTDIR}/install.sh;

mkdir ${DISTDIR}/packages;

IFS="
";

for DEPENDENCY_DMG in `ls -1 ${DEPSDIR}/*.dmg`;
do
  # TODO: skip hachoir packages.
  DEPENDENCY_PKG=`basename ${DEPENDENCY_DMG/.dmg/.pkg}`;
  hdiutil attach ${DEPENDENCY_DMG};
  cp -rf /Volumes/${DEPENDENCY_PKG}/${DEPENDENCY_PKG} ${DISTDIR}/packages;
  hdiutil detach /Volumes/${DEPENDENCY_PKG};

  # TODO: copy license files on a per-dependency basis.
done

cp -r config/licenses ${DISTDIR}/;
rm -f ${DISTDIR}/licenses/LICENSE.pywin32;

cp -rf ${PKG_FILENAME} ${DISTDIR}/packages;

hdiutil create ${DISTFILE} -srcfolder ${DISTDIR}/ -fs HFS+;

exit ${EXIT_SUCCESS};

