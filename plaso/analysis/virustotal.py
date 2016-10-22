# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in VirusTotal and tag events."""

import logging

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.lib import errors


class VirusTotalAnalyzer(interface.HTTPHashAnalyzer):
  """Class that analyzes file hashes by consulting VirusTotal."""
  _VIRUSTOTAL_API_REPORT_URL = (
      u'https://www.virustotal.com/vtapi/v2/file/report')

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes a VirusTotal Analyzer thread.

    Args:
      hash_queue (Queue.queue): queue that contains hashes to be analyzed.
      hash_analysis_queue (Queue.queue): queue the analyzer will append
          HashAnalysis objects to.
    """
    super(VirusTotalAnalyzer, self).__init__(
        hash_queue, hash_analysis_queue, **kwargs)
    self._api_key = None
    self._checked_for_old_python_version = False

  def SetAPIKey(self, api_key):
    """Sets the VirusTotal API key to use in queries.

    Args:
      api_key (str): VirusTotal API key
    """
    self._api_key = api_key

  def Analyze(self, hashes):
    """Looks up hashes in VirusTotal using the VirusTotal HTTP API.

    The API is documented here:
      https://www.virustotal.com/en/documentation/public-api/

    Args:
      hashes (list[str]): hashes to look up.

    Returns:
      list[HashAnalysis]: analysis results.

    Raises:
      RuntimeError: If the VirusTotal API key has not been set.
    """
    if not self._api_key:
      raise RuntimeError(u'No API key specified for VirusTotal lookup.')

    hash_analyses = []
    resource_string = u', '.join(hashes)
    params = {u'apikey': self._api_key, u'resource': resource_string}
    try:
      json_response = self.MakeRequestAndDecodeJSON(
          self._VIRUSTOTAL_API_REPORT_URL, u'GET', params=params)
    except errors.ConnectionError as exception:
      logging.error(
          (u'Error communicating with VirusTotal {0:s}. VirusTotal plugin is '
           u'aborting.').format(exception))
      self.SignalAbort()
      return hash_analyses

    # The content of the response from VirusTotal has a different structure if
    # one or more than one hash is looked up at once.
    if isinstance(json_response, dict):
      # Only one result.
      resource = json_response[u'resource']
      hash_analysis = interface.HashAnalysis(resource, json_response)
      hash_analyses.append(hash_analysis)
    else:
      for result in json_response:
        resource = result[u'resource']
        hash_analysis = interface.HashAnalysis(resource, result)
        hash_analyses.append(hash_analysis)
    return hash_analyses


class VirusTotalAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up hashes in VirusTotal."""

  # TODO: Check if there are other file types worth checking VirusTotal for.
  DATA_TYPES = [u'pe:compilation:compilation_time']

  URLS = [u'https://virustotal.com']

  NAME = u'virustotal'

  _VIRUSTOTAL_NOT_PRESENT_RESPONSE_CODE = 0
  _VIRUSTOTAL_PRESENT_RESPONSE_CODE = 1
  _VIRUSTOTAL_ANALYSIS_PENDING_RESPONSE_CODE = -2

  def __init__(self):
    """Initializes a VirusTotal analysis plugin."""
    super(VirusTotalAnalysisPlugin, self).__init__(VirusTotalAnalyzer)
    self._api_key = None

  def EnableFreeAPIKeyRateLimit(self):
    """Configures Rate limiting for queries to VirusTotal.

    The default rate limit for free VirusTotal API keys is 4 requests per
    minute.
    """
    self._analyzer.hashes_per_batch = 4
    self._analyzer.wait_after_analysis = 60
    self._analysis_queue_timeout = self._analyzer.wait_after_analysis + 1

  def GenerateLabels(self, hash_information):
    """Generates a list of strings that will be used in the event tag.

    Args:
      hash_information (dict[str, object]): the JSON decoded contents of the
          result of a VirusTotal lookup, as produced by the VirusTotalAnalyzer.

    Returns:
      list[str]: strings describing the results from VirusTotal.
    """
    response_code = hash_information[u'response_code']
    if response_code == self._VIRUSTOTAL_NOT_PRESENT_RESPONSE_CODE:
      return [u'virustotal_not_present']
    elif response_code == self._VIRUSTOTAL_PRESENT_RESPONSE_CODE:
      positives = hash_information[u'positives']
      if positives > 0:
        return [u'virustotal_detections_{0:d}'.format(positives)]
      return [u'virsutotal_no_detections']
    elif response_code == self._VIRUSTOTAL_ANALYSIS_PENDING_RESPONSE_CODE:
      return [u'virustotal_analysis_pending']
    else:
      logging.error(
          u'VirusTotal returned unknown response code {0!s}'.format(
              response_code))
      return [u'virustotal_unknown_response_code_{0:d}'.format(response_code)]

  def SetAPIKey(self, api_key):
    """Sets the VirusTotal API key to use in queries.

    Args:
      api_key (str): VirusTotal API key
    """
    self._analyzer.SetAPIKey(api_key)


manager.AnalysisPluginManager.RegisterPlugin(VirusTotalAnalysisPlugin)
