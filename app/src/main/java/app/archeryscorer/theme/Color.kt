package app.archeryscorer.theme

import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color

// GENERATED — do not hand-edit individual roles.
//
// Both schemes are derived from four brand seeds by Material's tonal palette
// construction (CAM16/HCT): the seeds are the judgement, the ~36 roles are
// arithmetic. Hand-picking a role breaks the fixed tonal relationship it holds
// with the rest of its family, and the failure shows up as a contrast bug on one
// screen out of thirty rather than as a visible mistake here.
//
//   primary   #2F6B4A  — brand: filled buttons, FAB, selected tab
//   secondary #5C6E63  — quiet containers: chips, tonal buttons, selected segment
//   tertiary  #7A5C8E  — accents and caution markers, used sparingly
//   neutral   #E2E5E1  — seeds every surface, so it decides warm or cool overall
//
// Error stays M3 baseline (hue 25, chroma 84): a safety signal, not a brand choice.
//
// To change the palette, edit the seeds in scripts/gen_scheme.py and re-run it.
// Colours come from MaterialTheme, never literals, and dynamic colour defaults
// off (ADR-0006) so this file is what a user actually sees.

private val AppLightColors =
    lightColorScheme(
        primary = Color(0xFF2E6A49),
        onPrimary = Color(0xFFFFFFFF),
        primaryContainer = Color(0xFFB1F1C7),
        onPrimaryContainer = Color(0xFF002110),
        inversePrimary = Color(0xFF96D4AC),
        secondary = Color(0xFF516258),
        onSecondary = Color(0xFFFFFFFF),
        secondaryContainer = Color(0xFFD4E7DA),
        onSecondaryContainer = Color(0xFF0E1F17),
        tertiary = Color(0xFF705284),
        onTertiary = Color(0xFFFFFFFF),
        tertiaryContainer = Color(0xFFF4D9FF),
        onTertiaryContainer = Color(0xFF290E3C),
        error = Color(0xFFBA1B1B),
        onError = Color(0xFFFFFFFF),
        errorContainer = Color(0xFFFFDAD4),
        onErrorContainer = Color(0xFF410001),
        background = Color(0xFFF7FAF6),
        onBackground = Color(0xFF191C1A),
        surface = Color(0xFFF7FAF6),
        onSurface = Color(0xFF191C1A),
        surfaceVariant = Color(0xFFDBE5DE),
        onSurfaceVariant = Color(0xFF404944),
        surfaceDim = Color(0xFFD8DBD7),
        surfaceBright = Color(0xFFF7FAF6),
        surfaceContainerLowest = Color(0xFFFFFFFF),
        surfaceContainerLow = Color(0xFFF1F4F0),
        surfaceContainer = Color(0xFFECEFEB),
        surfaceContainerHigh = Color(0xFFE6E9E5),
        surfaceContainerHighest = Color(0xFFE0E3DF),
        inverseSurface = Color(0xFF2E312F),
        inverseOnSurface = Color(0xFFEEF1ED),
        outline = Color(0xFF6F7973),
        outlineVariant = Color(0xFFBFC9C2),
        scrim = Color(0xFF000000),
    )

private val AppDarkColors =
    darkColorScheme(
        primary = Color(0xFF96D4AC),
        onPrimary = Color(0xFF00391F),
        primaryContainer = Color(0xFF105132),
        onPrimaryContainer = Color(0xFFB1F1C7),
        inversePrimary = Color(0xFF2E6A49),
        secondary = Color(0xFFB8CBBE),
        onSecondary = Color(0xFF24342B),
        secondaryContainer = Color(0xFF3A4B41),
        onSecondaryContainer = Color(0xFFD4E7DA),
        tertiary = Color(0xFFDDBAF2),
        onTertiary = Color(0xFF402553),
        tertiaryContainer = Color(0xFF573B6B),
        onTertiaryContainer = Color(0xFFF4D9FF),
        error = Color(0xFFFFB4A9),
        onError = Color(0xFF680003),
        errorContainer = Color(0xFF930006),
        onErrorContainer = Color(0xFFFFDAD4),
        background = Color(0xFF101412),
        onBackground = Color(0xFFE0E3DF),
        surface = Color(0xFF101412),
        onSurface = Color(0xFFE0E3DF),
        surfaceVariant = Color(0xFF404944),
        onSurfaceVariant = Color(0xFFBFC9C2),
        surfaceDim = Color(0xFF101412),
        surfaceBright = Color(0xFF373A38),
        surfaceContainerLowest = Color(0xFF0B0F0D),
        surfaceContainerLow = Color(0xFF191C1A),
        surfaceContainer = Color(0xFF1D201E),
        surfaceContainerHigh = Color(0xFF272B29),
        surfaceContainerHighest = Color(0xFF323533),
        inverseSurface = Color(0xFFE0E3DF),
        inverseOnSurface = Color(0xFF2E312F),
        outline = Color(0xFF8A938D),
        outlineVariant = Color(0xFF404944),
        scrim = Color(0xFF000000),
    )

internal val LightColors = AppLightColors
internal val DarkColors = AppDarkColors
