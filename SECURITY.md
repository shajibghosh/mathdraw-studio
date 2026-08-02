# Security Policy

## Supported version

Security corrections are applied to the latest released version.

| Version | Supported |
|---|---|
| 0.2.x | Yes |
| Earlier versions | No |

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose local files, execute unintended commands, corrupt exported data, or create unsafe handling of image/document inputs.

Use GitHub's private vulnerability reporting feature when it is enabled. Otherwise, contact the repository owner privately through the contact method shown on the owner's GitHub profile. Include:

- affected version and operating system;
- input format and minimal reproduction steps;
- observed and expected behavior;
- potential impact;
- a proposed correction, when available.

## Security scope

MathDraw Studio processes user-selected files locally. Particular attention is given to image decoders, PDF/SVG conversion tools, LaTeX/Pandoc subprocesses, path handling, and very large coefficient exports. Users should keep Python packages, Pandoc, Tectonic, and external image decoders updated and should avoid processing untrusted files in privileged environments.
