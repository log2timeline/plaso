# -*- coding: utf-8 -*-
"""The hashlookup_bloom analysis plugin CLI arguments helper."""

from plaso.analysis import hashlookup_bloom
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class HashlookupBloomAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Hashlookup Bloom analysis plugin CLI arguments helper."""

  NAME = 'hashlookup_bloom'
  CATEGORY = 'analysis'
  DESCRIPTION = 'Argument helper for the hashlookup_bloom analysis plugin.'

  _DEFAULT_BLOOM_DATABASE_PATH = "hashlookup-full.bloom"
  _DEFAULT_HASH = 'sha1'
  _DEFAULT_LABEL = hashlookup_bloom.HashlookupBloomAnalysisPlugin.DEFAULT_LABEL
  _SUPPORTED_HASHES = sorted(
      hashlookup_bloom.HashlookupBloomAnalysisPlugin.SUPPORTED_HASHES)

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser): group
          to append arguments to.
    """
    argument_group.add_argument(
        '--hashlookup-bloom-hash', '--hashlookup_bloom_hash',
        dest='hashlookup_bloom_hash', type=str, action='store',
        choices=cls._SUPPORTED_HASHES, default=cls._DEFAULT_HASH,
        metavar='HASH', help=(
            'Type of hash to use to query bloom file'
            '(hash are capitalized), the default is: '
            '{0:s}. Supported options: {1:s}'.format(
                cls._DEFAULT_HASH, ', '.join(cls._SUPPORTED_HASHES))))

    argument_group.add_argument(
        '--hashlookup-bloom-file', '--hashlookup_bloom_file',
        dest='hashlookup_bloom_file', type=str, action='store',
        default=cls._DEFAULT_BLOOM_DATABASE_PATH, metavar='PATH',
        help=(
            'Path to the bloom file, the '
            'default is: {0:s}').format(cls._DEFAULT_BLOOM_DATABASE_PATH))

    argument_group.add_argument(
        '--hashlookup-bloom-label', '--hashlookup_bloom_label',
        dest='hashlookup_bloom_label', type=str,
        action='store', default=cls._DEFAULT_LABEL, metavar='LABEL', help=(
            'Label to apply to events, the default is: {0:s}.').format(
                cls._DEFAULT_LABEL))

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options object.
      analysis_plugin (HashlookupBloomAnalysisPlugin): analysis plugin
        to configure.

    Raises:
      BadConfigObject: when the analysis plugin is the wrong type.
      BadConfigOption: when unable to load the bloom file.
    """
    if not isinstance(analysis_plugin,
      hashlookup_bloom.HashlookupBloomAnalysisPlugin):
      raise errors.BadConfigObject(
          'Analysis plugin is not an instance of HashlookupBloomAnalysisPlugin')

    label = cls._ParseStringOption(
        options, 'hashlookup_bloom_label', default_value=cls._DEFAULT_LABEL)
    analysis_plugin.SetLabel(label)

    lookup_hash = cls._ParseStringOption(
        options, 'hashlookup_bloom_hash', default_value=cls._DEFAULT_HASH)
    analysis_plugin.SetLookupHash(lookup_hash)

    hashlookup_bloom_file = cls._ParseStringOption(
        options, 'hashlookup_bloom_file',
        default_value=cls._DEFAULT_BLOOM_DATABASE_PATH)
    analysis_plugin.SetBloomDatabasePath(hashlookup_bloom_file)

    if not analysis_plugin.TestLoading():
      raise errors.BadConfigOption(
          'Unable to load bloom file {0:s}'.format(hashlookup_bloom_file))


manager.ArgumentHelperManager.RegisterHelper(
  HashlookupBloomAnalysisArgumentsHelper)
