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


class FirefoxPageVisitFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a Firefox places.sqlite page visited."""
  DATA_TYPE = 'firefox:places:page_visited'

  # Transitions defined in the source file:
  #   src/toolkit/components/places/nsINavHistoryService.idl
  # Also contains further explanation into what each of these settings mean.
  _URL_TRANSITIONS = {
      1: 'LINK',
      2: 'TYPED',
      3: 'BOOKMARK',
      4: 'EMBED',
      5: 'REDIRECT_PERMANENT',
      6: 'REDIRECT_TEMPORARY',
      7: 'DOWNLOAD',
      8: 'FRAMED_LINK',
  }
  _URL_TRANSITIONS.setdefault('UNKOWN')

  # TODO: Make extra conditional formatting.
  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({title})',
      u'[count: {visit_count}]',
      u'Host: {host}',
      u'{extra_string}']

  FORMAT_STRING_SHORT_PIECES = [u'URL: {url}']

  def GetMessages(self, event_object):
    """Return the message strings."""
    transition = self._URL_TRANSITIONS.get(
        getattr(event_object, 'visit_type', 0), None)

    if transition:
      transition_str = 'Transition: {}'.format(transition)

    if hasattr(event_object, 'extra'):
      if transition:
        event_object.extra.append(transition_str)
      event_object.extra_string = u' '.join(event_object.extra)
    elif transition:
      event_object.extra_string = transition_str

    return super(FirefoxPageVisitFormatter, self).GetMessages(event_object)
