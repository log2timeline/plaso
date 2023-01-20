# -*- coding: utf-8 -*-
"""MacOS OpenDirectory helper."""


class ODMBRIdHelper(object):
  """OpenDirectory MBR ID helper.

  See:
/Library/Developer/CommandLineTools/SDKs/MacOSX12.3.sdk/usr/include/membership.h

  """
  _OD_MBRID_TYPES = {
      0: 'UID',
      1: 'GID',
      3: 'SID',
      4: 'USERNAME',
      5: 'GROUPNAME',
      6: 'UUID',
      7: 'GROUP NFS',
      8: 'USER NFS',
      10: 'GSS EXPORT NAME',
      11: 'X509 DN',
      12: 'KERBEROS'}

  @classmethod
  def GetType(cls, code):
    """Retrieves the description for a specific type.

    Args:
      code (int): type code

    Returns:
      str: name of the type code.
    """
    return cls._OD_MBRID_TYPES.get(code, 'UNKNOWN: {0:d}'.format(code))


class ODErrorsHelper(object):
  """OpenDirectory errors helper.

  See:
    https://developer.apple.com/documentation/opendirectory/odframeworkerrors?changes=__2&language=objc

  """

  _OD_ERRORS = {
      0: 'ODErrorSuccess',
      2: 'Not Found',
      1000: 'ODErrorSessionLocalOnlyDaemonInUse',
      1001: 'ODErrorSessionNormalDaemonInUse',
      1002: 'ODErrorSessionDaemonNotRunning',
      1003: 'ODErrorSessionDaemonRefused',
      1100: 'ODErrorSessionProxyCommunicationError',
      1101: 'ODErrorSessionProxyVersionMismatch',
      1102: 'ODErrorSessionProxyIPUnreachable',
      1103: 'ODErrorSessionProxyUnknownHost',
      2000: 'ODErrorNodeUnknownName',
      2001: 'ODErrorNodeUnknownType',
      2002: 'ODErrorNodeDisabled',
      2100: 'ODErrorNodeConnectionFailed',
      2200: 'ODErrorNodeUnknownHost',
      3000: 'ODErrorQuerySynchronize',
      3100: 'ODErrorQueryInvalidMatchType',
      3101: 'ODErrorQueryUnsupportedMatchType',
      3102: 'ODErrorQueryTimeout',
      4000: 'ODErrorRecordReadOnlyNode',
      4001: 'ODErrorRecordPermissionError',
      4100: 'ODErrorRecordParameterError',
      4101: 'ODErrorRecordInvalidType',
      4102: 'ODErrorRecordAlreadyExists',
      4103: 'ODErrorRecordTypeDisabled',
      4104: 'ODErrorRecordNoLongerExists',
      4200: 'ODErrorRecordAttributeUnknownType',
      4201: 'ODErrorRecordAttributeNotFound',
      4202: 'ODErrorRecordAttributeValueSchemaError',
      4203: 'ODErrorRecordAttributeValueNotFound',
      5000: 'ODErrorCredentialsInvalid',
      5001: 'ODErrorCredentialsInvalidComputer',
      5100: 'ODErrorCredentialsMethodNotSupported',
      5101: 'ODErrorCredentialsNotAuthorized',
      5102: 'ODErrorCredentialsParameterError',
      5103: 'ODErrorCredentialsOperationFailed',
      5200: 'ODErrorCredentialsServerUnreachable',
      5201: 'ODErrorCredentialsServerNotFound',
      5202: 'ODErrorCredentialsServerError',
      5203: 'ODErrorCredentialsServerTimeout',
      5204: 'ODErrorCredentialsContactPrimary',
      5205: 'ODErrorCredentialsServerCommunicationError',
      5300: 'ODErrorCredentialsAccountNotFound',
      5301: 'ODErrorCredentialsAccountDisabled',
      5302: 'ODErrorCredentialsAccountExpired',
      5303: 'ODErrorCredentialsAccountInactive',
      5304: 'ODErrorCredentialsAccountTemporarilyLocked',
      5305: 'ODErrorCredentialsAccountLocked',
      5400: 'ODErrorCredentialsPasswordExpired',
      5401: 'ODErrorCredentialsPasswordChangeRequired',
      5402: 'ODErrorCredentialsPasswordQualityFailed',
      5403: 'ODErrorCredentialsPasswordTooShort',
      5404: 'ODErrorCredentialsPasswordTooLong',
      5405: 'ODErrorCredentialsPasswordNeedsLetter',
      5406: 'ODErrorCredentialsPasswordNeedsDigit',
      5407: 'ODErrorCredentialsPasswordChangeTooSoon',
      5408: 'ODErrorCredentialsPasswordUnrecoverable',
      5500: 'ODErrorCredentialsInvalidLogonHours',
      6000: 'ODErrorPolicyUnsupported',
      6001: 'ODErrorPolicyOutOfRange',
      10000: 'ODErrorPluginOperationNotSupported',
      10001: 'ODErrorPluginError',
      10002: 'ODErrorDaemonError',
      10003: 'ODErrorPluginOperationTimeout'}

  @classmethod
  def GetError(cls, code):
    """Retrieves the description for a specific error code.

    Args:
      code (int): error code

    Returns:
      str: name of the error code.
    """
    return cls._OD_ERRORS.get(code, 'UNKNOWN: {0:d}'.format(code))
