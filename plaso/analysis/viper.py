# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in Viper and tag events."""

import logging

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.lib import errors


class ViperAnalyzer(interface.HTTPHashAnalyzer):
  """Class that analyzes file hashes by consulting Viper.

  REST API reference:
    https://viper-framework.readthedocs.org/en/latest/usage/web.html#api
  """

  SUPPORTED_HASHES = [u'md5', u'sha256']
  SUPPORTED_PROTOCOLS = [u'http', u'https']

  def __init__(self, hash_queue, digest_hash_recording_queue, **kwargs):
    """Initializes a Viper hash analyzer.

    Args:
      hash_queue (Queue.queue): that contains hashes to be analyzed.
      digest_hash_recording_queue (Queue.queue): that the analyzer will add
          resulting digest hash recording to.
    """
    super(ViperAnalyzer, self).__init__(
        hash_queue, digest_hash_recording_queue, **kwargs)
    self._checked_for_old_python_version = False
    self._host = None
    self._port = None
    self._protocol = None
    self._url = None

  def _QueryHash(self, digest):
    """Queries the Viper Server for a specfic hash.

    Args:
      digest (str): hash to look up.

    Returns:
      dict[str, object]: JSON response or None on error.
    """
    if not self._url:
      self._url = u'{0:s}://{1:s}:{2:d}/file/find'.format(
          self._protocol, self._host, self._port)

    request_data = {self.lookup_hash: digest}

    try:
      json_response = self.MakeRequestAndDecodeJSON(
          self._url, u'POST', data=request_data)

    except errors.ConnectionError as exception:
      json_response = None
      logging.error(u'Unable to query Viper with error: {0:s}.'.format(
          exception))

    return json_response

  def Analyze(self, digest_hashes):
    """Looks up hashes in Viper using the Viper HTTP API.

    Args:
      digest_hashes (list[str]): hashes to look up. The Viper plugin supports
          only one hash at a time.

    Returns:
      list[DigestHashRecording]: digest hash recordings.

    Raises:
      RuntimeError: If no host has been set for Viper.
      ValueError: If the hashes list contains a number of hashes other than one.
    """
    hash_analyses = []
    for digest in digest_hashes:
      json_response = self._QueryHash(digest)
      hash_analysis = interface.HashAnalysis(digest, json_response)
      hash_analyses.append(hash_analysis)

    return hash_analyses

  def SetHost(self, host):
    """Sets the address or hostname of the server running Viper server.

    Args:
      host (str): IP address or hostname to query.
    """
    self._host = host

  def SetPort(self, port):
    """Sets the port where Viper server is listening.

    Args:
      port (int): port to query.
    """
    self._port = port

  def SetProtocol(self, protocol):
    """Sets the protocol that will be used to query Viper.

    Args:
      protocol (str): protocol to use to query Viper. Either 'http' or 'https'.

    Raises:
      ValueError: if the protocol is not supported.
    """
    if protocol not in self.SUPPORTED_PROTOCOLS:
      raise ValueError(u'Unsupported protocol: {0!s}'.format(protocol))

    self._protocol = protocol

  def TestConnection(self):
    """Tests the connection to the Viper server.

    Returns:
      bool: True if the Viper server instance is reachable.
    """
    url = u'{0:s}://{1:s}:{2:d}/test'.format(
        self._protocol, self._host, self._port)

    try:
      json_response = self.MakeRequestAndDecodeJSON(url, u'GET')
    except errors.ConnectionError:
      json_response = None

    return json_response is not None


class ViperAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up SHA256 hashes in Viper."""

  # TODO: Check if there are other file types worth checking Viper for.
  DATA_TYPES = [u'pe:compilation:compilation_time']

  URLS = [u'https://viper.li']

  NAME = u'viper'

  def __init__(self):
    """Initializes a Viper analysis plugin."""
    super(ViperAnalysisPlugin, self).__init__(ViperAnalyzer)

  def SetHost(self, host):
    """Sets the address or hostname of the server running Viper server.

    Args:
      host (str): IP address or hostname to query.
    """
    self._analyzer.SetHost(host)

  def SetPort(self, port):
    """Sets the port where Viper server is listening.

    Args:
      port (int): port to query.
    """
    self._analyzer.SetPort(port)

  def SetProtocol(self, protocol):
    """Sets the protocol that will be used to query Viper.

    Args:
      protocol (str): protocol to use to query the Viper server, either
          'http' or 'https'.

    Raises:
      ValueError: If an invalid protocol is selected.
    """
    protocol = protocol.lower().strip()
    if protocol not in [u'http', u'https']:
      raise ValueError(u'Invalid protocol specified for Viper lookup')
    self._analyzer.SetProtocol(protocol)

  def TestConnection(self):
    """Tests the connection to the Viper server.

    Returns:
      bool: True if the Viper server instance is reachable.
    """
    return self._analyzer.TestConnection()


manager.AnalysisPluginManager.RegisterPlugin(ViperAnalysisPlugin)
