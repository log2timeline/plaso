# -*- coding: utf-8 -*-
"""A plugin to generate a list of domains visited."""

import urlparse

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

  _DATATYPES = [
      u'chrome:history:file_downloaded', u'chrome:history:page_visited',
      u'firefox:places:page_visited', u'firefox:downloads:download',
      u'macosx:lsquarantine', u'msiecf:redirected', u'msiecf:url',
      u'msie:webcache:container', u'opera:history', u'safari:history:visit']

  def __init__(self, incoming_queue):
    """Initializes the domains visited plugin.

    Args:
      incoming_queue: A queue to read events from.
    """
    super(UniqueDomainsVisitedPlugin, self).__init__(incoming_queue)
    self._domains = []

  def ExamineEvent(self, analysis_mediator, event_object, **kwargs):
    """Analyzes an event_object and extracts domains from it.

    We only evaluate straightforward web history events, not visits which can
    be inferred by TypedURLs, cookies or other means.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: The event object (instance of EventObject) to examine.
    """
    if event_object.data_type not in self._DATATYPES:
      return

    url = getattr(event_object, u'url', None)
    if url is None:
      return
    parsed_url = urlparse.urlparse(url)
    domain = getattr(parsed_url, u'netloc', None)
    if domain in self._domains:
      # We've already found an event containing this domain.
      return
    self._domains.append(domain)

  def CompileReport(self, analysis_mediator):
    """Compiles an analysis report.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    lines_of_text = [u'Listing domains visited by all users']
    for domain in sorted(self._domains):
      lines_of_text.append(domain)

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)
    return reports.AnalysisReport(self.NAME, text=report_text)


manager.AnalysisPluginManager.RegisterPlugin(UniqueDomainsVisitedPlugin)
