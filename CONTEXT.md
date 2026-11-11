# Vocabulary

<The words this app uses, and the ones it does not. Fill this in early — it is cheap now and
expensive later, because a name that is wrong in the model is wrong in the schema, the UI copy, every
translation of it, and the URL scheme.>

**The rule this file exists to enforce: one concept, one word, everywhere.** The entity, the DAO, the
route key, the string resource and the sentence in the UI all use it. When the domain word and the
user-facing word genuinely differ, both are written here with the difference stated.

## The domain

| Term | Means | Not |
| --- | --- | --- |
| **End** | the arrows shot before going to the target to score them, usually 3 or 6. The app scores one end at a time and keeps no history | round (a round is many ends) |
| **Arrow** | one shot in an end. Its score comes from its entry point, never from where the nock is | |
| **Face** | the printed target. The first is the World Archery single-spot 10-ring face, in 122, 80, 60 or 40 cm | target (the whole boss and stand) |
| **View** | one photo of the end. An end is scored from as few views as resolve every arrow | |
| **Entry point** | where the shaft enters the face; the point that is scored | hole (what is left once the arrow is pulled) |
| **Line cutter** | an arrow whose shaft touches a dividing line, which scores the higher zone | |
| **Tip** | a one-off payment to the developer through Google Play that **unlocks nothing** (ADR-0007). The home screen mentions it once; Help and feedback offers it for good | donation, support the project, premium, supporter |

## Words we deliberately avoid

<For example: "'delete' is reserved for something irreversible; anything recoverable is 'archived'."
The value here is in the distinctions, not the definitions.>

## Naming conventions in code

Some names in this codebase are deliberately generic — `AppTheme`, `AppPreferences`,
`AppContainer`, `MainApplication`, `MainActivity`. They stay correct whatever the app is called, so
renaming the app is a package move rather than a repo-wide find-and-replace. Don't rename them to
match the product; name the *domain* types after the domain instead.
