# -*- coding: utf-8 -*-
"""This file contains the install history plist plugin in Plaso."""

from plaso.containers import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class InstallHistoryPlugin(interface.PlistPlugin):
  """Plist plugin that extracts the installation history."""

  NAME = u'macosx_install_history'
  DESCRIPTION = u'Parser for installation history plist files.'

  PLIST_PATH = u'InstallHistory.plist'
  PLIST_KEYS = frozenset([
      u'date', u'displayName', u'displayVersion', u'processName',
      u'packageIdentifiers'])

  def GetEntries(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts relevant install history entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      top_level: Optional plist in dictionary form.
    """
    for entry in top_level:
      packages = []
      for package in entry.get(u'packageIdentifiers', []):
        packages.append(package)

      if not packages or not u'date' in entry:
        continue

      description = (
          u'Installation of [{0:s} {1:s}] using [{2:s}]. '
          u'Packages: {3:s}.').format(
              entry.get(u'displayName', u'<UNKNOWN>'),
              entry.get(u'displayVersion', u'<DISPLAY_VERSION>'),
              entry.get(u'processName', u'<PROCESS_NAME>'),
              u', '.join(packages))
      event_object = plist_event.PlistEvent(
          u'/item', u'', entry.get(u'date'), description)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(InstallHistoryPlugin)
