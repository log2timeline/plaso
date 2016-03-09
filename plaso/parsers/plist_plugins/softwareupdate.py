# -*- coding: utf-8 -*-
"""This file contains a default plist plugin in Plaso."""

from plaso.containers import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class SoftwareUpdatePlugin(interface.PlistPlugin):
  """Basic plugin to extract the Mac OS X update status.

  Further details about the extracted fields:
    LastFullSuccessfulDate:
      timestamp when Mac OS X was full update.
    LastSuccessfulDate:
      timestamp when Mac OS X was partially update.
  """

  NAME = u'maxos_software_update'
  DESCRIPTION = u'Parser for Mac OS X software update plist files.'

  PLIST_PATH = u'com.apple.SoftwareUpdate.plist'
  PLIST_KEYS = frozenset([
      u'LastFullSuccessfulDate', u'LastSuccessfulDate',
      u'LastAttemptSystemVersion', u'LastUpdatesAvailable',
      u'LastRecommendedUpdatesAvailable', u'RecommendedUpdates'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Mac OS X update entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
    """
    root = u'/'
    key = u''
    version = match.get(u'LastAttemptSystemVersion', u'N/A')
    pending = match.get(u'LastUpdatesAvailable', None)

    description = u'Last Mac OS X {0:s} full update.'.format(version)
    if u'LastFullSuccessfulDate' in match and match[u'LastFullSuccessfulDate']:
      event_object = plist_event.PlistEvent(
          root, key, match[u'LastFullSuccessfulDate'], description)
      parser_mediator.ProduceEvent(event_object)

    if pending and u'LastSuccessfulDate' in match:
      software = []
      for update in match.get(u'RecommendedUpdates', []):
        software.append(u'{0:s}({1:s})'.format(
            update.get(u'Identifier', u'<IDENTIFIER>'),
            update.get(u'Product Key', u'<PRODUCT_KEY>')))
      if not software:
        return

      description = (
          u'Last Mac OS {0!s} partially update, pending {1!s}: {2:s}.').format(
              version, pending, u','.join(software))
      event_object = plist_event.PlistEvent(
          root, key, match[u'LastSuccessfulDate'], description)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(SoftwareUpdatePlugin)
