# -*- coding: utf-8 -*-
"""This file contains the interface for analysis plugins."""

import abc
import collections
import time

import requests

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.containers import events
from plaso.lib import errors


class HashAnalysis(object):
  """Analysis information about a hash.

  Attributes:
    hash_information (object): object containing information about the hash.
    subject_hash (str): hash that was analyzed.
  """

  def __init__(self, subject_hash, hash_information):
    """Initializes analysis information about a hash.

    Args:
      subject_hash (str): hash that the hash_information relates to.
      hash_information (object): information about the hash. This object will be
          used by the GenerateLabels method in the HashTaggingAnalysisPlugin
          to tag events that relate to the hash.
    """
    self.hash_information = hash_information
    self.subject_hash = subject_hash


class HashTaggingAnalysisPlugin(interface.AnalysisPlugin):
  """An interface for plugins that tag events based on the source file hash."""

  # The event data types the plugin will collect hashes from. Subclasses
  # must override this attribute.
  DATA_TYPES = []

  # Lookup hashes supported by the hash tagging analysis plugin.
  SUPPORTED_HASHES = frozenset([])

  _DEFAULT_HASHES_PER_BATCH = 1
  _DEFAULT_LOOKUP_HASH = 'sha256'
  _DEFAULT_WAIT_AFTER_ANALYSIS = 0.0

  _REQUEST_TIMEOUT = 60

  def __init__(self):
    """Initializes a hash tagging analysis plugin."""
    super(HashTaggingAnalysisPlugin, self).__init__()
    self._batch_of_lookup_hashes = []
    self._data_stream_identifiers = set()
    self._data_streams_by_hash = collections.defaultdict(set)
    self._event_identifiers_by_data_stream = collections.defaultdict(set)
    self._hashes_per_batch = self._DEFAULT_HASHES_PER_BATCH
    self._lookup_hash = self._DEFAULT_LOOKUP_HASH
    self._wait_after_analysis = self._DEFAULT_WAIT_AFTER_ANALYSIS

  @abc.abstractmethod
  def _Analyze(self, hashes):
    """Analyzes a list of hashes.

    Args:
      hashes (list[str]): list of hashes to look up.

    Returns:
      list[HashAnalysis]: list of results of analyzing the hashes.
    """

  @abc.abstractmethod
  def _GenerateLabels(self, hash_information):
    """Generates a list of strings to tag events with.

    Args:
      hash_information (bool): response from the hash tagging analyzer that
          indicates that the file hash was present or not.

    Returns:
      list[str]: list of labels to apply to event.
    """

  def _MakeRequestAndDecodeJSON(self, url, method, **kwargs):
    """Make a HTTP request and decode the results as JSON.

    Args:
      url (str): URL to make a request to.
      method (str): HTTP method to used to make the request. GET and POST are
          supported.
      kwargs: parameters to the requests .get() or post() methods, depending
          on the value of the method parameter.

    Returns:
      dict[str, object]: body of the HTTP response, decoded from JSON.

    Raises:
      ConnectionError: If it is not possible to connect to the given URL, or it
          the request returns a HTTP error.
      ValueError: If an invalid HTTP method is specified.
    """
    method_upper = method.upper()
    if method_upper not in ('GET', 'POST'):
      raise ValueError('Method {0:s} is not supported')

    try:
      if method_upper == 'GET':
        response = requests.get(url, timeout=self._REQUEST_TIMEOUT, **kwargs)

      elif method_upper == 'POST':
        response = requests.post(url, timeout=self._REQUEST_TIMEOUT, **kwargs)

      response.raise_for_status()

    except requests.ConnectionError as exception:
      error_string = 'Unable to connect to {0:s} with error: {1!s}'.format(
          url, exception)
      raise errors.ConnectionError(error_string)

    except requests.HTTPError as exception:
      error_string = '{0:s} returned a HTTP error: {1!s}'.format(
          url, exception)
      raise errors.ConnectionError(error_string)

    return response.json()

  def _ProcessHashAnalysis(self, analysis_mediator, hash_analysis):
    """Processes the results of the analysis of a hash.

    This method ensures that labels are generated for the hash,
    then tags all events derived from files with that hash.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.
      hash_analysis (HashAnalysis): hash analysis plugin's results for a given
          hash.
    """
    labels = self._GenerateLabels(hash_analysis.hash_information)

    try:
      data_stream_identifiers = self._data_streams_by_hash.pop(
          hash_analysis.subject_hash)
    except KeyError:
      data_stream_identifiers = []
      logger.error((
          'unable to retrieve data streams for digest hash: {0:s}').format(
              hash_analysis.subject_hash))

    for data_stream_identifier in data_stream_identifiers:
      event_identifiers = self._event_identifiers_by_data_stream.pop(
          data_stream_identifier)

      # Do no bail out earlier to maintain the state of
      # self._data_streams_by_hash and self._event_identifiers_by_data_stream.
      if not labels:
        continue

      for event_identifier in event_identifiers:
        event_tag = events.EventTag()
        event_tag.SetEventIdentifier(event_identifier)

        try:
          event_tag.AddLabels(labels)
        except (TypeError, ValueError):
          error_label = 'error_{0:s}'.format(self.NAME)
          logger.error((
              'unable to add labels: {0!s} for digest hash: {1:s} defaulting '
              'to: {2:s}').format(
                  labels, hash_analysis.subject_hash, error_label))
          labels = [error_label]
          event_tag.AddLabels(labels)

        analysis_mediator.ProduceEventTag(event_tag)

        for label in labels:
          self._analysis_counter[label] += 1

  def CompileReport(self, analysis_mediator):
    """Compiles an analysis report.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.

    Returns:
      AnalysisReport: report.
    """
    if self._batch_of_lookup_hashes:
      for hash_analysis in self._Analyze(self._batch_of_lookup_hashes):
        self._ProcessHashAnalysis(analysis_mediator, hash_analysis)

      self._batch_of_lookup_hashes = []

    return super(HashTaggingAnalysisPlugin, self).CompileReport(
        analysis_mediator)

  def ExamineEvent(
      self, analysis_mediator, event, event_data, event_data_stream):
    """Evaluates whether an event contains the right data for a hash lookup.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    if (not self._lookup_hash or not event_data_stream or
        event_data.data_type not in self.DATA_TYPES):
      return

    data_stream_identifier = event_data_stream.GetIdentifier()
    if data_stream_identifier not in self._data_stream_identifiers:
      self._data_stream_identifiers.add(data_stream_identifier)

      lookup_hash = '{0:s}_hash'.format(self._lookup_hash)
      lookup_hash = getattr(event_data_stream, lookup_hash, None)
      if not lookup_hash:
        path_specification = getattr(event_data_stream, 'path_spec', None)
        display_name = analysis_mediator.GetDisplayNameForPathSpec(
            path_specification)
        logger.warning((
            'Lookup hash attribute: {0:s}_hash missing from event data stream: '
            '{1:s}.').format(self._lookup_hash, display_name))

      else:
        self._data_streams_by_hash[lookup_hash].add(data_stream_identifier)
        self._batch_of_lookup_hashes.append(lookup_hash)

    event_identifier = event.GetIdentifier()
    self._event_identifiers_by_data_stream[data_stream_identifier].add(
        event_identifier)

    if len(self._batch_of_lookup_hashes) >= self._hashes_per_batch:
      for hash_analysis in self._Analyze(self._batch_of_lookup_hashes):
        self._ProcessHashAnalysis(analysis_mediator, hash_analysis)

      self._batch_of_lookup_hashes = []

      time.sleep(self._wait_after_analysis)

  def SetLookupHash(self, lookup_hash):
    """Sets the hash to query.

    Args:
      lookup_hash (str): name of the hash attribute to look up.

    Raises:
      ValueError: if the lookup hash is not supported.
    """
    if lookup_hash not in self.SUPPORTED_HASHES:
      raise ValueError('Unsupported lookup hash: {0!s}'.format(lookup_hash))

    self._lookup_hash = lookup_hash
