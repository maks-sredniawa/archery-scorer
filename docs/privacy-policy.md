---
layout: default
title: Privacy Policy
---

# Privacy Policy

_Last updated: 12 November 2026_

Archery Scorer is an Android app that counts the score of an archery end from photos of the target.
This policy describes what the app does with the information you put into it. It is short because
the app does very little.

## The app collects nothing

Archery Scorer has no account, no sign-in, and no server. Nothing you enter is transmitted anywhere.

Everything you record is stored **only in the app's private storage on your own device**, and is
readable only by the app.

There is no analytics, no crash reporting, no advertising, and no third-party SDK that phones home.
The Google Play Billing library, which handles tips, carries usage logging of its own; without the
`INTERNET` permission it has no way to send it.

## What the app can access, and why

- **Photos of your target.** When you photograph an end, the app hands the shot to your phone's own
  camera app and receives the single picture it takes; it declares no camera permission and never
  has access to your gallery. The picture is **scored on your phone and never uploaded**. It is
  copied into the app's own storage, **re-encoded so that the original's metadata does not travel
  with it**; the location a camera stamps on a photo is removed in the process.
- **Google Play billing.** Lets the app ask the Google Play app for the price of a tip and open its
  payment sheet. It gives the app nothing about you.

## The two things that happen outside the app

These are done by the operating system or by Google, not by Archery Scorer, but they are the honest
answer to "where could my data be":

1. **Android's automatic backup.** If it is enabled on your phone, Android backs up the app's data
   to your own Google Drive, in a space that does not count against your storage quota and that
   Google states apps cannot read. It covers everything the app stores, your settings included, so
   they come back when you set up a new phone. You can turn this off in your phone's settings.
2. **Google Play.** Installing and updating an app is a transaction between your phone and Google,
   with its own privacy policy. About installs, the developer of this app receives aggregate,
   anonymous statistics — install counts, crash rates, country-level breakdowns — and no information
   about individuals.

   **A tip, if you leave one, is paid to Google Play.** The app asks the Play app on your phone for
   the prices and opens Play's own payment sheet; your payment details go to Google and never to the
   app. Tips unlock nothing, so the app keeps no record of one. The developer receives the payment
   and Google's order reports, which show for each tip the product, the price, your country, state
   and postcode, and the model of your phone — and your city, in the few countries where the developer
   rather than Google is the seller — but not your name or payment details. The developer uses them
   only for accounting.

## Children

The app is not directed at children and collects nothing from anyone.

## Deleting your data

Uninstalling the app removes everything it stored. There is nowhere else to delete it from, because
there is nowhere else it went.

## Changes

If this policy changes, the date at the top changes with it, and the history of this file is public
in the repository.

## Contact

**archery-scorer.support@maksforge.com**
