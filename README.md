# Archery Scorer

Counts your archery score from a few photos of the target taken from different angles, as few as it
needs, so you don't have to tally the arrows by hand.

Every feature is free. No ads, no account.

## Status

In development. The release pipeline uploads every release to Play's internal testing track, and the
home screen is an empty *Score an end* screen: scoring from a photo is not built yet. Whether a phone
can do it reliably is Phase 0's question ([`docs/phase-0.md`](docs/phase-0.md)).

## Contributing

Archery Scorer is source-available, not open source: read it, verify it, file issues. Pull requests are not
accepted — see [LICENSE](LICENSE).

## Build

```bash
./gradlew assembleDebug          # build
./gradlew installDebug           # build + install on the connected phone
./gradlew test                   # JVM unit tests
./gradlew connectedAndroidTest   # instrumented tests — needs a device
./gradlew spotlessApply          # format (the CI gate is spotlessCheck)
python3 scripts/project.py       # what the toolchain thinks this app is called
```

Commit subjects are [Conventional Commits](https://www.conventionalcommits.org); release-please
derives the version and `CHANGELOG.md` from them. See [docs/RELEASING.md](docs/RELEASING.md).
