---
layout: default
title: Archery Scorer
---

# Archery Scorer

**Counts the score of an archery end from photos of the target, taken with the arrows still in.**
Free, ad-free, and entirely on your own phone: no account, no sign-up, no server.

## What it does

- **Scores an end from a photo** — take a photo of the target with your phone's own camera app, and
  the app shows each arrow it found on a drawing of the face, with its value, the end's total and the
  X count.
- **Asks for another angle only when it is unsure** — one more photo from the side, and only for the
  arrows it cannot place.
- **Lets you correct every arrow** — drag one that sits wrong, add one it missed, remove one it
  invented. An arrow within about 2 mm of a line is flagged so you look at it yourself.
- **Knows the rules** — a line cutter takes the higher value, and the compound inner ten on the 60
  and 40 cm faces is counted as such.

It scores the single-spot ten-ring World Archery face in 122, 80, 60 and 40 cm. The 80 cm six-ring
face and the vertical triple spot are planned.

## Not ready yet

The app is in testing. The current test build has the *Score an end* screen, but scoring from a photo
does not work yet; it arrives in the next test builds.

## The score is yours to confirm

The app reads the target from a photo, so a blurred, dark or steeply angled shot can give a wrong
value or miss an arrow. Every arrow is shown for you to check before the end counts. It scores with
the arrows still in the target, not from holes, and at a tournament the judge's call stands.

## Your data stays on your device

There is no backend to send anything to, and the app does not request the internet permission.
Photos are scored on your phone and never uploaded, with their location and other metadata removed
before they are stored. Everything lives in the app's private storage, and Android's own backup, if
you have it on, keeps a copy in your Google account. The details are in the

**[Privacy Policy](privacy-policy.md)**.

## Support

**archery-scorer.support@maksforge.com** — an ordinary mailbox that a person reads.

## The source

Built in the open at **[maks-sredniawa/archery-scorer](https://github.com/maks-sredniawa/archery-scorer)**.
