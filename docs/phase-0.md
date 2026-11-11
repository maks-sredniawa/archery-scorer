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
| **B** | **The strip**: delete the modules section 2 names, amend their ADRs | `refactor:` | owner's yes on section 2 |
| **C** | **The first face** and the scoring rules it needs, as a written table (section 3) | `docs:` | owner's answer on the face |
| **D** | **Palette and mark** | `feat:` | — |
| **E** | **The placeholder domain becomes an empty *Score an end* screen** | `feat:` | B |

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

A Python script in the scratchpad, never committed, on OpenCV (Apache 2.0, the same library the app
would use):

1. Segment the colour zones in Lab colour space and fit an ellipse to each zone boundary, per view.
   Report the ring residual in mm. The black/white and blue/black boundaries have no printed line and
   may not fit: record which ones do.
2. Two points per shaft per view: clicked by hand first, then tried with OpenCV's line segment
   detector to see whether they can be found automatically.
3. Triangulate each shaft from two views against the face plane (intrinsics from EXIF, or from
   decomposing the ring homography) and compare that with the single-view tip.
4. Pull the arrows, photograph the holes straight on, and use them as ground truth.

### The verdicts, decided now rather than argued about later

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

### The verdict, taken *(date)*

*(Not yet: it needs the photos.)*

## 2. The strip: what goes, decided against the app's shape

`optional-modules.md` lists the files; this is the proposal, waiting on the owner's yes.

| Module | Proposal | Why |
| --- | --- | --- |
| Room and the schema gate | **Delete** | The idea scores an end; it keeps no rounds or history. If the owner wants rounds kept, Room stays instead: a round is ends joined to arrows, which is what a table is for. |
| Photos (media pipeline) | **Keep** | The app takes photos. `TakePicture` and the `FileProvider` are the capture path until Phase 1 decides on CameraX. Whether photos are kept after scoring is Phase 1's call; the default is to delete them once the end is confirmed. |
| Backup export/restore | **Delete**; Auto Backup takes over | Nothing to back up without history. Comes back with Room if rounds are kept. |
| Reminders and WorkManager | **Delete** | No schedules in the idea. |
| The tip | **Keep** unless the owner says otherwise | As in every MaksForge app. |
| Placeholder domain | **Replace** with an empty *Score an end* screen (E) | |

## 3. The first face

**Proposal:** the single-spot ten-ring World Archery face, with the size as a parameter. 122, 80, 60
and 40 cm are the same ten equal rings at different scales (ring width 6.1, 4, 3 and 2 cm), so one
implementation covers outdoor and indoor. After it, the 80 cm six-ring face, then the vertical triple
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

Design decisions go to a Fable subagent before options reach the owner (global rule). Not branded:
MaksForge colours only if the owner says so.

---

## Tests

None in this phase: no app code computes a score yet. The scoring function arrives in Phase 1 with its
tests, because it is this app's safety value: a line cutter scored low, a compound gold scored 10, a
second arrow in a triple spot scored. Each one fails in the direction the archer cannot see.

## Documents this phase amends

ADR-0001, 0002, 0003, 0005 (each a dated amendment on the strip), `CONTEXT.md`, `CLAUDE.md`'s stack
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
| R1 | Rings fit automatically in each of the three views, with the residual in mm | the gate script, step 1 | *(not taken)* |
| R2 | Median and worst entry-point error, single view against two views, against the holes | the gate script, steps 3–4 | *(not taken)* |
| R3 | How many of the six entry points each view hides | the gate script, step 2 | *(not taken)* |
| R4 | Shafts found automatically by the line segment detector, out of 18 | the gate script, step 2 | *(not taken)* |
