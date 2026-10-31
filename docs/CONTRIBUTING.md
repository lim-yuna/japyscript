# Contributing to JapyScript

Small changes, clear motivation, tested outcome.

## Before you start

1. Read `docs/SPEC.md` and `docs/ARCHITECTURE.md`.
2. Search existing issues and pull requests.
3. For anything larger than a typo or a one-line bug fix, open an issue first.

## Ground rules

Every change ships a test. Every syntax addition ships a spec change.
The compiler is deterministic. No silent failures.

## Workflow

1. Fork the repository.
2. Create a branch named `feat/<topic>` or `fix/<topic>`.
3. Run `jpy test` and `jpy lint src/` from the repository root.
4. Open a pull request against `main`.

## Code of conduct

Be precise, be patient, be honest about what your code does and does not do.

## License

Contributions are MIT-licensed.
