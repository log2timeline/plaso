# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in Viper and tag events."""

import logging
import re

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.lib import errors


class ViperAnalyzer(interface.HTTPHashAnalyzer):
  """Class that analyzes file hashes by consulting Viper."""
  _VIPER_API_PATH = u'file/find'
  _SUPPORTED_PROTOCOLS = frozenset([u'http', u'https'])

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes a Viper hash analyzer.

    Args:
      hash_queue: A queue (instance of Queue.queue) that contains hashes to
                  be analyzed.
      hash_analysis_queue: A queue (instance of Queue.queue) that the analyzer
                           will append HashAnalysis objects to.
    """
    super(ViperAnalyzer, self).__init__(
        hash_queue, hash_analysis_queue, **kwargs)
    self._checked_for_old_python_version = False
    self._host = None
    self._protocol = None

  def SetHost(self, host):
    """Sets the Viper host that will be queried.

    Args:
      host: The Viper host to query.
    """
    self._host = host

  def SetProtocol(self, protocol):
    """Sets the protocol that will be used to query Viper.

    Args:
      protocol: The protocol to use to query Viper. Either 'http' or 'https'.

    Raises:
      ValueError: If an invalid protocol is specified.
    """
    protocol = protocol.lower().strip()
    if not protocol in self._SUPPORTED_PROTOCOLS:
      raise ValueError(u'Invalid protocol specified for Viper lookup')
    self._protocol = protocol

  def Analyze(self, hashes):
    """Looks up hashes in Viper using the Viper HTTP API.

    The API is documented here:
      https://viper-framework.readthedocs.org/en/latest/usage/web.html#api

    Args:
      hashes: A list of hashes (strings) to look up. The Viper plugin supports
              only one hash at a time.

    Returns:
      A list of hash analysis objects (instances of HashAnalysis).

    Raises:
      RuntimeError: If no host has been set for Viper.
      ValueError: If the hashes list contains a number of hashes other than
                      one.
    """
    if not self._host:
      raise RuntimeError(u'No host specified for Viper lookup.')

    if len(hashes) != 1:
      raise ValueError(
          u'Unsupported number of hashes provided. Viper supports only one '
          u'hash at a time.')
    sha256 = hashes[0]

    hash_analyses = []
    url = u'{0:s}://{1:s}/{2:s}'.format(
        self._protocol, self._host, self._VIPER_API_PATH)
    params = {u'sha256': sha256}
    try:
      json_response = self.MakeRequestAndDecodeJSON(url, u'POST', data=params)
    except errors.ConnectionError as exception:
      logging.error(
          (u'Error communicating with Viper {0:s}. Viper plugin is '
           u'aborting.').format(exception))
      self.SignalAbort()
      return hash_analyses

    hash_analysis = interface.HashAnalysis(sha256, json_response)
    hash_analyses.append(hash_analysis)
    return hash_analyses


class ViperAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up SHA256 hashes in Viper."""

  REQUIRED_HASH_ATTRIBUTES = [u'sha256_hash']

  # TODO: Check if there are other file types worth checking Viper for.
  DATA_TYPES = [u'pe:compilation:compilation_time']

  URLS = [u'https://viper.li']

  NAME = u'viper'

  REPLACEMENT_REGEX = re.compile(u'[^A-Za-z0-9_]')

  def __init__(self, event_queue):
    """Initializes a Viper analysis plugin.

    Args:
      event_queue: A queue that is used to listen for incoming events.
    """
    super(ViperAnalysisPlugin, self).__init__(event_queue, ViperAnalyzer)
    self._host = None

  def SetHost(self, host):
    """Sets the Viper host that will be queried.

    Args:
      host: The Viper host to query.
    """
    self._analyzer.SetHost(host)

  def SetProtocol(self, protocol):
    """Sets the protocol that will be used to query Viper.

    Args:
      protocol: The protocol to use to query Viper. Either 'http' or 'https'.

    Raises:
      ValueError: If an invalid protocol is selected.
    """
    protocol = protocol.lower().strip()
    if not protocol in [u'http', u'https']:
      raise ValueError(u'Invalid protocol specified for Viper lookup')
    self._analyzer.SetProtocol(protocol)

  def GenerateTagStrings(self, hash_information):
    """Generates a string that will be used in the event tag.

    Args:
      hash_information: A dictionary containing the JSON decoded contents of the
                        result of a Viper lookup, as produced by the
                        ViperAnalyzer.

    Returns:
      A list of strings describing the results from Viper.
    """
    if not hash_information:
      return u'File not present in Viper.'

    projects = []
    tags = []
    for project, entries in iter(hash_information.items()):
      if not entries:
        continue
      projects.append(project)
      for entry in entries:
        if entry[u'tags']:
          tags.extend(entry[u'tags'])
    if not projects:
      return [u'viper_not_present']
    strings = [u'viper_present']

    for project in projects:
      project_name = self.REPLACEMENT_REGEX.sub(u'_', project)
      strings.append(u'viper_project_{0:s}'.format(project_name))

    for tag in tags:
      tag_name = self.REPLACEMENT_REGEX.sub(u'_', tag)
      strings.append(u'viper_tag_{0:s}'.format(tag_name))

    return strings


manager.AnalysisPluginManager.RegisterPlugin(ViperAnalysisPlugin)
