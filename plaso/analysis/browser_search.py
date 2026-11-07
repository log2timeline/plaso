"""A plugin that extracts browser history from events."""

import re

from urllib import parse as urlparse

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.containers import analysis_results


class BrowserSearchPlugin(interface.AnalysisPlugin):
    """Analyze browser search entries from events."""

    NAME = "browser_search"

    _EVENT_TAG_LABELS = ["browser_search"]

    _SUPPORTED_EVENT_DATA_TYPES = frozenset(
        [
            "chrome:autofill:entry",
            "chrome:cache:entry",
            "chrome:cookie:entry",
            "chrome:extension_activity:activity_log",
            "chrome:history:file_downloaded",
            "chrome:history:page_visited",
            "cookie:google:analytics:utma",
            "cookie:google:analytics:utmb",
            "cookie:google:analytics:utmt",
            "cookie:google:analytics:utmz",
            "firefox:cache:record",
            "firefox:cookie:entry",
            "firefox:downloads:download",
            "firefox:places:bookmark",
            "firefox:places:bookmark_annotation",
            "firefox:places:bookmark_folder",
            "firefox:places:page_visited",
            "msiecf:leak",
            "msiecf:redirected",
            "msiecf:url",
            "msie:webcache:container",
            "msie:webcache:containers",
            "msie:webcache:leak_file",
            "msie:webcache:partitions",
            "opera:history:entry",
            "opera:history:typed_entry",
            "safari:cookie:entry",
            "safari:history:visit",
            "safari:history:visit_sqlite",
        ]
    )

    # TODO: use groups to build a single RE.

    # Here we define filters, callback methods and callback method arguments
    # for all hits on each filter.
    _URL_FILTERS = frozenset(
        [
            (
                "Bing",
                re.compile(r"bing\.com/search"),
                "_ExtractSearchQueryStringValue",
                ("q",),
            ),
            (
                "DuckDuckGo",
                re.compile(r"duckduckgo\.com"),
                "_ExtractQueryStringValue",
                ("q",),
            ),
            (
                "GMail",
                re.compile(r"mail\.google\.com"),
                "_ExtractGMailSearchQuery",
                (),
            ),
            (
                "Google Docs",
                re.compile(r"docs\.google\.com"),
                "_ExtractQueryStringValue",
                ("q",),
            ),
            (
                "Google Drive",
                re.compile(r"drive\.google\.com/drive/search"),
                "_ExtractSearchQueryStringValue",
                ("q",),
            ),
            (
                "Google Search",
                # The segment between "google." and "/search" is the remainder
                # of the host (a TLD, optionally a port), so it is short. Bound
                # it rather than using an unbounded "[^/]*": the unbounded form
                # rescans the rest of a slash-free value from every "google."
                # token, making the examine time grow with the square of the
                # URL length on long values.
                re.compile(r"(www\.|encrypted\.|/)google\.[^/]{0,256}/search"),
                "_ExtractSearchQueryStringValue",
                ("q",),
            ),
            (
                "Google Sites",
                re.compile(r"sites\.google\.com/site"),
                "_ExtractSearchQueryStringValue",
                ("q",),
            ),
            (
                "Yahoo",
                re.compile(r"yahoo\.com/search"),
                "_ExtractKeyValue",
                ("p",),
            ),
            (
                "Yandex",
                re.compile(r"yandex\.com/search"),
                "_ExtractKeyValue",
                ("text",),
            ),
            (
                "Youtube",
                re.compile(r"youtube\.com"),
                "_ExtractSearchQueryStringValue",
                ("q",),
            ),
        ]
    )

    def _ExtractGMailSearchQuery(self, url):
        """Extracts a search query from a GMail search URL.

        GMail: https://mail.google.com/mail/u/0/#search/query[/?]

        Args:
          url (str): URL.

        Returns:
          str: search query or None if no query was found.
        """
        if "search/" not in url:
            return None

        _, _, line = url.partition("search/")
        line, _, _ = line.partition("/")
        line, _, _ = line.partition("?")

        return line.replace("+", " ")

    def _ExtractKeyValue(self, url, key):
        """Extracts a search query from the first key value pair in a URL.

        Unlike _ExtractQueryStringValue the key is searched for in the entire
        URL and only the value up to the first whitespace is used.

        Yahoo: https://search.yahoo.com/search?p=query
        Yahoo: https://search.yahoo.com/search;?p=query
        Yandex: https://www.yandex.com/search/?text=query

        Args:
          url (str): URL.
          key (str): key of the key value pair, such as "p".

        Returns:
          str: search query or None if no query was found.
        """
        _, _, value = url.partition(f"{key:s}=")
        value, _, _ = value.partition("&")
        if not value:
            return None

        value = value.split()[0]

        return value.replace("+", " ")

    def _ExtractQueryStringValue(self, url, key):
        """Extracts a search query from the query string of a URL.

        The value is that of the first occurrence of "key=" after the first "?"
        and runs up to the next "&".

        DuckDuckGo: https://duckduckgo.com/?q=query
        Google Docs: https://docs.google.com/.*/u/0/?q=query

        Args:
          url (str): URL.
          key (str): key of the key value pair, such as "q".

        Returns:
          str: search query or None if no query was found.
        """
        _, _, query_string = url.partition("?")
        _, _, value = query_string.partition(f"{key:s}=")
        value, _, _ = value.partition("&")
        if not value:
            return None

        return value.replace("+", " ")

    def _ExtractSearchQueryStringValue(self, url, key):
        """Extracts a search query from the query string of a search URL.

        This is the same as _ExtractQueryStringValue for URLs that contain
        "search".

        Bing: https://www.bing.com/search?q=query
        Google Drive: https://drive.google.com/drive/search?q=query
        Google Search: https://www.google.com/search?q=query
        Google Sites: https://sites.google.com/site/.*/system/app/pages/
                      search?q=query
        YouTube: https://www.youtube.com/search?q=query

        Args:
          url (str): URL.
          key (str): key of the key value pair, such as "q".

        Returns:
          str: search query or None if no query was found.
        """
        if "search" not in url:
            return None

        return self._ExtractQueryStringValue(url, key)

    def CompileReport(self, analysis_mediator):
        """Compiles an analysis report.

        Args:
          analysis_mediator (AnalysisMediator): mediates interactions between
              analysis plugins and other components, such as storage and dfVFS.

        Returns:
          AnalysisReport: analysis report.
        """
        for lookup_key, number_of_queries in self._analysis_counter.items():
            search_engine, _, search_term = lookup_key.partition(":")

            analysis_result = analysis_results.BrowserSearchAnalysisResult(
                number_of_queries=number_of_queries,
                search_engine=search_engine,
                search_term=search_term,
            )
            analysis_mediator.ProduceAnalysisResult(analysis_result)

        return super().CompileReport(analysis_mediator)

    def ExamineEvent(self, analysis_mediator, event, event_data, event_data_stream):
        """Analyzes an event.

        Args:
          analysis_mediator (AnalysisMediator): mediates interactions between
              analysis plugins and other components, such as storage and dfVFS.
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.
        """
        if event_data.data_type not in self._SUPPORTED_EVENT_DATA_TYPES:
            return

        url = getattr(event_data, "url", None)
        if not url:
            return

        for engine, url_expression, method_name, arguments in self._URL_FILTERS:
            callback_method = getattr(self, method_name, None)
            if not callback_method:
                logger.warning(
                    f"Missing callback method: {method_name:s} to parse search query"
                )
                continue

            match = url_expression.search(url)
            if not match:
                continue

            search_query = callback_method(url, *arguments)
            if not search_query:
                message = (
                    f"Unable to determine search query: {method_name:s} in URL: {url:s}"
                )
                analysis_mediator.ProduceAnalysisWarning(message, self.NAME)
                continue

            try:
                search_query = urlparse.unquote(search_query)
            except TypeError:
                search_query = None

            if not search_query:
                message = (
                    f"Unable to decode search query: {method_name:s} in URL: {url:s}"
                )
                analysis_mediator.ProduceAnalysisWarning(message, self.NAME)
                continue

            event_tag = self._CreateEventTag(event, self._EVENT_TAG_LABELS)
            analysis_mediator.ProduceEventTag(event_tag)

            lookup_key = ":".join([engine, search_query])
            self._analysis_counter[lookup_key] += 1


manager.AnalysisPluginManager.RegisterPlugin(BrowserSearchPlugin)
