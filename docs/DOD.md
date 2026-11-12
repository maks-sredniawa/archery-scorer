# Definition of done — what is still open

The **live checklist**. Keep it short: when an item closes, tick it, write the *result* into whatever
long-form record you keep, and delete the detail from here. A session should be able to pick up the
work by reading this file alone.

## The standing schema gate — *parked*

**Parked 2026-11-11: the app has no database.** Room went in the strip (`optional-modules.md`), so
there is no `APP_SCHEMA_VERSION` to bump. The gate comes back, as written below, the day a feature
adds a table.

**An update must migrate an existing install without losing anything** (ADR-0001). This item does not
close. Whenever `APP_SCHEMA_VERSION` changes, all five hold before the release goes out:

1. `MIGRATION_x_y` written **and registered in** `APP_MIGRATIONS` for every step. A migration Room
   never runs is not a migration, and nothing about the build complains.
2. The exported `app/schemas/*/N.json` committed — every later migration is transcribed from it,
   never from the entity classes.
3. `SchemaGateTest` extended, so the **launch gate** is proven to let the upgrade through. Every
   migration test opens the database directly and walks past that gate; this assertion is the only
   thing standing in front of it.
4. A migration test proving the **rows survive** — read values back, do not merely assert nothing
   threw. `runMigrationsAndValidate` compares *shapes* and is blind to a table emptied by a cascading
   `DROP`.
5. **An actual upgrade watched on a phone**: install the previous build, put real data in it, install
   the new one over the top, confirm the app opens and the data is there.
   `./gradlew assembleDebug -PreleaseShapedDebug` is how to do this without touching a Play install —
   it is minified *and* `BuildConfig.DEBUG == false`, so migrations are registered rather than the
   destructive fallback. ⚠️ **Both halves are load-bearing**: a plain debug build takes the fallback
   and proves the opposite of what you wanted.

`scripts/schema-gate.py` enforces 1–3 mechanically in CI. Items 4 and 5 are yours.

## Before the first upload

- [x] **Delete what the app does not need.** Room, backup export/restore and reminders went 2026-11-11;
      photos and the tip stay.
- [x] **Decide `minSdk` deliberately, before launch.** Kept at 26 (owner, 2026-11-12). The direction is asymmetric: raising it later
      strands existing installs on the last build that fitted them, lowering it later is free. If the
      only phone in the loop sits at the top of the range, every `SDK_INT` branch below it ships
      unvalidated — the first app built from this template raised 26 to 33 for exactly that reason. Move CI's floor legs with it,
      and write the reason beside `minSdk` in `app/build.gradle.kts`, where the next person to touch it reads it.
- [ ] **Regenerate the feature graphic** with the Group mark: `python3 art/make-feature-graphic.py`,
      once the listing copy is written. Deferred to Phase N (`phase-0.md` section 4): the template's
      copy runs into the new mark.
- [x] **Replace the placeholder domain.** Items deleted 2026-11-11; the home screen is an empty
      **Score an end** screen.
- [x] **Rewrite `scripts/edge-to-edge.py`'s SCENES** against your screens. Rewritten in the strip;
      all 10 legs green on a dispatched run of `6b0ca73`, 2026-11-12
      ([run](https://github.com/maks-sredniawa/archery-scorer/actions/runs/43167927367)).
- [x] **Make the artifact allowlists yours.** All four `aab-*.py` scripts passed on a local
      `bundleRelease` of `6b0ca73`, 2026-11-12: three permissions (two from Play Billing, one from
      AndroidX), no features, no orientation locks, Polish complete.
- [x] **Choose the palette.** Range green, chosen 2026-11-11 (`phase-0.md` section 4).
- [ ] **Make the support address work both ways.** `bootstrap.py` compiled in
      `<repo>.support@maksforge.com` (or `--support`) and wrote it into the site, the privacy policy
      and the Play docs. Mail to it arrives through the domain's catch-all; replying from it needs the
      receiving Gmail's *Send mail as* entry, confirmed. Send *Report a problem* from a non-Gmail
      account and check it lands outside Spam. One address everywhere — the listing's contact field
      and IARC's rating contact too; `SupportHandoff.kt` says why it lives on our own domain.
      *Send mail as* confirmed and the signature set, 2026-11-12; the non-Gmail test is still owed.
- [x] **Write the listing.** `docs/store-listing.md`, English and Polish, 2026-11-12. Every heading in
      it is parsed by a script.
      The Console's *Review* step then asks for the AI-generated assets declaration: the owner's to make.
- [ ] **Capture the screenshots** with `scripts/screenshots.py` from a release-shaped build, in every
      listing language, into `art/play-screenshots/`. Play wants at least two before the first review.
- [ ] **Put the app on maksforge.com.** Its icon goes at `assets/icons/<repo>.webp` in
      maks-sredniawa/maks-sredniawa.github.io, which the app's own site loads, and the app goes on that home
      page. Replace `description` in `docs/_config.yml` too: it is the tagline under the app's name.
- [x] **Write the privacy policy** and confirm `maksforge.com/<repo>/privacy-policy`
      serves it. Written 2026-11-12; serving it is checked after the merge. Play requires a *hosted* URL, and an offline app has no server of its own.
- [ ] **Answer the Console's App content pages and write [`play-app-content.md`](play-app-content.md)
      in the same sitting** — the reasons are in front of you then and gone a week later. It moves in
      the same commit as the privacy policy, every time. Re-read *Target audience* after the content
      rating is submitted.
- [x] **`LICENSE` and `README.md`.** Source-available kept (owner, 2026-11-12). Bootstrap wrote a source-available notice and a *Contributing*
      that refuses pull requests, or with `--licence reserved` a notice that grants nothing and a
      placeholder. Keep both or replace both; they must agree.
- [x] **The upload keystore**, created and backed up 2026-11-12, and its four `UPLOAD_*` secrets
      set the same day: *The upload key* in `RELEASING.md`.
- [ ] **Set up the GitHub repository** — `python3 scripts/repo-setup.py` does the ruleset and the
      merge setting; the release-please PAT is the one step it cannot do, and without it no
      release PR is ever opened. *Setting up a new repository* in [`RELEASING.md`](RELEASING.md).
      **None of this is inherited from the template** — GitHub copies files, never settings — and
      the build stays green while it is all still undone. **Write the PAT's expiry date into this
      item** the day you create it: when it lapses the release PR simply stops appearing.
- [x] **Create the service account and set `PLAY_SERVICE_ACCOUNT_JSON`**, 2026-11-12:
      `archery-scorer-play-ci` in its own Cloud project `archery-scorer-play`, invited with no
      account permissions, the two app permissions on this app only, and no expiry date.
- [x] **Plan the closed test.** Recruiting testers is not a concern for this app (owner, 2026-11-12). A new personal developer account reaches production only after a
      closed test — at the time of writing 12 testers opted in for 14 continuous days, then an access
      application. Recruit the testers before the build is ready, not after; `publish-play-closed.yml`
      moves each build to them. A tester-swap community, where developers test each other's closed
      tests, filled the apps built from this template within days. Testers: internal is the email
      list `only-me-Tester`, every closed test both groups `testers-community@googlegroups.com` and
      `maks-forge-testers@googlegroups.com` — never a per-app group or list. **The first closed
      release of a never-published app is made in the Console**; the workflow takes over after its approval ([`RELEASING.md`](RELEASING.md)).
- [x] **Decide the `applicationId` deliberately.** `com.maksforge.archeryscorer`, fixed by the Play
      entry created 2026-11-12 (default listing language en-US, free).

## The tip — open until a real purchase is consumed

ADR-0007. The code is in; these are the parts only Play and a phone can prove. The steps are
*Selling the tip* in [`RELEASING.md`](RELEASING.md).

- [x] **Keep it or delete it, before the first upload.** Kept (owner, 2026-11-11).
- [ ] **A build with billing on internal testing**, then the four products created and active.
      The build is there: 0.2.0, uploaded by `publish-play.yml` on 2026-11-12.
- [ ] **One purchase from a licence tester** on the internal install, ending in the thank-you line,
      and the *same* tip bought again — the second purchase is the proof that the first was consumed.
- [ ] **The debug build shows no tip section and no card.** Play has never heard of the `.debug`
      package, so absent is the correct reading, not a failure.
- [ ] **Content rating re-submitted** with *digital purchases* Yes, before production.

## Before the next upload

Re-declarations a change owes Play, written down the day the change merges and ticked when the
Console matches. A new permission, foreground service or data type is a Console change that waits in
*Publishing overview* for *Send for review* with the upload that needs it. Empty most of the time.

## After the closed test

- [ ] **The production-access application is in, with its answers recorded verbatim** in
      [`play-app-content.md`](play-app-content.md). Until it is granted the production track does not
      exist. The app this template was extracted from waited one day; that is one datapoint, not a
      promise. **If it comes back rejected, read the reason before changing any artifact.** Changing
      the build first leaves you arguing the reason against a different build.
- [ ] **Add the production countries in the Console** — *Test and release → Production → Countries /
      regions*. A new app's production track targets none, the API cannot add them, and a dry run
      does not catch it ([`RELEASING.md`](RELEASING.md)).
- [ ] **Decide the first production number.** release-please never jumps to `1.0.0` by itself (with
      the major at 0 even `feat!:` bumps the minor), so it takes a `Release-As: 1.0.0` footer
      ([`RELEASING.md`](RELEASING.md)), or a deliberate decision to stay on 0.x. In order: production
      access granted, *then* that version's release notes in every locale on an ordinary branch (never
      on release-please's own, which it force-pushes), *then* the AAB and the listing go up together.

## Standing checks that never close

- [ ] **Every release: run the artifact checks on the built AAB**, not on the source.
      `aab-permissions.py` is the one that finds what a *dependency* merged into your manifest —
      a permission you never declared, or a `uses-feature` that quietly filters the app off devices.
- [ ] **Every release: read the release notes gate's output** rather than trusting it passed.
- [ ] **Every Play declaration: confirm Data safety still holds** against
      [`play-app-content.md`](play-app-content.md), and write the date of the re-read here.
- [ ] **Every dependency bump: re-run `licensee`.** The build fails on an unallowed licence, which is
      the point — but the fix is two things, the allowlist *and* the bundled text.
- [ ] **Test the release-shaped build on a device.** A missing R8 keep rule does not crash; it makes
      a feature silently stop working.
