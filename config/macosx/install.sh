#!/bin/bash
# Script that installs the binary version of plaso on Mac OS X.
#
# Copyright 2012 The Plaso Project Authors.
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

FOLDER=/usr/local/share/plaso
LNK_PATH=/usr/bin

link()
{
  if [ -h "$LNK_PATH/$1" ]
  then
    sudo rm "$LNK_PATH/$1"
  fi

  sudo ln -s "$FOLDER/$1/$1" "$LNK_PATH/$1"
}

folder()
{
  if [ -d "$FOLDER/$1" ]
  then
    sudo /bin/rm -rf "$FOLDER/$1"
  fi

  sudo cp -r "$1/" "$FOLDER/$1/"
}

uninstall_tool()
{
  echo -n "Uninstalling $1..."
  if [ -d "$FOLDER/$1" ]
  then
    sudo /bin/rm -rf "$FOLDER/$1"
  fi

  if [ -h "$LNK_PATH/$1" ]
  then
    sudo rm "$LNK_PATH/$1"
  fi
}

install_tool()
{
  echo -n "Installing $1..."
  folder "$1"
  link "$1"
  echo " [DONE]"
}

if [ ! -d "$FOLDER" ]
then
  sudo mkdir -p $FOLDER
fi

echo "Uninstalling previous versions."
uninstall_tool plaso_console
uninstall_tool plaso_information

echo "Installing tools."
install_tool log2timeline
install_tool pinfo
install_tool pprof
install_tool preg
install_tool pshell
install_tool psort

echo "Installing missing dylibs."
sudo mv libevt.1.dylib /usr/lib/
sudo mv libevtx.1.dylib /usr/lib/
sudo mv libmsiecf.1.dylib /usr/lib/
sudo mv liblnk.1.dylib /usr/lib/
sudo mv libregf.1.dylib /usr/lib/
sudo mv libvshadow.1.dylib /usr/lib/
