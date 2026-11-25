# Security Policy

This project does not consider minor code weaknesses, vulnerabilities. Minor code weaknesses can be
reported as regular issues.

## What is considered a vulnerability

This project reserves the term "vulnerability" for issues that would allow remote access or other
types of critical weaknesses, in line with the following definition:

> A vulnerability is a weakness or flaw in computer code, system architecture, or network design
> that a malicious actor (or hacker) can exploit to gain unauthorized access or cause damage.

Plaso is intended to be used inside a lab environment where other controls are in place and access
is limited. Issues that require an actor who already has authorized access to that environment,
such as a local user on the analysis host or the person running the tools, are not considered
vulnerabilities. Such issues, and other undesirable behavior such as parsing edge cases, can be
reported as regular issues or addressed with a pull request.

### Third-party reporting policy

This project does not recognize Mitre, NIST, or any third-party CVE Numbering Authority (CNA) as
authoritative sources for vulnerability reports due to ongoing deficiencies in quality assurance,
transparency, and accountability within the CVE program.

Consequently, the project actively disputes any vulnerability claim or CVE assignment that has not
been explicitly verified and confirmed directly with the project’s maintainers. Until the broader
CVE ecosystem addresses these systemic shortcomings, the project will rely solely on its own
internal verification and advisory process, to evaluate and validate potential security weaknesses
and inform its users.

## Reporting an actual vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**

If you discover an actual security vulnerability within this project, please report it privately to
the maintainers. This allows us to coordinate a fix and protect users before the flaw is made
public.

A finding by a fuzzer or other type of security tool is **not necessarily** a security
vulnerability. Make sure to include an analysis of what makes the finding an actual vulnerability.

### How to Report

You can report vulnerabilities through one of the following methods:

1. **Email:** Send a detailed report to log2timeline-maintainers at googlegroups.com

### What to Include

Please include:

* A description of the vulnerability and its impact. Do not speculate about impact, and make sure
  to include your impact analysis. No need to include CVSS scores.
* Step-by-step instructions to reproduce the issue, including any specific test data or
  configurations. 
  * Report in text, no screenshots or videos.
  * Make sure to include a working proof-of-concept (POC).
  * Add integrity hashes of the files.
* Any proposed fixes, patches, or mitigations.
