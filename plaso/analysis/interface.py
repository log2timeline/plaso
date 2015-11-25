# -*- coding: utf-8 -*-
"""This file contains the interface for analysis plugins."""

import abc
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

from collections import defaultdict

from plaso.analysis import definitions
from plaso.engine import queue
from plaso.lib import timelib
from plaso.lib import errors
from plaso.lib import event


class AnalysisPlugin(queue.ItemQueueConsumer):
  """Class that implements the analysis plugin object interface."""

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

  # A flag to indicate that this plugin takes a long time to compile a report.
  LONG_RUNNING_PLUGIN = False

  def __init__(self, incoming_queue):
    """Initializes an analysis plugin.

    Args:
      incoming_queue: A queue that is used to listen to incoming events.
    """
    super(AnalysisPlugin, self).__init__(incoming_queue)
    self.plugin_type = definitions.PLUGIN_TYPE_REPORT

  def _ConsumeItem(self, item, analysis_mediator=None, **kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      item: the item object.
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      kwargs: keyword arguments to pass to the _ConsumeItem callback.
    """
    # TODO: rename to ExamineItem.
    self.ExamineEvent(analysis_mediator, item, **kwargs)

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.NAME

  @abc.abstractmethod
  def CompileReport(self, analysis_mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """

  @abc.abstractmethod
  def ExamineEvent(self, analysis_mediator, event_object, **kwargs):
    """Analyzes an event object.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: An event object (instance of EventObject).
    """

  def RunPlugin(self, analysis_mediator):
    """For each item in the queue send the read event to analysis.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
    """
    self.ConsumeItems(analysis_mediator=analysis_mediator)

    analysis_report = self.CompileReport(analysis_mediator)

    if analysis_report:
      analysis_report.time_compiled = timelib.Timestamp.GetNow()
      analysis_mediator.ProduceAnalysisReport(
          analysis_report, plugin_name=self.plugin_name)
    analysis_mediator.ReportingComplete()


class HashTaggingAnalysisPlugin(AnalysisPlugin):
  """An interface for plugins that tag events based on the source file hash.

  An implementation of this class should be paired with an implementation of
  the HashAnalyzer interface.

  Attributes:
    hash_analysis_queue: A queue (instance of Queue.Queue) that contains
                         the results of analysis of file hashes.
    hash_queue: A queue (instance of Queue.Queue) that contains file hashes.
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
  # Hashing analysis plugins can take a long time to run, so set this by
  # default.
  LONG_RUNNING_PLUGIN = True

  def __init__(self, incoming_queue, analyzer_class):
    """Initializes a hash tagging analysis plugin.

    Args:
      incoming_queue: A queue that is used to listen for incoming events.
      analyzer_class: A subclass of HashAnalyzer that will be instantiated
                      by the plugin.
    """
    super(HashTaggingAnalysisPlugin, self).__init__(incoming_queue)
    self._analysis_queue_timeout = self.DEFAULT_QUEUE_TIMEOUT
    self._analyzer_started = False
    self._event_uuids_by_pathspec = defaultdict(list)
    self._hash_pathspecs = defaultdict(list)
    self._requester_class = None
    self._time_of_last_status_log = time.time()
    self.hash_analysis_queue = Queue.Queue()
    self.hash_queue = Queue.Queue()

    self._analyzer = analyzer_class(self.hash_queue, self.hash_analysis_queue)

  def _GenerateTextLine(self, analysis_mediator, pathspec, tag_strings):
    """Generates a line of text regarding the plugins findings.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      pathspec: The pathspec (instance of dfvfs.PathSpec) whose hash was
                looked up by the plugin.
      tag_strings: A list of strings describing the plugin's results for a given
                   pathspec.
    """
    display_name = analysis_mediator.GetDisplayName(pathspec)
    return u'{0:s}: {1:s}'.format(display_name, u', '.join(tag_strings))

  @abc.abstractmethod
  def GenerateTagStrings(self, hash_information):
    """Generates a list of strings to tag events with.

    Args:
      hash_information: An object that encapsulates the result of the
                        analysis of a hash, as returned by the Analyze() method
                        of the analyzer class associated with this plugin.

    Returns:
      A list of string tags to apply to events.
    """

  def _CreateTag(self, event_uuid, tag_strings):
    """Creates an event tag.

    Args:
      event_uuid: The UUID of the event that should be tagged.
      tag_strings: A list of strings that the event should be tagged with.
    """
    event_tag = event.EventTag()
    event_tag.event_uuid = event_uuid
    event_tag.comment = u'Tag applied by {0:s} analysis plugin'.format(
        self.NAME)
    event_tag.tags = tag_strings
    return event_tag

  def _HandleHashAnalysis(self, hash_analysis):
    """Deals with a the results of the analysis of a hash.

    This method ensures that tag strings are generated for the hash,
    then tags all events derived from files with that hash.

    Args:
      hash_analysis: The the hash analysis plugin's results for a given hash
                     (instance of HashAnalysis).

    Returns:
      A tuple of:
        pathspecs: A list of pathspecs that had the hash value looked up.
        tag_strings: A list of strings that corresponds to the hash value that
                     was looked up.
        tags: A list of EventTags for all events that were extracted from the
              pathspecs.
    """
    tags = []
    event_uuids = []
    tag_strings = self.GenerateTagStrings(hash_analysis.hash_information)
    pathspecs = self._hash_pathspecs[hash_analysis.subject_hash]
    for pathspec in pathspecs:
      event_uuids.extend(self._event_uuids_by_pathspec[pathspec])
    for event_uuid in event_uuids:
      tag = self._CreateTag(event_uuid, tag_strings)
      tags.append(tag)
    return pathspecs, tag_strings, tags

  def _EnsureRequesterStarted(self):
    """Checks if the analyzer is running and starts it if not."""
    if not self._analyzer_started:
      self._analyzer.start()
      self._analyzer_started = True

  def ExamineEvent(self, analysis_mediator, event_object, **kwargs):
    """Evaluates whether an event contains the appropriate data for a hash
    lookup.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: An event object (instance of EventObject).
    """
    self._EnsureRequesterStarted()
    pathspec = event_object.pathspec
    event_uuids = self._event_uuids_by_pathspec[pathspec]
    event_uuids.append(event_object.uuid)
    if event_object.data_type in self.DATA_TYPES:
      for attribute in self.REQUIRED_HASH_ATTRIBUTES:
        hash_for_lookup = getattr(event_object, attribute, None)
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
              event_object.uuid, self.REQUIRED_HASH_ATTRIBUTES)
      logging.warning(warning_message)

  def _ContinueReportCompilation(self):
    """Determines if the plugin should continue trying to compile the report.

    Returns:
      True if the plugin should continue, False otherwise.
    """
    analyzer_alive = self._analyzer.is_alive()
    hash_queue_has_tasks = self.hash_queue.unfinished_tasks > 0
    analysis_queue = not self.hash_analysis_queue.empty()
    return (analyzer_alive and hash_queue_has_tasks) or analysis_queue

  def EstimateTimeRemaining(self):
    """Estimate how long until all hashes have been analyzed.

    Returns:
      The estimated number of seconds until all hashes have been analyzed.
    """
    number_of_hashes = self.hash_queue.qsize()
    hashes_per_batch = self._analyzer.hashes_per_batch
    wait_time_per_batch = self._analyzer.wait_after_analysis
    average_analysis_time = (
        self._analyzer.seconds_spent_analyzing /
        self._analyzer.analyses_performed)
    batches_remaining = number_of_hashes / hashes_per_batch
    estimated_seconds_per_batch = average_analysis_time + wait_time_per_batch
    return batches_remaining * estimated_seconds_per_batch

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

  def CompileReport(self, analysis_mediator):
    """Compiles a report of the analysis.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
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
      pathspecs, tag_strings, new_tags = self._HandleHashAnalysis(
          hash_analysis)
      tags.extend(new_tags)
      for pathspec in pathspecs:
        text_line = self._GenerateTextLine(
            analysis_mediator, pathspec, tag_strings)
        lines_of_text.append(text_line)
    self._analyzer.SignalAbort()

    report = event.AnalysisReport(self.NAME)
    report.SetText(lines_of_text)
    report.SetTags(tags)
    return report


class HashAnalyzer(threading.Thread):
  """Class that defines the interfaces for hash analyzer threads.

  This interface should be implemented once for each hash analysis plugin.

  Attributes:
    analyses_performed: The number of analysis batches completed by this
                        analyzer.
    hashes_per_batch: The maximum number of hashes to analyze at once.
    seconds_spent_analyzing: The number of seconds this analyzer has spent
                             performing analysis (as opposed to waiting on
                             queues, etc.)
    wait_after_analysis: How long the analyzer will sleep for after analyzing a
                         batch of hashes.
  """
  # How long to wait for new items to be added to the the input queue.
  EMPTY_QUEUE_WAIT_TIME = 4

  def __init__(
      self, hash_queue, hash_analysis_queue, hashes_per_batch=1,
      wait_after_analysis=0):
    """Initializes a hash analyzer.

    Args:
      hash_queue: A queue (instance of Queue.queue) that contains hashes to
                  be analyzed.
      hash_analysis_queue: A queue (instance of Queue.queue) that the analyzer
                           will append HashAnalysis objects to.
      hashes_per_batch: The number of hashes to analyze at once. The default
                        is 1.
      wait_after_analysis: The number of seconds to wait after each batch is
                           analyzed. The default is 0.
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
    self.daemon = True

  @abc.abstractmethod
  def Analyze(self, hashes):
    """Analyzes a list of hashes.

    Args:
      hashes: A list of hashes (strings) to look up.

    Returns:
      A list of hash analysis objects (instances of HashAnalysis).
    """

  def _GetHashes(self, target_queue, max_hashes):
    """Retrieves a list of items from a queue.

    Args:
      target_queue: The target_queue to retrieve items from.
      max_hashes: The maximum number of items to retrieve from the target_queue.

    Returns:
      A list of at most max_hashes elements from the target_queue. The list
      may have no elements if the target_queue is empty.
    """
    hashes = []
    for _ in range(0, max_hashes):
      try:
        item = target_queue.get_nowait()
      except Queue.Empty:
        continue
      hashes.append(item)
    return hashes

  def SignalAbort(self):
    """Instructs this analyzer to stop running."""
    self._abort = True

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


class HTTPHashAnalyzer(HashAnalyzer):
  """A class that provides a useful interface for hash plugins using HTTP(S)"""

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes a HTTP hash analyzer.

    Args:
      hash_queue: A queue (instance of Queue.queue) that contains hashes to
                  be analyzed.
      hash_analysis_queue: A queue (instance of Queue.queue) that the analyzer
                           will append HashAnalysis objects to.
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
      hashes: A list of hashes (strings) to look up.

    Returns:
      A list of hash analysis objects (instances of HashAnalysis).
    """

  def MakeRequestAndDecodeJSON(self, url, method, **kwargs):
    """Make a HTTP request and decode the results as JSON.

    Args:
      url: The URL to make a request to.
      method: The HTTP method to use to make the request, as a string. GET and
              POST are supported.
      kwargs: Parameters to the requests .get() or post() methods, depending
              on the value of the method parameter.

    Returns:
      The body of the HTTP response, decoded from JSON.

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
    hash_information: An object containing information about the hash.
    subject_hash: The hash that was analyzed.
  """

  def __init__(self, subject_hash, hash_information):
    """Initializes a HashAnalysis object.

    Args:
      subject_hash: The hash that the hash_information relates to.
      hash_information: An object containing information about the hash.
                        This object will be used by the _GenerateTagString
                        method in the HashTaggingAnalysisPlugin to tag events
                        that relate to the hash.
    """
    self.hash_information = hash_information
    self.subject_hash = subject_hash
