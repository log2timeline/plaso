# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in nsrlsvr and tag events."""

import logging
import socket

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.lib import errors

class NsrlsvrAnalyzer(interface.HashAnalyzer):

  _NSRL_ADDRESS = u'127.0.0.1'
  _NSRL_PORT = 9120

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes a VirusTotal Analyzer thread.

    Args:
      hash_queue: A queue (instance of Queue.queue) that contains hashes to
                  be analyzed.
      hash_analysis_queue: A queue (instance of Queue.queue) that the analyzer
                           will append HashAnalysis objects to.
    """
    super(NsrlsvrAnalyzer, self).__init__(
        hash_queue, hash_analysis_queue, **kwargs)


  def Analyze(self, hashes):
    """Looks up hashes in VirusTotal using the VirusTotal HTTP API.

    The API is documented here:
      https://www.virustotal.com/en/documentation/public-api/

    Args:
      hashes: A list of hashes (strings) to look up.

    Returns:
      A list of HashAnalysis objects.

    Raises:
      RuntimeError: If the VirusTotal API key has not been set.
    """
    hash_analyses = []
    # Open a socket
    nsrl_socket = socket.create_connection((self._NSRL_ADDRESS, self._NSRL_PORT))
    # look through queries
    for hash in hashes:
      query = u'QUERY {0:s}'.format(hash)
      nsrl_socket.sendall(query)
      response = nsrl_socket.recv()
      if response.split(u' ')[1] == u'1':
        hash_analysis = interface.HashAnalysis(hash, True)
        hash_analyses.append(hash_analysis)
      else:
        hash_analysis = interface.HashAnalysis(hash, False)
        hash_analyses.append(hash_analysis)
    return hash_analyses

class NsrlsvrAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up hashes in nsrlsvr."""
  # nsrlsvr allows lookups using any of these hash algorithms.
  REQUIRED_HASH_ATTRIBUTES = [u'sha256_hash']

  DATA_TYPES = [u'pe:compilation:compilation_time']

  URLS = [u'https://rjhansen.github.io/nsrlsvr/']

  NAME = u'nsrlsvr'

  def __init__(self, event_queue):
    """Initializes a VirusTotal analysis plugin.

    Args:
      event_queue: A queue that is used to listen for incoming events.
    """
    super(NsrlsvrAnalysisPlugin, self).__init__(
        event_queue, NsrlsvrAnalysisPlugin)


  def GenerateTagStrings(self, hash_information):
    """Generates a list of strings that will be used in the event tag.

    Args:
      hash_information: A dictionary containing the JSON decoded contents of the
                        result of a VirusTotal lookup, as produced by the
                        VirusTotalAnalyzer.

    Returns:
      A list of strings describing the results from VirusTotal.
    """
    if hash_information:
      return u'nsrl_present'
    return u'nsrl_not_present'

manager.AnalysisPluginManager.RegisterPlugin(NsrlsvrAnalysisPlugin)
