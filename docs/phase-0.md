# Phase 0 — photo scoring is proven possible on a desk, and the template is cut down to the app

Sequence lives in [`PLAN.md`](PLAN.md); the live worklist lives in [`DOD.md`](DOD.md). This phase
reopens ADR-0001 (Room), ADR-0002 (photos), ADR-0003 (reminders) and ADR-0005 (backup), and keeps
ADR-0007's *`INTERNET` stays out*: photos are scored on the phone and never leave it.
[`CONTEXT.md`](../CONTEXT.md) gets its first domain terms: **End**, **Arrow**, **Face**, **View**,
**Entry point**, **Line cutter**.

**What closing this phase means.** Today the repo is the android-starter template with a placeholder
*Item* domain, and nobody has measured whether a phone photo can be scored. After this phase a desk
experiment on real photos of a real end has named one of three verdicts, the modules the app does not
need are gone, and the palette and mark are chosen. Asked of a device: the debug build opens on an
empty *Score an end* screen, and a throwaway script has scored a photographed end against the holes
the same arrows left, with the error in millimetres written down below.

---

## 0. What this phase inherits

- **The owner is an archer** (owner, 2026-11-11), so the gate's photos come from a real boss, face and
  arrows, but not today. The apparatus is therefore built and checked first, on a rendered end, so
  the reading is one run on the day the photos exist.
- **Others already do this.** Arrow Tempo (on-device, the archer confirms every end, $59.99 a year
  for Pro) and ArrowMind (real-time camera scoring, offline) ship camera scoring of arrows in the
  target. Neither is open source. What this app adds is the MaksForge shape: free, offline, no
  account, no subscription. That is the pitch to keep honest in the listing, not "the first".
- **The best published accuracy is 1.4–1.8 mm** (Shepherd 2026, arXiv 2604.16758, holes on a 40 cm
  face; Kim, Moon & Lee 2025, a 122 cm face). A 40 cm face's rings are 2 cm wide and its dividing
  lines up to 2 mm, so a line cutter can sit inside that error. No system scores alone: World
  Archery's own three-camera RyngDyng reaches about 1 mm and judges still confirm. **The app proposes
  and the archer confirms.** That is a product rule, not a fallback.
- **Parallax does not move the entry point.** The shaft enters the face in the face's own plane, so
  one view's ring homography maps it correctly *when it is visible*. A second view is needed for two
  other reasons: a nock hides the entry point in a straight-on photo, and a shaft seen in two views can
  be triangulated and met with the face plane without the entry point being visible at all. That is
  what *"as few photos as it needs"* means here: ask for another angle until every arrow is resolved in
  two views.
- **The template's camera path needs no permission.** `TakePicture` hands the shot to the system
  camera, and `scripts/aab-permissions.py` forbids `CAMERA` because declaring it changes the listing.
  A guided capture (a live overlay saying *"step left"*) would need CameraX and `CAMERA`. Phase 1
  decides; this phase only writes the trade-off down.
- **`applicationId` is `com.maksforge.archeryscorer`**, written by bootstrap. Nothing reached Play
  yet, so it can still change; it freezes the day the Play entry exists.

## What is in, and what is deliberately not

**In:** the gate (section 1), the module strip it implies (section 2), the first face (section 3),
the palette and mark, and the vocabulary.

**Not in, and each with a reason rather than a phase:**

- Any vision code in `main/`. The gate's apparatus is a throwaway Python script outside the app; the
  first on-device detector belongs to Phase 1, whose whole point is that one mechanism.
- A trained model. It needs a few hundred labelled photos of our own (no public dataset labels entry
  points on a World Archery face), and the gate decides whether classical vision is enough first.
- Holes after the arrows are pulled. Archers score with the arrows still in the target, and a face
  with old holes in it cannot tell this end's holes from the last one's. The holes are used once, here,
  as the experiment's ground truth.
- The pipeline (repository settings, keystore, Play entry). Its own phase (`PLAN.md` rule 2).

**The tempting one is "it scores without me checking".** Every published system is within a line's
width of being wrong on a 40 cm face. An app that silently gets one line cutter wrong per round
teaches the archer to stop trusting it, and then it saves nothing. Every arrow is shown on a drawing of
the face and can be moved, added or removed, and any arrow within about 2 mm of a line is flagged.

---

## Checkpoints

| | Checkpoint | Merges | Depends on |
| --- | --- | --- | --- |
| **A** | **The gate**: can a few handheld photos of an end be scored to within 1.5 mm, automatically or nearly so? | `docs:` the verdict here | photos of a real end |
| **B** ✅ | **The strip**: delete the modules section 2 names, amend their ADRs | `refactor:` | owner's yes on section 2 |
| **C** ✅ | **The first face** and the scoring rules it needs, as written rules (section 3). Decided (owner, 2026-11-11) | `docs:` | owner's answer on the face |
| **D** ✅ | **Palette and mark** | `feat:` | — |
| **E** ✅ | **The placeholder domain becomes an empty *Score an end* screen** | `feat:` | B |

A goes first because verdict 3 vetoes the app as pitched. B waits only on the owner, not on A: none
of the modules it removes is needed by any verdict.

---

## 1. The gate: can a phone score an end from a few photos?

### The question, in the form that can be measured

*With six arrows in a real face on a boss (two of them on a line, three in a tight group), and three
handheld phone photos from about 1 m (one straight on, two at about ±35°): do the rings fit
automatically in every view, and is the median distance between each arrow's computed entry point and
the hole it leaves at most 1.5 mm?*

### The apparatus

[`tools/gate/`](../tools/gate/), on OpenCV (Apache 2.0, the same library the app would use). It is
committed rather than kept in a scratchpad because the photos arrive in a later session; it never
ships in the app, and the photos stay out of git (`tools/gate/runs/` is ignored). `synth.py` renders a
fake end with known entry points, `click.py` collects the clicks on real photos, `gate.py` takes the
reading, and `test_gate.py` holds all three to account:

1. Segment the colour zones in Lab colour space and fit an ellipse to the outer edge of the gold,
   red and blue regions, per view, each searched only inside the one around it. The face plane comes
   from the red and blue edges: in a straight-on photo the fletchings cover most of the gold, and
   fletchings in gold or red would otherwise pass for rings. Report each ring's residual in mm. The
   Lab thresholds are tuned on the rendered colours; real light may need them moved, which is itself
   a finding.
2. Two points per shaft per view: clicked by hand first, then tried with OpenCV's line segment
   detector to see whether they can be found automatically. When a view hides the entry point (a
   nock in front of it), the near click goes on the lowest point of the shaft that shows and `h`
   marks it *entry hidden*. `gate.py` counts the hidden entries per view (R3) and splits the front
   photo's error into visible and hidden entries (R2).
3. Triangulate each shaft from two views against the face plane (intrinsics from EXIF, or from
   decomposing the ring homography) and compare that with the single-view tip.
4. Pull the arrows, photograph the holes straight on, and use them as ground truth.

### The verdicts, decided now rather than argued about later

*The rings fit* in a photo when the red and blue edges each sit within 1.0 mm RMS of their nominal
circles (`RING_FIT_MAX_RMS_MM` in `gate.py`, beside the 1.5 mm pass line). The verdicts read it over
the three views only. The holes photo is checked against the same line, but it decides only whether
the ground truth can be used: if its rings do not fit, the run gives no reading and the holes photo
is retaken.

1. **Rings fit automatically in all three views, two-view error ≤ 1.5 mm, shafts found
   automatically in most views.** → Phase 1 builds it on the phone with classical vision: OpenCV on
   device, rings fitted per view, shafts detected and triangulated, the archer confirming. Another
   photo is asked for only while some arrow is seen in fewer than two views. A trained model is a later
   phase, fed by the archer's own corrections if they agree to keep them.
2. **Rings fit, but shafts are not found reliably.** → Phase 1 still rectifies the face from the
   photos, but the archer taps each arrow's entry point on the straightened face, zoomed in. The app
   does the arithmetic (zones, line cutters with the shaft's radius, X count, the end total), which is
   still the tally the idea removes. Automatic shaft detection becomes its own phase with a trained
   model, and its licence is chosen then: never Ultralytics YOLO (AGPL-3.0, and so is every model
   trained with it), which conflicts with this repo's `LICENSE`.
3. **The rings do not fit reliably** from handheld photos. → The app as pitched does not work. Stop
   and bring the choice to the owner: the archer taps the face's centre and edge to straighten it, a
   printed marker beside the face, or park the idea.

### The dry run, on a rendered end (2026-11-11)

`uv run --script tools/gate/synth.py tools/gate/runs/synth` then `gate.py` on it: a 40 cm face, six
5.5 mm shafts tilted up to 9°, the *near* click 12 mm up each shaft, 1 px click noise, JPEG at 92.
Red and blue fit to 0.15–0.24 mm RMS in all four photos; gold only in the two the fletchings do not
cover (0.5–0.7 mm against 7–10 mm). Entry error against the holes: front photo alone median 1.21 mm,
worst 2.82 mm; two or three views median 0.85 mm, worst 1.60 mm, and one of the six scored a zone low.
The worst two-view arrows are those whose shaft planes meet the face at a narrow angle (15° and
27°), so a fourth photo should be asked for by that angle, not by count. `synth.py` marks no entry
hidden, so the run's R3 is zero in every view. This proves the arithmetic,
not the method: a rendered face has perfect colours, a flat sheet and straight shafts.

### The verdict, taken *(date)*

*(Not yet: it needs the photos.)*

## 2. The strip: what goes, decided against the app's shape

`optional-modules.md` lists the files. **Owner said yes on 2026-11-11 and the strip is done**: the
app scores one end at a time and keeps no rounds or history. `spotlessCheck test lint assembleDebug`,
`translation-gate.py`, `schema-gate.py` (*no database, nothing to gate*), the scripts' unit tests and
all four `aab-*.py` checks on a release-shaped `bundleDebug` passed on the branch; `bundleRelease`
needs the upload key, which does not exist yet.

The androidTest set is now `MediaFilesTest` alone: `ItemDaoTest`, `MigrationTest`,
`ManifestWiringTest` and `ShareChosenCallbackTest` went with Room, the reminders and the backup
share. It keeps CI's instrumented job above zero tests.

The tip's one ask now counts **ends scored** (`ends_scored` in `AppPreferences`), and nothing counts
one until Phase 1 scores an end.

| Module | Decision | Why |
| --- | --- | --- |
| Room and the schema gate | **Delete** | The idea scores an end; it keeps no rounds or history. If the owner wants rounds kept, Room stays instead: a round is ends joined to arrows, which is what a table is for. |
| Photos (media pipeline) | **Keep** | The app takes photos. `TakePicture` and the `FileProvider` are the capture path until Phase 1 decides on CameraX. Whether photos are kept after scoring is Phase 1's call; the default is to delete them once the end is confirmed. `MediaKind.Photo` in `MediaFiles` downsamples to a 2048 px long edge and strips EXIF, while the scorer needs full resolution and the camera's focal length from EXIF for millimetre precision, so Phase 1 captures for scoring outside that path or extends it. |
| Backup export/restore | **Delete**; Auto Backup takes over | Nothing to back up without history. Comes back with Room if rounds are kept. |
| Reminders and WorkManager | **Delete** | No schedules in the idea. |
| The tip | **Keep** | As in every MaksForge app. Its ask moves to the *Score an end* screen. |
| Placeholder domain | **Replace** with an empty *Score an end* screen (E) | |

## 3. The first face

**Decision (owner, 2026-11-11):** the single-spot ten-ring World Archery face, with the size as a
parameter. 122, 80, 60 and 40 cm are the same ten equal rings at different scales (ring width 6.1,
4, 3 and 2 cm), so one implementation covers outdoor and indoor. After it, the 80 cm six-ring face, then the vertical triple
spot with the compound inner ten. Field, 3D and non-WA faces are not in this plan.

The rules the scoring function must get right, from World Archery Book 2 Art. 7.2.2 and Book 3
Art. 12.2 (2026-01-27 versions):

- Dividing lines are at most 2 mm wide and belong wholly to the higher zone.
- **Line cutter:** a shaft touching a line or two colours takes the higher value. So the score is
  taken from the distance to the shaft's centre *minus the shaft's radius*, and the shaft diameter
  (at most 9.3 mm) is a setting the archer gives once.
- **X:** the inner ten (6.1 cm on the 122 cm face, 4 cm on the 80 cm face) counts only for ties, so
  it is shown as a count beside the total.
- **Compound on 60 and 40 cm faces:** only the inner ten scores 10; the rest of the gold scores 9.
- **Triple spot:** outside the blue 6 is a miss, and with two arrows in one spot only the lower
  scores; the other is a miss.
- A torn line is judged as the ideal circle. Robin Hoods, bounce-outs and pass-throughs are entered
  by hand.

## 4. Palette and mark

**Owner chose option A on 2026-11-11**, from three a Fable design pass drew up (range green,
graphite, violet). Not branded.

- **Palette:** seeds primary `2F6B4A` (range green), secondary `5C6E63` (grey-green), tertiary
  `7A5C8E` (heather, the *moved by hand* marker), neutral `E2E5E1` (near-grey). Green is the one hue
  with a reason to be here, and the furthest from the face's gold, red and blue; a warm neutral
  would lean to the gold and a blue-grey to the blue ring. All of `gen_scheme.py`'s contrast checks
  pass.
- **Mark:** the Group, three arrow holes in a tight group inside a ring (`art/README.md`). Its
  known weakness is that at a glance it can pass for a bowling ball; if that shows on a home screen,
  move the holes further off-centre before changing the idea.
- **A rule for every phase that draws arrows on the face:** no brand colour reaches 3:1 against every
  zone. The primary (tone 40) is under 2:1 against the face's red; the light container tones reach
  about 3.4–3.9:1 against the red but sit near 1:1 on the gold. So an arrow marker on the face always
  carries a white and black keyline, never brand colour alone.
- The feature graphic is left for Phase N: regenerated with this mark, the template's copy runs into
  it, and the listing copy is not written yet.

---

## Tests

None in this phase: no app code computes a score yet. The scoring function arrives in Phase 1 with its
tests, because it is this app's safety value: a line cutter scored low, a compound gold scored 10, a
second arrow in a triple spot scored. Each one fails in the direction the archer cannot see.

## Documents this phase amends

ADR-0001, 0003, 0005 and 0007 (each a dated amendment on the strip), ADR-0002 (a dated note that
it stays), `CONTEXT.md`, `CLAUDE.md`'s stack
table and layout, the privacy policy and `play-app-content.md` (photos are taken and scored on the
device, never uploaded).

## Known gaps, deliberately

- One archer, one face, one light: the experiment proves the method, not every range. Outdoor light,
  a worn face and paper that moved on impact are Phase 1's readings on the phone.
- Arrows touching in a tight group are unsolved in every published system. The app flags them for the
  archer rather than claim them.

## Sources

Read for this phase on 2026-11-11.

- Shepherd 2026, holes on a 40 cm face, MIT code and annotations, no released weights:
  [arXiv 2604.16758](https://arxiv.org/abs/2604.16758),
  [repo](https://github.com/maxwellshepherd/frozen_vision_transformers_for_archery_scoring)
- Kim, Moon & Lee 2025, a 122 cm face outdoors: DOI 10.1177/17543371251406361
- Parag 2017, one fixed camera, homography from the ring colours, Hough lines for the shaft:
  [thesis](https://theses.liacs.nl/pdf/RaymondParag.pdf)
- OnTarget, two fixed cameras: [arXiv 2104.01622](https://arxiv.org/pdf/2104.01622)
- DeepDarts, keypoints from one camera: [arXiv 2105.09880](https://arxiv.org/abs/2105.09880)
- RyngDyng at Tokyo: [World Archery](https://www.worldarchery.sport/news/200459/automatic-camera-arrow-spotting-makes-olympic-debut-tokyo)
- Arrow Tempo: [arrowtempo.com](https://arrowtempo.com); ArrowMind: [arrowmindai.com](https://arrowmindai.com)
- World Archery rules, 2026-01-27:
  [Book 2](https://extranet.worldarchery.sport/documents/index.php/Rules/Rule_Book_versions/2026-01-27/EN-Book_2_-_2026-01-27_Version.pdf),
  [Book 3](https://extranet.worldarchery.sport/documents/index.php/Rules/Rule_Book_versions/2026-01-27/EN-Book_3_-_2026-01-27_Version.pdf)
- On-device: [LiteRT](https://developers.google.com/edge/litert),
  [OpenCV licence](https://github.com/opencv/opencv/blob/4.x/LICENSE),
  [Ultralytics licence](https://www.ultralytics.com/license)

## Readings

| # | Reading | Command | Result |
| --- | --- | --- | --- |
| R1 | Rings fit automatically in each of the three views, with the residual in mm | `uv run --script tools/gate/gate.py tools/gate/runs/<date>` after `click.py` | *(not taken)* |
| R2 | Median and worst entry-point error against the holes: front view alone (split into visible and hidden entries) against two views | the same run | *(not taken)* |
| R3 | How many of the six entry points each view hides | the same run's R3 table, from the near clicks marked `h` in `click.py` | *(not taken)* |
| R4 | Shafts found automatically by the line segment detector, out of 18 | not built yet: added once R1–R3 are read | *(not taken)* |
