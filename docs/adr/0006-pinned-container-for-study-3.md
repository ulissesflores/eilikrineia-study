# 0006. Study 3 ran in a container image pinned by digest

- Status: accepted
- Date: 2026-11-08

## Context

The pilot and studies 1 and 2 ran on the author's Mac, each trial in its own folder, with the global settings of
the agent client switched off (`--setting-sources ""`). The agents could still read the rest of the machine: the
home directory, its settings folders and the temporary parent folder common to every trial. Study 3 also needed the same
interpreter for every hidden check (one check depends on the standard library's `tomllib`, whose behaviour
differs between Python versions) and a way to state the environment exactly in the preregistration.

## Decision

Study 3 ran each trial in its own virtual machine, from one image pinned by digest:

- Apple `container` 1.6.1; image digest `sha256:48310dae…ec3c0`, recorded in the preregistration; base images
  pinned by digest in [`container/Containerfile`](../../container/Containerfile); Claude Code 2.1.319, Python
  3.11.18, `openssh-client` for the signing tool; a non-root user.
- 2 CPUs and 2 GB per trial; the hidden check runs in a second machine with no network.
- The study 3 ledger template was built inside the image, so no host path appears in it.
- Concurrency was set by a measured ramp: 30 machines at once lost the network, 20 ran clean.

## Alternatives considered

- **Keep running on the host.** Cheaper, but leaves the home directory and the common temporary parent folder readable.
- **Docker or Podman.** Neither was installed; Apple's runtime gives each container its own virtual machine.

## Consequences

- Study 3's rates are not expected to equal study 2's: the context is bare (about 3.3k tokens) and the ledger
  genesis is new. Arm S was run again inside study 3, so every contrast of study 3 is internal to it.
- Paths under `/home/agent/` in the study 3 transcripts are the container, not the author's machine.
- The host-run studies keep the exposure the container removed. Their transcripts show listings of the home
  directory, which were redacted before publication ([0008](0008-redact-log-audit.md)), and some show an agent
  reading temporary files left by another trial under that common temporary parent. How often that happened and
  whether it changed any outcome has not been assessed in this version; it is listed as a known limit in
  [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md).

## References

- [`PREREGISTRATION-STUDY3.md`](../../PREREGISTRATION-STUDY3.md), "Environment" and "Environment change against
  study 2"
- [`container/Containerfile`](../../container/Containerfile), [`runner/build_template3.sh`](../../runner/build_template3.sh)
