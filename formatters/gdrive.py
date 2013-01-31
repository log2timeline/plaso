#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright David Nides (davnads.blogspot.com). All Rights Reserved.
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

"""This file contains a formatter for the Google Drive snaphots."""
from plaso.lib import eventdata


class GDriveCloudEntryFormatter(eventdata.EventFormatter):
  """Formatter for Google Drive snapshot cloud entry."""
  DATA_TYPE = 'gdrive:snapshot:cloud_entry'

  FORMAT_STRING = (u'File Path: {path} [{shared}] Size:{size} URL:{url} '
                   u'doc_type:{doc_type}')
  FORMAT_STRING_SHORT = u'{path}'


class GDriveLocalEntryFormatter(eventdata.EventFormatter):
  """Formatter for Google Drive snapshot local entry."""
  DATA_TYPE = 'gdrive:snapshot:local_entry'

  FORMAT_STRING = u'File Path: {path} Size: {size}'
  FORMAT_STRING_SHORT = u'{path}'
