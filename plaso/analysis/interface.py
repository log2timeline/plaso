# -*- coding: utf-8 -*-
"""This file contains the interface for analysis plugins."""

import abc
import collections
import logging
import sys
import threading
import time

if sys.version_info[0] < 3:
  import Queue
else:
  import queue as Queue  # pylint: disable=import-error

import requests

# Some distributions unvendor urllib3 from the requests module, and we need to
# access some methods inside urllib3 to disable warnings. We'll try to import it
# here, to keep the imports together.
try:
  import urllib3
except ImportError:
  urllib3 = None

from plaso.analysis import definitions
from plaso.containers import events
from plaso.containers import reports
from plaso.lib import errors


class AnalysisPlugin(object):
  """Class that defines the analysis plugin interface."""

  # The URLS should contain a list of URLs with additional information about
  # this analysis plugin.
  URLS = []

  # The name of the plugin. This is the name that is matched against when
  # loading plugins, so it is important that this name is short, concise and
  # explains the nature of the plugin easily. It also needs to be unique.
  NAME = u'analysis_plugin'

  # A flag indicating whether or not this plugin should be run during extraction
  # phase or reserved entirely for post processing stage.
  # Typically this would mean that the plugin is perhaps too computationally
  # heavy to be run during event extraction and should rather be run during
  # post-processing.
  # Since most plugins should perhaps rather be run during post-processing
  # this is set to False by default and needs to be overwritten if the plugin
  # should be able to run during the extraction phase.
  ENABLE_IN_EXTRACTION = False

  def __init__(self):
    """Initializes an analysis plugin."""
    super(AnalysisPlugin, self).__init__()
    self.plugin_type = definitions.PLUGIN_TYPE_REPORT

  @property
  def plugin_name(self):
    """str: name of the plugin."""
    return self.NAME

  def _CreateEventTag(self, event, comment, labels):
    """Creates an event tag.

    Args:
      event (EventObject): event to tag.
      comment (str): event tag comment.
      labels (list[str]): event tag labels.
    """
    event_identifier = event.GetIdentifier()

    event_tag = events.EventTag(comment=comment)
    event_tag.SetEventIdentifier(event_identifier)
    event_tag.AddLabels(labels)

    event_identifier_string = event_identifier.CopyToString()
    logging.debug(u'Created event tag: {0:s} for event: {1:s}'.format(
        comment, event_identifier_string))

    return event_tag

  @abc.abstractmethod
  def CompileReport(self, mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: report.
    """

  @abc.abstractmethod
  def ExamineEvent(self, mediator, event):
    """Analyzes an event object.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
    """


class HashTaggingAnalysisPlugin(AnalysisPlugin):
  """An interface for plugins that tag events based on the source file hash.

  An implementation of this class should be paired with an implementation of
  the HashAnalyzer interface.

  Attributes:
    digest_hash_recording_queue (Queue.queue): that the analyzer will add
        resulting digest hash recording to.
    hash_queue (Queue.queue): that contains hashes to be analyzed.
  """
  # The event data types the plugin will collect hashes from. Subclasses
  # must override this attribute.
  DATA_TYPES = []

  # The default number of seconds for the plugin to wait for analysis results
  # to be added to the digest_hash_recording_queue by the analyzer thread.
  DEFAULT_QUEUE_TIMEOUT = 4
  SECONDS_BETWEEN_STATUS_LOG_MESSAGES = 30

  def __init__(self, analyzer_class):
    """Initializes a hash tagging analysis plugin.

    Args:
      analyzer_class (type): a subclass of HashAnalyzer that will be
          instantiated by the plugin.
    """
    super(HashTaggingAnalysisPlugin, self).__init__()
    self._analysis_queue_timeout = self.DEFAULT_QUEUE_TIMEOUT
    self._analyzer_started = False
    # Note that collections.defaultdict will create an element of
    # the specified type.
    self._event_identifiers_by_hash = collections.defaultdict(list)
    self._path_spec_by_event_identifier = {}
    self._requester_class = None
    self._tag_comment = u'Tag applied by {0:s} analysis plugin'.format(
        self.NAME)
    self._time_of_last_status_log = time.time()
    self.digest_hash_recording_queue = Queue.Queue()
    self.hash_queue = Queue.Queue()

    self._analyzer = analyzer_class(
        self.hash_queue, self.digest_hash_recording_queue)

  def _HandleHashAnalysis(self, hash_analysis):
    """Deals with the results of the analysis of a hash.

    logging.debug(u'Created event tag: {0:s} for event: {1:s}'.format(
        comment, event_identifier.identifier))

    Returns:
      tuple: containing:

        list[dfvfs.PathSpec]: pathspecs that had the hash value looked up.
        list[str]: labels that corresponds to the hash value that was looked up.
        list[EventTag]: event tags for all events that were extracted from the
            path specifications.
    """
    tags = []
    labels = self.GenerateLabels(hash_analysis.hash_information)
    path_specifications = self._hash_pathspecs.pop(hash_analysis.subject_hash)
    for path_specification in path_specifications:
      event_identifiers = self._event_identifiers_by_pathspec.pop(
          path_specification, [])

      if not labels:
        continue

      for event_identifier in event_identifiers:
        event_tag = events.EventTag(comment=self._comment)
        event_tag.SetEventIdentifier(event_identifier)
        event_tag.AddLabels(labels)

        tags.append(event_tag)

    return path_specifications, labels, tags

  def _EnsureRequesterStarted(self):
    """Checks if the analyzer is running and starts it if not."""
    if not self._analyzer_started:
      self._analyzer.start()
      self._analyzer_started = True

  def _ContinueReportCompilation(self):
    """Determines if the plugin should continue trying to compile the report.

    Returns:
      bool: True if the plugin should continue, False otherwise.
    """
    analyzer_alive = self._analyzer.is_alive()
    hash_queue_has_tasks = self.hash_queue.unfinished_tasks > 0
    analysis_queue = not self.digest_hash_recording_queue.empty()
    return (analyzer_alive and hash_queue_has_tasks) or analysis_queue

  # TODO: Refactor to do this more elegantly, perhaps via callback.
  def _LogProgressUpdateIfReasonable(self):
    """Prints a progress update if enough time has passed."""
    next_log_time = (
        self._time_of_last_status_log +
        self.SECONDS_BETWEEN_STATUS_LOG_MESSAGES)
    current_time = time.time()
    if current_time < next_log_time:
      return

    completion_time = time.ctime(current_time + self.EstimateTimeRemaining())
    log_message = (
        u'{0:s} hash analysis plugin running. {1:d} hashes in queue, '
        u'estimated completion time {2:s}.'.format(
            self.NAME, self.hash_queue.qsize(), completion_time))
    logging.info(log_message)
    self._time_of_last_status_log = current_time

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: report.
    """
    lines_of_text = [u'{0:s} hash tagging Results'.format(self.NAME)]
    while self._ContinueReportCompilation():
      self._LogProgressUpdateIfReasonable()

      try:
        digest_hash_recording = self.digest_hash_recording_queue.get(
            timeout=self._analysis_queue_timeout)
      except Queue.Empty:
        # The result queue is empty, but there could still be items that need
        # to be processed by the analyzer.
        continue

      labels = digest_hash_recording.labels or []

      event_identifiers = self._event_identifiers_by_hash[
          digest_hash_recording.digest_hash]

      for event_identifier in iter(event_identifiers):
        event_tag = self._CreateEventTag(
            event_identifier, self._tag_comment, labels)
        mediator.ProduceEventTag(event_tag)

        path_spec = self._path_spec_by_event_identifier.get(
            event_identifier, None)
        if not path_spec:
          display_name = event_identifier.identifier
        else:
          display_name = mediator.GetDisplayName(path_spec)

        text_line = u'{0:s}: {1:s}'.format(display_name, u', '.join(labels))
        lines_of_text.append(text_line)

    self._analyzer.SignalAbort()

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)

    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)

  def EstimateTimeRemaining(self):
    """Estimates how long until all hashes have been analyzed.

    Returns:
      int: estimated number of seconds until all hashes have been analyzed.
    """
    number_of_hashes = self.hash_queue.qsize()
    hashes_per_batch = self._analyzer.hashes_per_batch
    wait_time_per_batch = self._analyzer.wait_after_analysis
    analyses_performed = self._analyzer.analyses_performed

    if analyses_performed == 0:
      average_analysis_time = self._analyzer.seconds_spent_analyzing
    else:
      average_analysis_time, _ = divmod(
          self._analyzer.seconds_spent_analyzing, analyses_performed)

    batches_remaining, _ = divmod(number_of_hashes, hashes_per_batch)
    estimated_seconds_per_batch = average_analysis_time + wait_time_per_batch
    return batches_remaining * estimated_seconds_per_batch

  def ExamineEvent(self, mediator, event):
    """Evaluates whether an event contains the right data for a hash lookup.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
    """
    self._EnsureRequesterStarted()

    if event.data_type not in self.DATA_TYPES:
      return

    event_identifier = event.GetIdentifier()

    digest_hash = None
    for attribute_name in self.REQUIRED_HASH_ATTRIBUTES:
      digest_hash = getattr(event, attribute_name, None)
      if digest_hash:
        break

    if not digest_hash:
      warning_message = (
          u'Event with ID {0:s} had none of the required attributes '
          u'{1:s}.').format(
              event_identifier.identifier, self.REQUIRED_HASH_ATTRIBUTES)
      logging.warning(warning_message)
      return

    event_identifiers = self._event_identifiers_by_hash[digest_hash]
    event_identifiers.append(event_identifier)

    self._path_spec_by_event_identifier[event_identifier] = event.pathspec

    # Here we make sure we look up each hash only once.
    if len(event_identifiers) == 1:
      self.hash_queue.put(digest_hash)

  def SetLookupHash(self, lookup_hash):
    """Sets the hash to query.

    Args:
      lookup_hash (str): name of the hash attribute to look up.
    """
    self._analyzer.SetLookupHash(lookup_hash)


class HashAnalyzer(threading.Thread):
  """Class that defines the interfaces for hash analyzer threads.

  This interface should be implemented once for each hash analysis plugin.

  Attributes:
    analyses_performed (int): number of analysis batches completed by this
        analyzer.
    hashes_per_batch (int): maximum number of hashes to analyze at once.
    lookup_hash (str): name of the hash attribute to look up.
    seconds_spent_analyzing (int): number of seconds this analyzer has spent
        performing analysis (as opposed to waiting on queues, etc.)
    wait_after_analysis (int): number of seconds the analyzer will sleep for
        after analyzing a batch of hashes.
  """
  # Number of seconds to wait for new items to be added to the the input queue.
  _EMPTY_QUEUE_WAIT_TIME = 4

  # List of lookup hashes supported by the analyzer.
  SUPPORTED_HASHES = []

  def __init__(
      self, hash_queue, digest_hash_recording_queue, hashes_per_batch=1,
      lookup_hash=u'sha256', wait_after_analysis=0):
    """Initializes a hash analyzer.

    Args:
      hash_queue (Queue.queue): that contains hashes to be analyzed.
      digest_hash_recording_queue (Queue.queue): that the analyzer will add
          resulting digest hash recording to.
      hashes_per_batch (Optional[int]): number of hashes to analyze at once.
      lookup_hash (Optional[str]): name of the hash attribute to look up.
      wait_after_analysis (Optional[int]: number of seconds to wait after each
          batch is analyzed.
    """
    super(HashAnalyzer, self).__init__()
    self._abort = False
    self._digest_hash_recording_queue = digest_hash_recording_queue
    self._hash_queue = hash_queue
    self.analyses_performed = 0
    self.hashes_per_batch = hashes_per_batch
    self.lookup_hash = lookup_hash
    self.seconds_spent_analyzing = 0
    self.wait_after_analysis = wait_after_analysis

  def _GetHashes(self, hash_queue, max_hashes):
    """Retrieves a list of items from a queue.

    Args:
      hash_queue (Queue.queue): queue to retrieve hashes from.
      max_hashes (int): maximum number of items to retrieve from the
          hash_queue.

    Returns:
      list[object]: list of at most max_hashes elements from the hash_queue.
          The list may have no elements if the hash_queue is empty.
    """
    hashes = []
    for _ in range(0, max_hashes):
      try:
        item = hash_queue.get_nowait()
      except Queue.Empty:
        continue
      hashes.append(item)
    return hashes

  @abc.abstractmethod
  def Analyze(self, digest_hashes):
    """Analyzes a list of digest hashes.

    Args:
      digest_hashes (list[str]): digest hashes to look up.

    Returns:
      list[DigestHashRecording]: digest hash recordings.
    """

  # This method is part of the threading.Thread interface, hence its name does
  # not follow the style guide.
  def run(self):
    """The method called by the threading library to start the thread."""
    while not self._abort:
      digest_hashes = self._GetHashes(self._hash_queue, self.hashes_per_batch)
      if not digest_hashes:
        # Wait for some more digest hashes to be added to the queue.
        time.sleep(self._EMPTY_QUEUE_WAIT_TIME)
        continue

      time_before_analysis = time.time()
      digest_hash_recordings = self.Analyze(digest_hashes)
      current_time = time.time()
      self.seconds_spent_analyzing += current_time - time_before_analysis
      self.analyses_performed += 1
      for digest_hash_recording in digest_hash_recordings:
        self._digest_hash_recording_queue.put(digest_hash_recording)
        self._hash_queue.task_done()
      time.sleep(self.wait_after_analysis)

  def SetLookupHash(self, lookup_hash):
    """Sets the hash to query.

    Args:
      lookup_hash (str): name of the hash attribute to look up.

    Raises:
      ValueError: if the lookup hash is not supported.
    """
    if lookup_hash not in self.SUPPORTED_HASHES:
      raise ValueError(u'Unsupported lookup hash: {0!s}'.format(lookup_hash))

    self.lookup_hash = lookup_hash

  def SignalAbort(self):
    """Instructs this analyzer to stop running."""
    self._abort = True


class HTTPHashAnalyzer(HashAnalyzer):
  """A class that provides a useful interface for hash plugins using HTTP(S)"""

  def __init__(self, hash_queue, digest_hash_recording_queue, **kwargs):
    """Initializes a HTTP hash analyzer.

    Args:
      hash_queue (Queue.queue): that contains hashes to be analyzed.
      digest_hash_recording_queue (Queue.queue): that the analyzer will add
          resulting digest hash recording to.
    """
    super(HTTPHashAnalyzer, self).__init__(
        hash_queue, digest_hash_recording_queue, **kwargs)
    self._checked_for_old_python_version = False

  def _CheckPythonVersionAndDisableWarnings(self):
    """Checks python version, and disables SSL warnings.

    urllib3 will warn on each HTTPS request made by older versions of Python.
    Rather than spamming the user, we print one warning message, then disable
    warnings in urllib3.
    """
    if self._checked_for_old_python_version:
      return
    if sys.version_info[0:3] < (2, 7, 9):
      logging.warn(
          u'You are running a version of Python prior to 2.7.9. Your version '
          u'of Python has multiple weaknesses in its SSL implementation that '
          u'can allow an attacker to read or modify SSL encrypted data. '
          u'Please update. Further SSL warnings will be suppressed. See '
          u'https://www.python.org/dev/peps/pep-0466/ for more information.')
      # Some distributions de-vendor urllib3 from requests, so we have to
      # check if this has occurred and disable warnings in the correct
      # package.
      if (hasattr(requests, u'packages') and
          hasattr(requests.packages, u'urllib3') and
          hasattr(requests.packages.urllib3, u'disable_warnings')):
        requests.packages.urllib3.disable_warnings()
      else:
        if urllib3 and hasattr(urllib3, u'disable_warnings'):
          urllib3.disable_warnings()
    self._checked_for_old_python_version = True

  @abc.abstractmethod
  def Analyze(self, digest_hashes):
    """Analyzes a list of digest hashes.

    Args:
      digest_hashes (list[str]): digest hashes to look up.

    Returns:
      list[DigestHashRecording]: digest hash recordings.
    """

  def MakeRequestAndDecodeJSON(self, url, method, **kwargs):
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
    method = method.lower()
    if method not in [u'get', u'post']:
      raise ValueError(u'Method {0:s} is not supported')

    if url.lower().startswith(u'https'):
      self._CheckPythonVersionAndDisableWarnings()

    try:
      if method.lower() == u'get':
        response = requests.get(url, **kwargs)
      if method.lower() == u'post':
        response = requests.post(url, **kwargs)
      response.raise_for_status()
    except requests.ConnectionError as exception:
      error_string = u'Unable to connect to {0:s}: {1:s}'.format(
          url, exception)
      raise errors.ConnectionError(error_string)
    except requests.HTTPError as exception:
      error_string = u'{0:s} returned a HTTP error: {1:s}'.format(
          url, exception)
      raise errors.ConnectionError(error_string)

    return response.json()
