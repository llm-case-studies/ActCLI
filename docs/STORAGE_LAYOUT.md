# Storage Layout Notes

Last updated: 2026-02-15

This repo keeps large Ollama model blobs off `/home` to avoid disk pressure.

## Current setup

- Logical path used by scripts and docs: `./models`
- Physical storage path: `/mnt/common/Projects/ActCLI/models`
- Bridge: `./models` is a symlink to `/mnt/common/Projects/ActCLI/models`

This preserves existing commands (no workflow changes):

- `scripts/ollama-local.sh`
- `scripts/fresh.sh`
- Any `OLLAMA_MODELS=./models` usage

## Why

- `/home` is on ext4 with limited capacity.
- `/mnt/common` has significantly more free space.
- Model blobs are large, replaceable artifacts and are safe to store off-repo.

## Verify

```bash
ls -ld ./models
realpath ./models
```

Expected: `./models` resolves to `/mnt/common/Projects/ActCLI/models`.

## Rollback

```bash
rm ./models
mkdir -p ./models
# repull models as needed
```

If you previously created a backup copy, restore it before re-pulling.
