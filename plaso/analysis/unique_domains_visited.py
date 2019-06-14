# -*- coding: utf-8 -*-
"""A plugin to generate a list of domains visited."""

from __future__ import unicode_literals

try:
  import urlparse
except ImportError:
  from urllib import parse as urlparse

# pylint: disable=wrong-import-position
from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports


class UniqueDomainsVisitedPlugin(interface.AnalysisPlugin):
  """A plugin to generate a list all domains visited.

  This plugin will extract domains from browser history events extracted by
  Plaso. The list produced can be used to quickly determine if there has been
  a visit to a site of interest, for example, a known phishing site.
  """

  NAME = 'unique_domains_visited'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

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

  def __init__(self):
    """Initializes the domains visited plugin."""
    super(UniqueDomainsVisitedPlugin, self).__init__()
    self._domains = []

  # pylint: disable=unused-argument
  def ExamineEvent(self, mediator, event, event_data):
    """Analyzes an event and extracts domains from it.

    We only evaluate straightforward web history events, not visits which can
    be inferred by TypedURLs, cookies or other means.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
      event_data (EventData): event data.
    """
    if event_data.data_type not in self._SUPPORTED_EVENT_DATA_TYPES:
      return

    url = getattr(event_data, 'url', None)
    if url is None:
      return

    parsed_url = urlparse.urlparse(url)
    domain = getattr(parsed_url, 'netloc', None)
    if domain in self._domains:
      # We've already found an event containing this domain.
      return

    self._domains.append(domain)

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: the analysis report.
    """
    lines_of_text = ['Listing domains visited by all users']
    for domain in sorted(self._domains):
      lines_of_text.append(domain)

    lines_of_text.append('')
    report_text = '\n'.join(lines_of_text)
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)


manager.AnalysisPluginManager.RegisterPlugin(UniqueDomainsVisitedPlugin)
