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

## Scope

ridi-check runs on your machine. It calls the systems you point it at, writes files into the output
folder you choose, and makes no other network request. Reports are welcome on, for example:

- a results file, questions file or settings file that makes the tool run code or write outside the
  output folder;
- answer text that escapes the HTML report or the browser version and runs script;
- a key or token that ends up in a file the tool writes, when it was given through an environment
  variable.

Out of scope: the behaviour of the assistant under test, commands and Python functions that you configure
yourself (the tool runs what you tell it to run), and spreadsheet programs that treat a CSV cell starting
with `=` as a formula.
