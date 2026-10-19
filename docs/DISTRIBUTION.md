# Distribution qualification

GiadaWare AI is an unpublished, experimental `0.x` library. Packaging checks
establish artifact integrity and installability; they do not establish semantic
qualification of a capability/provider composition. See `ARCHITECTURE.md` and
`QUALIFICATION-ADMISSION.md` for those boundaries.

## Metadata and build requirements

The approved distribution is `giadaware-ai` version `0.0.2`, supports Python
`>=3.11`, uses
`setuptools.build_meta`, and has no mandatory runtime dependencies. The `dev`
extra is optional build tooling, not a prerequisite for consumer imports.

The declared setuptools minimum remains `>=68`. The license uses the
`{file = "LICENSE"}` form supported by that minimum, with explicit
`tool.setuptools.license-files`. SPDX string expressions and
`project.license-files` require setuptools >=77; adopting those fields would
require deliberately raising the build requirement. See the
[setuptools configuration reference](https://setuptools.pypa.io/en/stable/userguide/pyproject_config.html).

Setuptools 68 also requests `wheel` through its PEP 517 wheel-build requirements.
Provision it in a non-isolated build environment. Missing cached setuptools,
wheel, or a build frontend is an environment prerequisite, not proof that
package metadata is defective. Do not lower requirements to work around an
empty cache.

## License material

`LICENSE` contains the complete Apache License 2.0, including the appendix,
followed by the existing `Copyright 2026 GiadaWare` and license boilerplate.
No holder or attribution has been invented.

The complete text was copied from the local system's
`/usr/share/common-licenses/Apache-2.0`. Its MD5 matched the installed
`base-files` package manifest (`3b83ef96387f14655fc854ddc3c6bd57`); its SHA-256
was `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
The terms were also checked against the
[Apache Software Foundation reference](https://www.apache.org/licenses/LICENSE-2.0.txt).
These checksums describe the original reference text, before the retained
project attribution was appended.

No existing NOTICE file, bundled third-party code, or applicable third-party
notice was found in the distributed package during this audit. No new NOTICE
is required by that evidence: Apache section 4(d) requires preservation of
applicable notices when the work includes a NOTICE file, rather than a new
NOTICE for every Apache-licensed project. The packaging configuration includes
future `NOTICE*` files if they are introduced. Research and experiments are
outside the distribution; their scoped provenance is not changed.

Wheel and sdist qualification verifies the exact license bytes, retained
attribution, and `License-File` metadata. The wheel also includes `py.typed`.

## Offline qualification

From an active Python environment with already provisioned `build>=1.2`,
`setuptools>=68`, and `wheel`, run:

```bash
python scripts/qualify_distribution.py --output dist/qualification-UNIQUE-ID
```

This command does not download dependencies. The build frontend runs without
build isolation, using the recorded environment. If `build` is unavailable but
the backend requirements are installed, the explicit alternative is:

```bash
python scripts/qualify_distribution.py --backend-only --output dist/qualification-OTHER-UNIQUE-ID
```

The alternative invokes the declared setuptools PEP 517 hooks directly. It
does not verify frontend dependency resolution, build isolation, or the ability
of a separate offline cache to provision a builder. No mode silently falls back.

The gate:

1. Copies tracked and non-ignored untracked files into a temporary source
   snapshot outside the working checkout, leaving existing build products alone.
2. Builds a source distribution and a wheel from the snapshot.
3. Checks all package code, `py.typed`, metadata, license bytes, and sdist test
   inputs; rejects experimental and generated payloads.
4. Rebuilds a wheel from only the extracted sdist and requires byte equality
   with the source-built wheel, with a fixed `SOURCE_DATE_EPOCH`.
5. Installs each wheel with `--no-index --no-deps` into a separate fresh venv.
6. Runs public API smoke tests and the complete deterministic unit suite using
   the installed packages, isolated Python (`-I`), and a working directory
   outside the checkout. Ollama transport is mocked; no real inference runs.
7. Writes logs and provenance, including Git HEAD, dirty status, a source-file
   hash manifest, build tool versions, epoch, and hashes of actual artifacts.

The smoke tests execute schema-less and schema-constrained Ollama generation
through mocked transport, inspect `AIBackend.generate_json`, execute a synthetic
consumer subclass of `SynthesizeCapability`, exercise the typed `AIError`
family, construct `OllamaBackend`, and validate a facade result. A successful
import alone is insufficient.

Reproducibility is checked within the recorded Python/tool environment; this is
not a claim that arbitrary setuptools or Python versions produce identical
archives. The sdist itself is not claimed to be byte-reproducible.

## Artifact locations and retention

Use a new directory below the existing canonical `dist/` location for every
run. The gate refuses existing output directories and never overwrites earlier
artifacts. The repository already ignores `dist/`, `build/`, egg-info, venvs,
and bytecode; generated material remains untracked. Temporary source trees and
consumer environments are removed by the gate when it exits. Durable evidence
stays in `dist/`, not a home or temporary directory. Existing artifacts are not
deleted by this workflow.

CI retains the wheel, sdist, rebuilt wheel, log, and provenance with
`actions/upload-artifact`, including failure evidence. It provisions packaging
tools explicitly before the offline gate, following the existing networked CI
setup convention. Local provisioning still needs explicit authorization before
downloads.

## Version decision for U1–U4

At the start of this work, all of the following were observed:

- `pyproject.toml` declared `0.0.1`.
- No local release tags existed.
- `CHANGELOG.md` had only an `Unreleased` section.
- The semantic contract allowed intentional, documented `0.x` changes but did
  not specify patch/minor numbering or authorize a release increment.
- Public extension APIs and backend functionality had evolved under `0.0.1`.

Version **0.0.2 is approved for U3.1 local qualification** on 2026-10-19.
This decision authorizes the distribution version change and offline checks
only. Commit, tag, push, GitHub release, and PyPI publication remain
unauthorized. It introduces no general release policy or additional
compatibility commitment, and changes no runtime AI behavior.

The U3.1 canonical output directory is
`dist/upstream-u3-0.0.2-20261019`. Its artifacts are
**LOCAL UNCOMMITTED QUALIFICATION CANDIDATES**, built from the dirty working
tree rather than an immutable committed `0.0.2` source tree. `provenance.json`
records actual HEAD, dirty status, source-file manifest and hashes, build mode,
tools, and artifact SHA-256. `verification.json` records the candidate label,
source checks, qualification results, and remaining downstream requirements.
Retained logs provide the test counts and results.

The normal build frontend is preferred when installed. For this U3.1 run,
`build` and `pyproject-hooks` are unavailable; the already provisioned
setuptools and wheel support the documented explicit `--backend-only` mode.
No dependencies are downloaded or provisioned by this run. The frontend gate
remains BLOCKED by those missing tools; backend-only qualification does not
claim frontend or build-isolation coverage.

Earlier U1–U4 `0.0.1` artifacts remain internal qualification candidates only
and are preserved. They must not be published or supplied as interchangeable
replacements for other `0.0.1` builds. Identify all candidates by their run
directory, source manifest, and artifact SHA-256, not the version alone.

Before downstream LeLe Manager M4.2 consumption, require passing qualification
of the approved `0.0.2` candidate, review of its hashes and uncommitted source
provenance, explicit acceptance of that candidate or a separately authorized
committed build, and downstream validation of the optional dependency.
Publication would require separate authorization. No downstream repository is
changed by this gate.
