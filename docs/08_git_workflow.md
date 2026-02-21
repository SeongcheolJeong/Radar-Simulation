# Git Workflow

## Repository Status

This project is now initialized as a Git repository.

## Branch Rule

- main: stable integration line
- feature branches: `codex/<short-topic>`

## Commit Rule

For each implementation step:

1. Code/doc change
2. Run corresponding validation command
3. Commit with validation scope in message

Examples:

- `feat(adapters): add HybridDynamicRT record adapter`
- `test(validation): add adapter smoke check`
- `docs(plan): add ffd integration checkpoints`

## Reference Repo Handling

- `external/*` sources are intentionally not tracked.
- `external/reference-locks.md` is tracked and records pinned local SHAs.

