# -*- coding: utf-8 -*-
"""This file contains the install history plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class InstallHistoryPlugin(interface.PlistPlugin):
  """Plist plugin that extracts the installation history."""

  NAME = 'plist_install_history'
  DESCRIPTION = u'Parser for installation history plist files.'

  PLIST_PATH = 'InstallHistory.plist'
  PLIST_KEYS = frozenset([
      'date', 'displayName', 'displayVersion',
      'processName', 'packageIdentifiers'])

  def GetEntries(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts relevant install history entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      top_level: Optional plist in dictionary form. The default is None.
    """
    for entry in top_level:
      packages = []
      for package in entry.get('packageIdentifiers'):
        packages.append(package)
      description = (
          u'Installation of [{0:s} {1:s}] using [{2:s}]. '
          u'Packages: {3:s}.').format(
              entry.get('displayName'), entry.get('displayVersion'),
              entry.get('processName'), u', '.join(packages))
      event_object = plist_event.PlistEvent(
          u'/item', u'', entry.get('date'), description)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(InstallHistoryPlugin)
