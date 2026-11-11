# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub:

1. Open the **Security** tab of this repository.
2. Choose **Report a vulnerability**.
3. Describe the problem, how to reproduce it and what an attacker could do with it.

This opens a private advisory that only the maintainers can see. Please do not open a public issue or
pull request for a vulnerability, and do not include real keys, tokens or personal data in a report.

There is no email address for security reports. If the **Report a vulnerability** button is not shown,
open a public issue that says only that you have a security report to make, with no details, and a
maintainer will open a private channel.

## What to expect

A maintainer will acknowledge the report, confirm whether it is a vulnerability, and tell you when a fix
is released. Fixes are made on the latest release only.

## Automated checks

CI runs [Bandit](https://bandit.readthedocs.io/) on `src/` and [pip-audit](https://pypi.org/project/pip-audit/)
on the package's dependencies. A finding of medium or high severity, or a known vulnerability in a
dependency the package needs to run, fails the build. Low-severity findings are listed and do not fail it.

Two findings are accepted on purpose and marked in the code:

- **A shell command is run** (`adapters.py`, Bandit B602). A `command:` system is a shell command that the
  owner of the assistant configures. Nothing read from the questions file is placed in it: the question is
  passed on standard input and the case id in an environment variable.
- **A URL is opened** (`adapters.py`, Bandit B310). The address of an `http` system must start with
  `http://` or `https://`; anything else is rejected before a request is made.

The low-severity notes are: the `subprocess` module is imported (it is needed for the above), a failure to
open a browser is ignored (the path of the report has already been printed), and the demo assistant uses
Python's ordinary random generator (for a repeatable example, not for anything secret). The package has no
runtime dependencies.

## Scope

ridi-check runs on your machine. It calls the systems you point it at, writes files into the output
folder you choose, and makes no other network request. Reports are welcome on, for example:

- a results file, questions file or settings file that makes the tool run code or write outside the
  output folder;
- answer text that escapes the HTML report or the browser version and runs script;
- a key or token that ends up in a file the tool writes or on the screen. The tool removes the values of
  credential headers, and of environment variables whose names say they are secrets, from what it
  records, also when a service repeats them in an error message; a credential written out in a
  definition file is left out of the manifest.

- a cell in a CSV file the tool writes that a spreadsheet program runs as a formula. Such cells are
  written with an apostrophe in front.

Out of scope: the behaviour of the assistant under test, and commands and Python functions that you
configure yourself (the tool runs what you tell it to run).
