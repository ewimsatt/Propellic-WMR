# Propellic Content Hygiene Toolkit

[![CI](https://github.com/ewimsatt/Propellic-WMR/actions/workflows/ci.yml/badge.svg)](https://github.com/ewimsatt/Propellic-WMR/actions/workflows/ci.yml)

A local-first toolkit for preparing client-owned copy and files for publication.

Propellic works with travel and tourism brands where content moves through a lot of hands, systems, and formats. This project helps teams inspect that material, remove supported provenance metadata and hidden Unicode artifacts, and make deliberate edits before publishing.

It runs on your machine. It does not upload files. It does not promise to fool a vendor detector. It gives you a clear report of what it found and what it changed.

> Use this only for content you own or are authorized to process. It is not for academic fraud, deceptive attribution, or bypassing platform policy.

## What it does

| Job | What the toolkit can do |
| --- | --- |
| Review text | Surface hidden Unicode characters, look-alike spaces, bidi controls, tag characters, and selected confusables. |
| Clean text | Remove or normalize supported edit-based artifacts while preserving normal text and supported script or emoji glue by default. |
| Review files | Inspect supported images and documents for C2PA, EXIF, XMP, document properties, and other provenance-related metadata. |
| Clean files | Create a cleaned copy of supported PNG, JPEG, WebP, SVG, PDF, DOCX, ODT, HTML, and Markdown files. |
| Rewrite carefully | Generate a local prompt or use an explicitly configured rewrite backend for a best-effort Layer B rewrite. |
| Work without a terminal | Run the local desktop app to inspect, clean, save copies, and manage backups. |

## Start here

### Desktop app

Python 3.10 or later is the only requirement for the core app.

```bash
git clone https://github.com/ewimsatt/Propellic-WMR.git
cd Propellic-WMR
python3 gui/launch.py
```

The app binds to `127.0.0.1`, uses a per-session token for its API, and keeps files on the local machine.

- **macOS:** double-click `gui/Propellic-WMR.command`
- **Windows:** double-click `gui/PropellicWMR.bat`
- **Linux:** run `python3 gui/launch.py`

See [the desktop app guide](gui/README.md) for screenshots, supported workflows, and troubleshooting.

### Command line

```bash
SCRIPTS=skills/remove-ai-marks/scripts

# Inspect text before changing it.
python3 "$SCRIPTS/inspect_text.py" draft.md

# Write a cleaned copy. The original stays untouched.
python3 "$SCRIPTS/clean_text.py" draft.md -o draft.cleaned.md --stats

# Inspect and clean a file container.
python3 "$SCRIPTS/inspect_file.py" brief.docx
python3 "$SCRIPTS/clean_file.py" brief.docx -o brief.cleaned.docx
```

## How to use the results

The toolkit separates three different problems that often get lumped together.

| Layer | Purpose | Confidence |
| --- | --- | --- |
| **Layer A: text hygiene** | Finds and removes supported invisible Unicode, tags, bidi controls, and space variants. | Deterministic and reported as counts. |
| **Layer B: rewrite** | Changes wording to reduce statistical text-watermark signals. | Best effort only. Rewriting can change voice, meaning, and quality. |
| **File provenance** | Removes supported C2PA, EXIF, XMP, and document metadata from supported formats. | The tool reports the container operations it performed. |

Start with inspection. Prefer the smallest change that solves the actual problem. For editorial work, that usually means Layer A or metadata cleanup, not a full rewrite.

## Supported formats

| Format | Inspection | Cleanup |
| --- | --- | --- |
| Markdown and plain text | Unicode artifacts and supported frontmatter signals | Text cleanup and supported frontmatter cleanup |
| HTML and SVG | Metadata and text artifacts | Supported metadata, attributes, and text cleanup |
| PNG, JPEG, WebP | C2PA and supported metadata segments | Re-encoded output without supported metadata segments |
| PDF | Metadata and available tool output | Best results require `exiftool` and `qpdf` |
| DOCX and ODT | Document properties and supported metadata | Document-property cleanup; optional text cleanup in the desktop app |

The project also includes optional, externally installed research integrations for SynthID scoring, CtrlRegen, and MarkLLM. They are off by default and documented in the [full skill](skills/remove-ai-marks/SKILL.md).

## Skills for Cursor and Codex

The repository includes two skill packages:

- [`clean-user-facing-text`](skills/clean-user-facing-text/) for editorial cleanup of authorized copy in Cursor and Codex
- [`remove-ai-marks`](skills/remove-ai-marks/) for the broader text, image, document, and metadata workflows

Install the lightweight text skill:

```bash
python3 install_skill.py cursor
python3 install_skill.py codex
python3 install_skill.py all
```

The installer copies the skill into your local skills directory and will not replace an existing installation unless you pass `--force`. A forced replacement creates a backup first.

For project-level setup, see:

- [Cursor rule snippet](integrations/cursor/clean-user-facing-text.mdc)
- [Codex AGENTS.md snippet](integrations/codex/AGENTS.md.snippet)
- [Full skill documentation](skills/remove-ai-marks/SKILL.md)

## Local-first and security model

- Core workflows use Python's standard library.
- The desktop app listens only on loopback and protects its API with a session token.
- File cleaners write to a new destination by default. In-place cleanup creates a backup first.
- Rewrite API keys are read from `WATERMARKS_REWRITE_API_KEY`, never from command-line arguments.
- Remote rewrite endpoints require an explicit opt-in.
- Optional tools and model integrations are not bundled into this repository.

Read [SECURITY.md](SECURITY.md) to report a vulnerability responsibly.

## Limits and editorial judgment

This project cannot certify that a third-party detector will fail. It cannot remove every kind of image, audio, video, or statistical watermark. C2PA soft binding and many pixel-domain marks are outside the core guarantee.

A clean report means the tool found no supported signal in the selected workflow. It does not make a claim about every possible provenance or detection system.

For production travel content, retain the original file, review the diff or report, and make sure the final copy still says what the client means.

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest
make smoke
```

The test suite covers the core text cleaners, supported file handling, installer behavior, and the local GUI server.

## Project docs

| Document | Use it for |
| --- | --- |
| [Desktop app guide](gui/README.md) | Running the app and managing local files |
| [Full skill](skills/remove-ai-marks/SKILL.md) | Advanced CLI use, optional integrations, and workflow details |
| [Coverage matrix](skills/remove-ai-marks/references/removal-matrix.md) | Format and signal coverage |
| [Responsible-use guidance](skills/remove-ai-marks/references/ethics.md) | Scope, limitations, and acceptable use |
| [Security policy](SECURITY.md) | Reporting vulnerabilities |

## License

[MIT](LICENSE)
