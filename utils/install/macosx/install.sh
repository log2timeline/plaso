#!/bin/bash
# A small script that submits a code for code review.
#
# Copyright 2012 Google Inc. All Rights Reserved.
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

echo "Installing tools."
install_tool log2timeline
install_tool plaso_information
install_tool plaso_console
install_tool psort

echo "Installing missing dylibs."
sudo mv libregf.1.dylib /usr/lib/
sudo mv liblnk.1.dylib /usr/lib/
sudo mv libevt.1.dylib /usr/lib/
sudo mv libevtx.1.dylib /usr/lib/
sudo mv libmsiecf.1.dylib /usr/lib/
sudo mv libvshadow.1.dylib /usr/lib/
