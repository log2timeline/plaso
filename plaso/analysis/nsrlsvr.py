# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in nsrlsvr and tag events."""

import logging
import socket

from plaso.analysis import interface
from plaso.analysis import manager


class NsrlsvrAnalyzer(interface.HashAnalyzer):
  """Class that analyzes file hashes by consulting an nsrlsvr instance."""
  _RECEIVE_BUFFER_SIZE = 4096
  _SOCKET_TIMEOUT = 3

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes an nsrlsvr analyzer thread.

    Args:
      hash_queue (Queue.queue):  contains hashes to be analyzed.
      hash_analysis_queue (Queue.queue): that the analyzer will append
          HashAnalysis objects this queue.
    """
    super(NsrlsvrAnalyzer, self).__init__(hash_queue, hash_analysis_queue,
        **kwargs)
    self._host = None
    self._port = None
    self.hashes_per_batch = 100

  def Analyze(self, hashes):
    """Looks up hashes in nsrlsvr.

    Args:
      hashes (list[str]):  hashes to look up.

    Returns:
      list[HashAnalysis]: analysis results.
    """
    hash_analyses = []
    # Open a socket
    logging.debug(
        u'Opening connection to {0:s}:{1:d}'.format(self._host, self._port))
    try:
      nsrl_socket = socket.create_connection((self._host, self._port),
          self._SOCKET_TIMEOUT)
    except socket.error as exception:
      logging.error(
        (u'Error communicating with nsrlsvr {0:s}. nsrlsvr plugin is '
         u'aborting.').format(exception))
      self.SignalAbort()
      return hash_analyses
    for digest in hashes:
      query = u'QUERY {0:s}\n'.format(digest)
      try:
        nsrl_socket.sendall(query)
        response = nsrl_socket.recv(self._RECEIVE_BUFFER_SIZE)
      except socket.error as exception:
        logging.error(
          (u'Error communicating with nsrlsvr {0:s}. nsrlsvr plugin is '
           u'aborting.').format(exception))
        self.SignalAbort()
        return hash_analyses
      if response.split(u' ')[1] == u'1':
        hash_analysis = interface.HashAnalysis(digest, True)
        hash_analyses.append(hash_analysis)
      else:
        hash_analysis = interface.HashAnalysis(digest, False)
        hash_analyses.append(hash_analysis)
    nsrl_socket.close()
    return hash_analyses

  def SetHost(self, host):
    """Sets the address or hostname of the server running nsrlsvr.

    Args:
      host (str): IP address or hostname to query.
    """
    self._host = host

  def SetPort(self, port):
    """Sets the port where nsrlsvr is listening.

    Args:
      port (int): port to query.

    """
    self._port = port


class NsrlsvrAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up hashes in nsrlsvr."""
  # nsrlsvr allows lookups using any of these hash algorithms.
  REQUIRED_HASH_ATTRIBUTES = [u'sha256_hash', u'md5_hash']

  # The NSRL contains files of all different types, and can handle a high load
  # so look up all files.
  DATA_TYPES = [u'fs:stat', u'fs:stat:ntfs']

  URLS = [u'https://rjhansen.github.io/nsrlsvr/']

  NAME = u'nsrlsvr'

  def __init__(self, event_queue):
    """Initializes an nsrlsvr analysis plugin.

    Args:
      event_queue (Queue.queue)): queue of events to analyze.
    """
    super(NsrlsvrAnalysisPlugin, self).__init__(event_queue, NsrlsvrAnalyzer)

  def GenerateTagStrings(self, hash_information):
    """Generates a list of strings that will be used in the event tag.

    Args:
      hash_information (bool): whether the analyzer received a response from
          nsrlsvr indicating that the hash was present in its loaded nsrl
          version.

    Returns:
      list[str]: strings describing the results from nsrlsvr.
    """
    if hash_information:
      return [u'nsrl_present']
    return [u'nsrl_not_present']

  def SetHost(self, host):
    """Sets the address or hostname of the server running nsrlsvr.

    Args:
      host (str): IP address or hostname to query.
    """
    self._analyzer.SetHost(host)

  def SetPort(self, port):
    """Sets the port where nsrlsvr is listening.

    Args:
      port (int): port to query.
    """
    self._analyzer.SetPort(port)


manager.AnalysisPluginManager.RegisterPlugin(NsrlsvrAnalysisPlugin)
