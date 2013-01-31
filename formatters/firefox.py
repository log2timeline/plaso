#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a formatter for the Mozilla Firefox history."""
from plaso.lib import eventdata


class FirefoxBookmarkAnnotationFormatter(eventdata.EventFormatter):
  """Formatter for a Firefox places.sqlite bookmark annotation."""
  DATA_TYPE = 'firefox:places:bookmark_annotation'

  FORMAT_STRING = (u'Bookmark Annotation: [{content}] to bookmark [{title}] '
                   u'({url})')
  FORMAT_STRING_SHORT = u'Bookmark Annotation: {title}'


class FirefoxBookmarkFolderFormatter(eventdata.EventFormatter):
  """Formatter for a Firefox places.sqlite bookmark folder."""
  DATA_TYPE = 'firefox:places:bookmark_folder'

  FORMAT_STRING = '{title}'


class FirefoxBookmarkFormatter(eventdata.EventFormatter):
  """Formatter for a Firefox places.sqlite URL bookmark."""
  DATA_TYPE = 'firefox:places:bookmark'

  FORMAT_STRING = (u'Bookmark {type} {title} ({url}) '
                   u'[{places_title}] visit count {visit_count}')
  FORMAT_STRING_SHORT = u'Bookmarked {title} ({url})'


class FirefoxPageVisitFormatter(eventdata.EventFormatter):
  """Formatter for a Firefox places.sqlite page visited."""
  DATA_TYPE = 'firefox:places:page_visited'

  # TODO: make extra conditional formatting.
  FORMAT_STRING = (u'{url} ({title}) [count: {visit_count}] '
                   u'Host: {hostname}{extra}')
  FORMAT_STRING_SHORT = u'URL: {url}'
