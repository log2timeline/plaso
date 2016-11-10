# -*- coding: utf-8 -*-
"""A plugin to generate a list of domains visited."""

import sys

if sys.version_info[0] < 3:
  import urlparse
else:
  from urllib import parse as urlparse  # pylint: disable=no-name-in-module

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports


class UniqueDomainsVisitedPlugin(interface.AnalysisPlugin):
  """A plugin to generate a list all domains visited.

  This plugin will extract domains from browser history events extracted by
  Plaso. The list produced can be used to quickly determine if there has been
  a visit to a site of interest, for example, a known phishing site.
  """

  NAME = u'unique_domains_visited'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  _DATATYPES = frozenset([
      u'chrome:history:file_downloaded', u'chrome:history:page_visited',
      u'firefox:places:page_visited', u'firefox:downloads:download',
      u'macosx:lsquarantine', u'msiecf:redirected', u'msiecf:url',
      u'msie:webcache:container', u'opera:history', u'safari:history:visit'])

  def __init__(self):
    """Initializes the domains visited plugin."""
    super(UniqueDomainsVisitedPlugin, self).__init__()
    self._domains = []

  def ExamineEvent(self, mediator, event):
    """Analyzes an event and extracts domains from it.

    We only evaluate straightforward web history events, not visits which can
    be inferred by TypedURLs, cookies or other means.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
    """
    if event.data_type not in self._DATATYPES:
      return

    url = getattr(event, u'url', None)
    if url is None:
      return
    parsed_url = urlparse.urlparse(url)
    domain = getattr(parsed_url, u'netloc', None)
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
      The analysis report (instance of AnalysisReport).
    """
    lines_of_text = [u'Listing domains visited by all users']
    for domain in sorted(self._domains):
      lines_of_text.append(domain)

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)


manager.AnalysisPluginManager.RegisterPlugin(UniqueDomainsVisitedPlugin)
