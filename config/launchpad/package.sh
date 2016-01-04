#!/bin/bash
# Script to package and upload plaso for release on launchpad.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

# DISTROS="precise trusty vivid wily";
DISTROS="precise trusty";
DPKG_VERSION="1";
DEVELOPMENT_RELEASE=1;

# These are example values.
# export NAME="Log2Timeline";
# export EMAIL="log2timeline-dev@googlegroups.com";

if test -z "${NAME}";
then
  echo "Environment variable: NAME not set.";

  exit ${EXIT_FAILURE};
fi

if test -z "${EMAIL}";
then
  echo "Environment variable: EMAIL not set.";

  exit ${EXIT_FAILURE};
fi

if ! test -f "${HOME}/.dput.cf";
then
  echo "Missing dput configuration file.";

  exit ${EXIT_FAILURE};
fi

# Remove previous packaged versions.
rm -f ../python-plaso_*;

# Trash any local changes.
git add -A . && git stash && git stash drop;

# Pull in the latest changes.
git pull;

# Apply work-around for launchpad Unicode issue.
mv test_data/ímynd.dd test_data/image.dd;

IFS="
";

for FILE in `grep -r ímynd.dd | sed 's/:.*$//'`;
do
  sed 's/ímynd.dd/image.dd/g' -i $FILE;
done

VERSION=`grep "__version__ = '" plaso/__init__.py | sed "s/__version__ = '\([0-9.]*\)'/\1/"`;
DATE_VERSION=`grep "VERSION_DATE = '" plaso/__init__.py | sed "s/VERSION_DATE = '\([0-9]*\)'/\1/"`;

IFS=" ";
for DISTRO in ${DISTROS};
do
  rm -rf debian && mkdir debian && cp -r config/dpkg/* debian

  if test ${DEVELOPMENT_RELEASE} -eq 0;
  then
    PACKAGE_VERSION="${VERSION}-${DPKG_VERSION}ppa1~${DISTRO}";
  else
    PACKAGE_VERSION="${VERSION}-dev-${DATE_VERSION}-${DPKG_VERSION}ppa1~${DISTRO}";
  fi

  dch -b -v ${PACKAGE_VERSION} --distribution ${DISTRO} --urgency low "Modifications for PPA release.";

  debuild -S -sa;

  dput ppa:gift/testing ../python-plaso_${PACKAGE_VERSION}_source.changes;
done

exit ${EXIT_SUCCESS};
