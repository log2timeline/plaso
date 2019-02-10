# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in VirusTotal and tag events."""

from __future__ import unicode_literals

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.lib import errors


class VirusTotalAnalyzer(interface.HTTPHashAnalyzer):
  """Class that analyzes file hashes by consulting VirusTotal."""

  _VIRUSTOTAL_API_REPORT_URL = (
      'https://www.virustotal.com/vtapi/v2/file/report')

  _EICAR_SHA256 = (
      '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f')

  SUPPORTED_HASHES = ['md5', 'sha1', 'sha256']

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes a VirusTotal analyzer.

    Args:
      hash_queue (Queue.queue): queue that contains hashes to be analyzed.
      hash_analysis_queue (Queue.queue): queue the analyzer will append
          HashAnalysis objects to.
    """
    super(VirusTotalAnalyzer, self).__init__(
        hash_queue, hash_analysis_queue, **kwargs)
    self._api_key = None
    self._checked_for_old_python_version = False

  def _QueryHashes(self, digests):
    """Queries VirusTotal for a specfic hashes.

    Args:
      digests (list[str]): hashes to look up.

    Returns:
      dict[str, object]: JSON response or None on error.
    """
    url_parameters = {'apikey': self._api_key, 'resource': ', '.join(digests)}

    try:
      json_response = self.MakeRequestAndDecodeJSON(
          self._VIRUSTOTAL_API_REPORT_URL, 'GET', params=url_parameters)
    except errors.ConnectionError as exception:
      json_response = None
      logger.error('Unable to query VirusTotal with error: {0!s}.'.format(
          exception))

    return json_response

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
      raise RuntimeError('No API key specified for VirusTotal lookup.')

    hash_analyses = []

    json_response = self._QueryHashes(hashes) or []

    # VirusTotal returns a dictionary when a single hash is queried
    # and a list when multiple hashes are queried.
    if isinstance(json_response, dict):
      json_response = [json_response]

    for result in json_response:
      resource = result['resource']
      hash_analysis = interface.HashAnalysis(resource, result)
      hash_analyses.append(hash_analysis)

    return hash_analyses

  def SetAPIKey(self, api_key):
    """Sets the VirusTotal API key to use in queries.

    Args:
      api_key (str): VirusTotal API key
    """
    self._api_key = api_key

  def TestConnection(self):
    """Tests the connection to VirusTotal

    Returns:
      bool: True if VirusTotal is reachable.
    """
    json_response = self._QueryHashes([self._EICAR_SHA256])
    return json_response is not None


class VirusTotalAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up hashes in VirusTotal."""

  # TODO: Check if there are other file types worth checking VirusTotal for.
  DATA_TYPES = ['pe:compilation:compilation_time']

  URLS = ['https://virustotal.com']

  NAME = 'virustotal'

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
    response_code = hash_information['response_code']
    if response_code == self._VIRUSTOTAL_NOT_PRESENT_RESPONSE_CODE:
      return ['virustotal_not_present']

    if response_code == self._VIRUSTOTAL_PRESENT_RESPONSE_CODE:
      positives = hash_information['positives']
      if positives > 0:
        return ['virustotal_detections_{0:d}'.format(positives)]

      return ['virsutotal_no_detections']

    if response_code == self._VIRUSTOTAL_ANALYSIS_PENDING_RESPONSE_CODE:
      return ['virustotal_analysis_pending']

    logger.error(
        'VirusTotal returned unknown response code {0!s}'.format(
            response_code))
    return ['virustotal_unknown_response_code_{0:d}'.format(response_code)]

  def SetAPIKey(self, api_key):
    """Sets the VirusTotal API key to use in queries.

    Args:
      api_key (str): VirusTotal API key
    """
    self._analyzer.SetAPIKey(api_key)

  def TestConnection(self):
    """Tests the connection to VirusTotal

    Returns:
      bool: True if VirusTotal is reachable.
    """
    return self._analyzer.TestConnection()


manager.AnalysisPluginManager.RegisterPlugin(VirusTotalAnalysisPlugin)
