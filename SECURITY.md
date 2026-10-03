# Security policy

## Supported versions

Security fixes are made on the `main` branch and ship in the next release.
Plaso uses date-based release versions (for example `20260928`); only the
latest release is supported.

## Reporting a vulnerability

Please do not report security vulnerabilities through public GitHub issues,
pull requests or discussions.

Report them privately through GitHub instead:

1. Go to the [Security tab](https://github.com/log2timeline/plaso/security) of
   this repository.
2. Select **Report a vulnerability** to open a private security advisory.

Please include:

* the affected Plaso version or commit;
* the tool involved (`log2timeline`, `psort`, `psteal`, `pinfo` or
  `image_export`) and the command line used;
* a minimal input that reproduces the issue, such as a small crafted file or
  storage image, or a description of how to build one;
* the observed and expected behavior, and the impact you see.

The maintainers will acknowledge the report, work with you on a fix in the
private advisory, and credit you in the advisory unless you prefer otherwise.

## Scope

Plaso processes evidence that may have been created or tampered with by an
attacker. Examples of issues that are in scope:

* a crafted file, file system or storage media image that makes a tool crash
  as a whole, hang, or use unbounded memory or CPU (an error recorded as an
  extraction warning for that one file is expected behavior);
* crafted input that makes Plaso silently produce wrong forensic results, such
  as shifted timestamps or events attributed to the wrong source, user or path;
* code execution, path traversal (for example in `image_export`) or writes
  outside the intended output location;
* output that can inject content into downstream tools, such as formula
  injection in CSV or XLSX output.

Vulnerabilities in dependencies, such as dfVFS or the libyal libraries, should
be reported to those projects. If you are not sure where an issue belongs,
report it here and it will be routed.
