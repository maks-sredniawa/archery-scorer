# Shafts are found by our own model, trained on the straightened face

## Context

Phase 0 decides whether classical vision (OpenCV) finds arrow shafts well enough to score an end
without taps (`phase-0.md`, verdicts 1 and 2). Either way a trained detector comes later: after
verdict 1 to catch what the line segment detector misses, after verdict 2 to remove the taps.
Gate R4 on a rendered end, and the web photos before it, show where classical detection fails:
tight groups merge into one line, fletchings hide short shafts in straight-on views, and printed
lines and shadows pass for shafts.

Three things constrain the model: this repo's `LICENSE` (the code and weights must be under a
licence it can ship, which rules out the AGPL and the GPL), a phone with no `INTERNET` permission
(ADR-0007), and *photos never leave the phone* (`PLAN.md`, *Not in this plan*). We also have no
labelled photos of our own yet.

## Decision

**Automatic shaft detection is a small model of our own that predicts each arrow's entry point as a
heatmap on the face straightened from the rings, trained first on rendered ends and then on ends
the owner photographs and labels. It ships inside the APK and runs on the phone.**

- **What it sees.** The face is straightened per photo from the ring fit, as the gate already does,
  so the model always sees a face of the same size, centred and the same way up. That geometry is
  work the model does not have to learn, which is what makes a small model and a small dataset
  plausible.
- **What it predicts.** A heatmap of entry points, plus each shaft's direction, so the existing
  triangulation can still combine views. A small U-Net with a MobileNet-class encoder, written
  directly in PyTorch (BSD-3-Clause). No framework whose licence travels with the trained weights.
- **On the phone.** Exported to LiteRT (TensorFlow Lite, Apache-2.0) or ONNX Runtime Mobile (MIT),
  bundled as an asset of a few MB. No download and no network.
- **Data.**
  1. Rendered ends, from `synth.py` grown into a renderer with real arrows, straw, light and curled
     faces, labelled perfectly by construction. Blender's GPL covers the program, not what it
     renders, but a script calling Blender's Python API must itself be GPL (Blender's licensing
     FAQ). Such a script lives in its own GPL repo and only its renders come in, or the renderer is
     a permissively licensed one.
  2. The owner's own ends, labelled with `tools/gate/click.py`, which already records each shaft's
     near and far points and the holes as ground truth.
  3. The Wikimedia photos in `tools/gate/runs/web/` are a test set only, never training data.
- **Order.** Phase 0's verdict comes first, because the model stands on the ring fit. After verdict
  1, a small classifier over the classical detector's candidates may ship before the model to cut
  false detections. It needs less data but cannot recover shafts the detector missed.

## Alternatives

- **Ultralytics YOLO (v5, v8, v11).** The easiest tooling, but AGPL-3.0, and so is every model
  trained with it. It conflicts with `LICENSE` (`phase-0.md`, verdict 2).
- **YOLOv7, YOLOv9.** GPL-3.0, so out for the same reason.
- **A ready-made box detector on the raw photo:** MediaPipe Model Maker, YOLOX, NanoDet, RT-DETR,
  D-FINE, all Apache-2.0. Licence-clean, and MediaPipe exports to the phone most easily. It lost
  because a box around a 5 mm entry in an unstraightened, oblique photo is coarse, and it throws away
  the geometry the ring fit already gives.
- **Keypoints per arrow (entry and nock) with MMPose or RTMPose,** Apache-2.0. It gives the whole
  shaft line directly, but the tooling is heavier and it needs more labelled data. It stays the
  fallback if the heatmap cannot recover directions well enough to triangulate.
- **Collecting the archer's corrections from the app.** It is the richest source, but it needs the
  network, a backend and a privacy policy that says photos leave the phone, which reverses
  ADR-0007's `INTERNET` removal and *Not in this plan*. Not taken.
- **Photos from other people, by any route, mail included.** They contradict `privacy-policy.md`,
  the store listing's "nothing leaves your phone" and `play-app-content.md`'s Data safety answers.
  Opening that route is a new decision that amends those documents.

## Consequences

- The model is only as good as the labels, and they come slowly: each real end costs an afternoon
  at the range and a session of clicking. Rendered ends carry it until there are enough real ones.
- A face size or discipline the model was not trained on is a new dataset, not a setting.
- Training needs a GPU: a free hosted notebook is enough at this size. Inference on the phone adds a
  runtime library and a few MB to the APK.
- `LICENSE` requires each bundled component's licence text in `app/src/main/assets/licences/`.
  ONNX Runtime adds an MIT text there; LiteRT is covered by the Apache-2.0 text already there.
- Pretrained encoder weights come with their own terms. Check them when the encoder is chosen,
  record the choice beside this ADR, and add the terms to `app/src/main/assets/licences/`.
