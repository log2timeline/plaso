# -*- coding: utf-8 -*-
"""This file contains the Spotlight Volume Configuration plist in Plaso."""

from plaso.containers import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class SpotlightVolumePlugin(interface.PlistPlugin):
  """Basic plugin to extract the Spotlight Volume Configuration."""

  NAME = u'spotlight_volume'
  DESCRIPTION = u'Parser for Spotlight volume configuration plist files.'

  PLIST_PATH = u'VolumeConfiguration.plist'
  PLIST_KEYS = frozenset([u'Stores'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant VolumeConfiguration Spotlight entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
    """
    for volume_name, volume in match[u'Stores'].iteritems():
      description = u'Spotlight Volume {0:s} ({1:s}) activated.'.format(
          volume_name, volume[u'PartialPath'])
      event_object = plist_event.PlistEvent(
          u'/Stores', u'', volume[u'CreationDate'], description)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(SpotlightVolumePlugin)
