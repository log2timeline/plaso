# -*- coding: utf-8 -*-
"""This file contains the interface for analysis plugins."""

import abc
from collections import defaultdict
import logging
import Queue
import sys
import threading
import time

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
    hash_analysis_queue (Queue.queue): queue that contains the results of
        analysis of file hashes.
    hash_queue (Queue.queue): queue that contains file hashes.
  """
  # The event data types the plugin will collect hashes from. Subclasses
  # must override this attribute.
  DATA_TYPES = []

  # The plugin will select hashes from the event objects from these attributes,
  # in priority order. More collision-resistant hashing algorithms should be
  # preferred over less resistant algorithms.
  REQUIRED_HASH_ATTRIBUTES = frozenset(
      [u'sha256_hash', u'sha1_hash', u'md5_hash'])

  # The default number of seconds for the plugin to wait for analysis results
  # to be added to the hash_analysis_queue by the analyzer thread.
  DEFAULT_QUEUE_TIMEOUT = 4
  SECONDS_BETWEEN_STATUS_LOG_MESSAGES = 30

  def __init__(self, analyzer_class):
    """Initializes a hash tagging analysis plugin.

    Args:
      analyzer_class (type): A subclass of HashAnalyzer that will be
          instantiated by the plugin.
    """
    super(HashTaggingAnalysisPlugin, self).__init__()
    self._analysis_queue_timeout = self.DEFAULT_QUEUE_TIMEOUT
    self._analyzer_started = False
    self._event_uuids_by_pathspec = defaultdict(list)
    self._hash_pathspecs = defaultdict(list)
    self._requester_class = None
    self._time_of_last_status_log = time.time()
    self.hash_analysis_queue = Queue.Queue()
    self.hash_queue = Queue.Queue()

    self._analyzer = analyzer_class(self.hash_queue, self.hash_analysis_queue)

  def _GenerateTextLine(self, mediator, pathspec, labels):
    """Generates a line of text regarding the plugin's findings.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      pathspec (dfvfs.PathSpec): pathspec whose hash was looked up by the
          plugin.
      labels (list[str]): strings describing the plugin's results for a given
          pathspec.

    Returns:
      str: human readable text regarding the plugin's findings.
    """
    display_name = mediator.GetDisplayName(pathspec)
    return u'{0:s}: {1:s}'.format(display_name, u', '.join(labels))

  def _CreateTag(self, event_uuid, labels):
    """Creates an event tag.

    Args:
      event_uuid (uuid.UUID): identifier of the event that should be tagged.
      labels (list[str]): labels for the gag.

    Returns:
      EventTag: event tag.
    """
    event_tag = events.EventTag(
        comment=u'Tag applied by {0:s} analysis plugin'.format(self.NAME),
        event_uuid=event_uuid)
    event_tag.AddLabels(labels)
    return event_tag

  def _HandleHashAnalysis(self, hash_analysis):
    """Deals with the results of the analysis of a hash.

    This method ensures that labels are generated for the hash,
    then tags all events derived from files with that hash.

    Args:
      hash_analysis (HashAnalysis): hash analysis plugin's results for a given
          hash.

    Returns:
      tuple: containing:

        list[dfvfs.PathSpec]: pathspecs that had the hash value looked up.
        list[str]: labels that corresponds to the hash value that was looked up.
        list[EventTag]: event tags for all events that were extracted from the
            path specifications.
    """
    tags = []
    labels = self.GenerateLabels(hash_analysis.hash_information)
    pathspecs = self._hash_pathspecs.pop(hash_analysis.subject_hash)
    for pathspec in pathspecs:
      event_uuids = self._event_uuids_by_pathspec.pop(pathspec)
      if labels:
        for event_uuid in event_uuids:
          tag = self._CreateTag(event_uuid, labels)
          tags.append(tag)
    return pathspecs, labels, tags

  def _EnsureRequesterStarted(self):
    """Checks if the analyzer is running and starts it if not."""
    if not self._analyzer_started:
      self._analyzer.start()
      self._analyzer_started = True

  def ExamineEvent(self, mediator, event):
    """Evaluates whether an event contains the right data for a hash lookup.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
    """
    self._EnsureRequesterStarted()
    pathspec = event.pathspec
    event_uuids = self._event_uuids_by_pathspec[pathspec]
    event_uuids.append(event.uuid)
    if event.data_type in self.DATA_TYPES:
      for attribute in self.REQUIRED_HASH_ATTRIBUTES:
        hash_for_lookup = getattr(event, attribute, None)
        if not hash_for_lookup:
          continue
        pathspecs = self._hash_pathspecs[hash_for_lookup]
        pathspecs.append(pathspec)
        # There may be multiple pathspecs that have the same hash. We only
        # want to look them up once.
        if len(pathspecs) == 1:
          self.hash_queue.put(hash_for_lookup)
        return
      warning_message = (
          u'Event with ID {0:s} had none of the required attributes '
          u'{1:s}.').format(
              event.uuid, self.REQUIRED_HASH_ATTRIBUTES)
      logging.warning(warning_message)

  def _ContinueReportCompilation(self):
    """Determines if the plugin should continue trying to compile the report.

    Returns:
      bool: True if the plugin should continue, False otherwise.
    """
    analyzer_alive = self._analyzer.is_alive()
    hash_queue_has_tasks = self.hash_queue.unfinished_tasks > 0
    analysis_queue = not self.hash_analysis_queue.empty()
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
    tags = []
    lines_of_text = [u'{0:s} hash tagging Results'.format(self.NAME)]
    while self._ContinueReportCompilation():
      try:
        self._LogProgressUpdateIfReasonable()
        hash_analysis = self.hash_analysis_queue.get(
            timeout=self._analysis_queue_timeout)
      except Queue.Empty:
        # The result queue is empty, but there could still be items that need
        # to be processed by the analyzer.
        continue
      pathspecs, labels, new_tags = self._HandleHashAnalysis(
          hash_analysis)
      tags.extend(new_tags)
      if labels:
        for pathspec in pathspecs:
          text_line = self._GenerateTextLine(mediator, pathspec, labels)
          lines_of_text.append(text_line)

    self._analyzer.SignalAbort()

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)
    analysis_report = reports.AnalysisReport(
        plugin_name=self.NAME, text=report_text)
    analysis_report.SetTags(tags)
    return analysis_report

  def EstimateTimeRemaining(self):
    """Estimates how long until all hashes have been analyzed.

    Returns:
      int: estimated number of seconds until all hashes have been analyzed.
    """
    number_of_hashes = self.hash_queue.qsize()
    hashes_per_batch = self._analyzer.hashes_per_batch
    wait_time_per_batch = self._analyzer.wait_after_analysis
    try:
      average_analysis_time = divmod(
          self._analyzer.seconds_spent_analyzing,
          self._analyzer.analyses_performed)
    except ZeroDivisionError:
      average_analysis_time = 1
    batches_remaining = divmod(number_of_hashes, hashes_per_batch)
    estimated_seconds_per_batch = average_analysis_time + wait_time_per_batch
    return batches_remaining * estimated_seconds_per_batch

  @abc.abstractmethod
  def GenerateLabels(self, hash_information):
    """Generates a list of strings to tag events with.

    Args:
      hash_information (object): object that mediates the result of the
          analysis of a hash, as returned by the Analyze() method of the
          analyzer class associated with this plugin.

    Returns:
      list[str]: list of labels to apply to events.
    """


class HashAnalyzer(threading.Thread):
  """Class that defines the interfaces for hash analyzer threads.

  This interface should be implemented once for each hash analysis plugin.

  Attributes:
    analyses_performed (int): number of analysis batches completed by this
        analyzer.
    hashes_per_batch (int): maximum number of hashes to analyze at once.
    seconds_spent_analyzing (int): number of seconds this analyzer has spent
        performing analysis (as opposed to waiting on queues, etc.)
    wait_after_analysis (int): number of seconds the analyzer will sleep for
        after analyzing a batch of hashes.
  """
  # How long to wait for new items to be added to the the input queue.
  EMPTY_QUEUE_WAIT_TIME = 4

  def __init__(
      self, hash_queue, hash_analysis_queue, hashes_per_batch=1,
      wait_after_analysis=0):
    """Initializes a hash analyzer.

    Args:
      hash_queue (Queue.queue): contains hashes to be analyzed.
      hash_analysis_queue (Queue.queue): queue that the analyzer will append
          HashAnalysis objects to.
      hashes_per_batch (Optional[int]): number of hashes to analyze at once.
      wait_after_analysis (Optional[int]: number of seconds to wait after each
          batch is analyzed.
    """
    super(HashAnalyzer, self).__init__()
    self._abort = False
    self._hash_queue = hash_queue
    self._hash_analysis_queue = hash_analysis_queue
    self.analyses_performed = 0
    self.hashes_per_batch = hashes_per_batch
    self.seconds_spent_analyzing = 0
    self.wait_after_analysis = wait_after_analysis
    # Indicate that this is a daemon thread. The program will exit if only
    # daemon threads are running. This thread should never block program exit.

  def _GetHashes(self, target_queue, max_hashes):
    """Retrieves a list of items from a queue.

    Args:
      target_queue (Queue.queue): queue to retrieve hashes from.
      max_hashes (int): maximum number of items to retrieve from the
          target_queue.

    Returns:
      list[object]: list of at most max_hashes elements from the target_queue.
          The list may have no elements if the target_queue is empty.
    """
    hashes = []
    for _ in range(0, max_hashes):
      try:
        item = target_queue.get_nowait()
      except Queue.Empty:
        continue
      hashes.append(item)
    return hashes

  @abc.abstractmethod
  def Analyze(self, hashes):
    """Analyzes a list of hashes.

    Args:
      hashes (list[str]): list of hashes to look up.

    Returns:
      list[HashAnalysis]: list of results of analyzing the hashes.
    """

  # This method is part of the threading.Thread interface, hence its name does
  # not follow the style guide.
  def run(self):
    """The method called by the threading library to start the thread."""
    while not self._abort:
      hashes = self._GetHashes(self._hash_queue, self.hashes_per_batch)
      if hashes:
        time_before_analysis = time.time()
        hash_analyses = self.Analyze(hashes)
        current_time = time.time()
        self.seconds_spent_analyzing += current_time - time_before_analysis
        self.analyses_performed += 1
        for hash_analysis in hash_analyses:
          self._hash_analysis_queue.put(hash_analysis)
          self._hash_queue.task_done()
        time.sleep(self.wait_after_analysis)
      else:
        # Wait for some more hashes to be added to the queue.
        time.sleep(self.EMPTY_QUEUE_WAIT_TIME)

  def SignalAbort(self):
    """Instructs this analyzer to stop running."""
    self._abort = True


class HTTPHashAnalyzer(HashAnalyzer):
  """A class that provides a useful interface for hash plugins using HTTP(S)"""

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes a HTTP hash analyzer.

    Args:
      hash_queue (Queue.queue): A queue that contains hashes to be analyzed.
      hash_analysis_queue (Queue.queue): queue that the analyzer will append
          HashAnalysis objects to.
    """
    super(HTTPHashAnalyzer, self).__init__(
        hash_queue, hash_analysis_queue, **kwargs)
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
  def Analyze(self, hashes):
    """Analyzes a list of hashes.

    Args:
      hashes (list[str]): hashes to look up.

    Returns:
      list[HashAnalysis]: analysis results.
    """

  def MakeRequestAndDecodeJSON(self, url, method, **kwargs):
    """Make a HTTP request and decode the results as JSON.

    Args:
      url (str): URL to make a request to.
      method (str): HTTP method to used to make the request. GET and POST are
          supported.
      kwargs: Parameters to the requests .get() or post() methods, depending
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


class HashAnalysis(object):
  """A class that holds information about a hash.

  Attributes:
    hash_information (object): object containing information about the hash.
    subject_hash (str):  hash that was analyzed.
  """

  def __init__(self, subject_hash, hash_information):
    """Initializes a HashAnalysis object.

    Args:
      subject_hash (str): hash that the hash_information relates to.
      hash_information (object): information about the hash. This object will be
          used by the GenerateLabels method in the HashTaggingAnalysisPlugin
          to tag events that relate to the hash.
    """
    self.hash_information = hash_information
    self.subject_hash = subject_hash
