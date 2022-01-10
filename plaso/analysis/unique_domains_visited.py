# -*- coding: utf-8 -*-
"""A plugin to generate a list of domains visited."""

from urllib import parse as urlparse

from plaso.analysis import interface
from plaso.analysis import manager


class UniqueDomainsVisitedPlugin(interface.AnalysisPlugin):
  """A plugin to generate a list all domains visited.

  This plugin will extract domains from browser history events extracted by
  Plaso. The list produced can be used to quickly determine if there has been
  a visit to a site of interest, for example, a known phishing site.
  """

  NAME = 'unique_domains_visited'

  _SUPPORTED_EVENT_DATA_TYPES = frozenset([
      'chrome:history:file_downloaded',
      'chrome:history:page_visited',
      'firefox:downloads:download',
      'firefox:places:page_visited',
      'macosx:lsquarantine',
      'msiecf:redirected',
      'msiecf:url',
      'msie:webcache:container',
      'opera:history',
      'safari:history:visit'])

  # pylint: disable=unused-argument
  def ExamineEvent(
      self, analysis_mediator, event, event_data, event_data_stream):
    """Analyzes an event and extracts domains from it.

    We only evaluate straightforward web history events, not visits which can
    be inferred by TypedURLs, cookies or other means.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.
      event (EventObject): event to examine.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    if event_data.data_type not in self._SUPPORTED_EVENT_DATA_TYPES:
      return

    url = getattr(event_data, 'url', None)
    if url:
      parsed_url = urlparse.urlparse(url)
      domain = getattr(parsed_url, 'netloc', None)
      if domain:
        self._analysis_counter[domain] += 1


manager.AnalysisPluginManager.RegisterPlugin(UniqueDomainsVisitedPlugin)
