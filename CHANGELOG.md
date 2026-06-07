# Changelog

All notable changes are logged here — for humans **and** agents.
Format follows [Keep a Changelog](https://keepachangelog.com/). Newest first.

## [Unreleased]

### Removed

- `plugins/sos/workflows/goal-10x.js` — the old multi-agent goal-10x workflow. Once the `sos`
  plugin is installed it surfaced as a second `/sos:goal-10x` entry that collided with the
  consolidated `/goal-10x` command ("one loop, two gears", commit #15), reintroducing the exact
  "two competing loops" that consolidation removed. Its parallel multi-agent capability lives on
  as the **parallel gear** (`/sos:ship-loop` → `lavish`/`treehouse`/`no-mistakes`), so nothing is
  lost. _Why:_ keep a single front door — one goal-10x, no divergent duplicate.

### Added

- `plugins/sos/scripts/install-goal-10x.sh` — one-command, idempotent cross-machine
  installer for `/goal-10x`. Registers the `wjlgatech/sos` marketplace, installs the `sos`
  plugin at user scope, and symlinks `~/.claude/commands/goal-10x.md` to the live plugin
  command so both the bare `/goal-10x` and namespaced `/sos:goal-10x` work on any machine and
  stay in sync via `claude plugin marketplace update`. _Why:_ `~/.claude` has no Anthropic-cloud
  sync, so the git-backed marketplace is the supported way to carry the command across computers;
  the symlink restores the bare name a plugin install can't provide on its own.
