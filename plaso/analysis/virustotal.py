# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in VirusTotal and tag events."""

import logging

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import hashes
from plaso.lib import errors


class VirusTotalAnalyzer(interface.HTTPHashAnalyzer):
  """Class that analyzes file hashes by consulting VirusTotal.

  For more information see about the VirusTotal API see:
  https://www.virustotal.com/en/documentation/public-api/#getting-file-scans
  """

  _VIRUSTOTAL_API_REPORT_URL = (
      u'https://www.virustotal.com/vtapi/v2/file/report')

  _VIRUSTOTAL_RESPONSE_CODE_NOT_PRESENT = 0
  _VIRUSTOTAL_RESPONSE_CODE_PRESENT = 1
  _VIRUSTOTAL_RESPONSE_CODE_ANALYSIS_PENDING = -2

  def __init__(self, hash_queue, digest_hash_recording_queue, **kwargs):
    """Initializes a VirusTotal Analyzer thread.

    Args:
      hash_queue (Queue.queue): that contains hashes to be analyzed.
      digest_hash_recording_queue (Queue.queue): that the analyzer will add
          resulting digest hash recording to.
    """
    super(VirusTotalAnalyzer, self).__init__(
        hash_queue, digest_hash_recording_queue, **kwargs)
    self._api_key = None
    self._checked_for_old_python_version = False

  def SetAPIKey(self, api_key):
    """Sets the VirusTotal API key to use in queries.

    Args:
      api_key (str): VirusTotal API key
    """
    self._api_key = api_key

  def Analyze(self, digest_hashes):
    """Looks up hashes in VirusTotal using the VirusTotal HTTP API.

    The API is documented here:
      https://www.virustotal.com/en/documentation/public-api/

    Args:
      digest_hashes (list[str]): digest hashes to look up.

    Returns:
      list[DigestHashRecording]: digest hash recordings.

    Raises:
      RuntimeError: If the VirusTotal API key has not been set.
    """
    if not self._api_key:
      raise RuntimeError(u'No API key specified for VirusTotal lookup.')

    resource_string = u', '.join(digest_hashes)
    params = {u'apikey': self._api_key, u'resource': resource_string}
    try:
      json_response = self.MakeRequestAndDecodeJSON(
          self._VIRUSTOTAL_API_REPORT_URL, u'GET', params=params)
    except errors.ConnectionError as exception:
      logging.error((
          u'Error communicating with VirusTotal {0:s}. VirusTotal plugin is '
          u'aborting.').format(exception))
      self.SignalAbort()
      return []

    # The content of the response from VirusTotal has a different structure
    # if one or more than one hash is looked up at once. Hence we wrap a
    # single in a list.
    if isinstance(json_response, dict):
      json_response = [json_response]

    digest_hash_recordings = []
    for json_file_report in json_response:
      resource = json_file_report.get(u'resource', None)
      if not resource:
        logging.warning(u'Resource missing in file report.')
        continue

      response_code = json_file_report.get(u'response_code', None)
      found_in_library = None
      if response_code == self._VIRUSTOTAL_RESPONSE_CODE_NOT_PRESENT:
        found_in_library = False
        label = u'virustotal_not_present'
      elif response_code == self._VIRUSTOTAL_RESPONSE_CODE_PRESENT:
        found_in_library = True

        positives = json_file_report.get(u'positives', 0)
        if positives > 0:
          label = u'virustotal_detections_{0:d}'.format(positives)
        else:
          label = u'virsutotal_no_detections'
      elif response_code == self._VIRUSTOTAL_RESPONSE_CODE_ANALYSIS_PENDING:
        found_in_library = True
        label = u'virustotal_analysis_pending'
      elif response_code is not None:
        logging.warning(u'Unsupported response code: {0!s}'.format(
            response_code))
        label = u'virustotal_unknown_response_code_{0!s}'.format(response_code)

      digest_hash_recording = hashes.DigestHashRecording(
          digest_hash=resource, found_in_library=found_in_library,
          library=u'VirusTotal')
      digest_hash_recording.labels = [label]
      digest_hash_recordings.append(digest_hash_recording)

    return digest_hash_recordings


class VirusTotalAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up hashes in VirusTotal."""

  # TODO: Check if there are other file types worth checking VirusTotal for.
  DATA_TYPES = [u'pe:compilation:compilation_time']

  URLS = [u'https://virustotal.com']

  NAME = u'virustotal'

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

  def SetAPIKey(self, api_key):
    """Sets the VirusTotal API key to use in queries.

    Args:
      api_key (str): VirusTotal API key
    """
    self._analyzer.SetAPIKey(api_key)


manager.AnalysisPluginManager.RegisterPlugin(VirusTotalAnalysisPlugin)
