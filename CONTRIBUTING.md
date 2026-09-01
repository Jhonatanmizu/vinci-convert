# Contributing to Vinci Convert

Thanks for helping out! This project is **GPL-3.0** and includes logic ported from
[davinconv](https://github.com/gohny/davinconv) (GPL-3.0, by Gohny). Read the
whole file before contributing; it covers the license, the CLA, and branding.

## Ground rules

- Python ≥ 3.11, managed with `uv`.
- Code style follows the existing files (no black/isort config yet — match the neighborhood).
- Every new source file should carry the GPL-3.0 header:

  ```python
  # SPDX-License-Identifier: GPL-3.0-or-later
  # Copyright (C) <year> <your name> — released under the GNU GPL v3 or later.
  ```

- Don't import or copy code from other projects without checking it's compatible
  with GPL-3.0.

## Development workflow

```bash
git clone https://github.com/jhonatanmizu/vinci-convert.git
cd vinci-convert
uv sync            # create .venv and install dependencies
uv run vinci-convert --help
uv run vinci-convert-gui
```

Run inline tests before opening a PR. There is no test suite yet — keep manual
checks documented in the PR description.

## Contributor License Agreement (CLA)

By submitting a pull request, you agree to the following terms. **Please paste
them into your PR body** (this is a hard requirement for merging):

> ## Contributor License Agreement
>
> I agree to license my contributions to **Vinci Convert** under the terms of
> the **GNU General Public License, version 3** (or any later version, at the
> project's option).
>
> I represent that the contribution is my own original work and that I have the
> right to license it under these terms. If I am contributing on behalf of an
> employer or organization, I confirm that they authorize the contribution.
>
> I understand that:
> - The project is distributed under GPL-3.0 and my contributions are subject
>   to that license.
> - The project maintainer may, **with the written consent of all copyright
>   holders** (including upstream [davinconv](https://github.com/gohny/davinconv)
>   author Gohny where their code is involved), relicense this project in the
>   future without further permission from me.
> - I will not rename or claim authorship of upstream (davinconv) code I did
>   not write.
>
> **Contributor name:** `<your name>`
> **Date:** `<date>`

### Why this CLA?

The repo's `converter.py` is derived from davinconv (GPL-3.0). Relicensing in
the future (e.g. to open-core) requires consent from **every** copyright holder.
The clause above lets the maintainer relicense **your** contributions if an
upstream agreement is ever reached — without making you re-sign later.

## Trademark policy

"Vinci Convert" and the logo are used to identify the official project.

- **Allowed:** saying "powered by Vinci Convert", linking to the repo, and
  distributing unmodified GPL binaries under the name.
- **Not allowed:** publishing *modified* forks under the "Vinci Convert" name
  (read: mark them as a fork), or using the name/logo to sell third-party
  services or products without written permission.
- The **paid service tiers** (Supporter / Studio, when available) are the only
  commercial use of the brand — see the [monetization strategy].

[monetization strategy]: https://github.com/jhonatanmizu/vinci-convert/blob/main/docs/monetization-strategy.md

## Code of Conduct

Be kind. Video post-production is hard — this project exists to make it easier.
Harassment and discrimination have no place here.