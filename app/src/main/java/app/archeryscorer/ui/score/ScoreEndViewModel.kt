package app.archeryscorer.ui.score

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import app.archeryscorer.MainApplication
import app.archeryscorer.data.AppPreferences
import app.archeryscorer.tip.TipJar
import app.archeryscorer.tip.tipAskDue
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.time.Instant

data class ScoreEndUiState(
    /** The tip's one ask (ADR-0007). False wherever Play will not sell a tip: nothing is asked for that cannot be bought. */
    val showTipAsk: Boolean = false,
)

class ScoreEndViewModel(
    endsScored: Flow<Int>,
    private val preferences: AppPreferences,
    tipJar: TipJar,
    installedAt: Instant,
) : ViewModel() {
    val state: StateFlow<ScoreEndUiState> =
        combine(endsScored, preferences.tipAsked, tipJar.offers) { ends, asked, offers ->
            ScoreEndUiState(showTipAsk = offers.isNotEmpty() && tipAskDue(asked, ends, installedAt, Instant.now()))
        }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ScoreEndUiState())

    init {
        // Prices are asked for only once the ask could otherwise be due — one product query saved
        // on every other visit. The binding itself happens on every foreground anyway, to settle tips.
        viewModelScope.launch {
            val due = tipAskDue(preferences.tipAsked.first(), endsScored.first(), installedAt, Instant.now())
            if (due) tipJar.refresh()
        }
    }

    /** Either answer — *Leave a tip* or *No thanks* — ends the ask on this install. */
    fun answerTipAsk() {
        viewModelScope.launch { preferences.markTipAsked() }
    }

    companion object {
        val Factory: ViewModelProvider.Factory =
            viewModelFactory {
                initializer {
                    val app = this[APPLICATION_KEY] as MainApplication
                    ScoreEndViewModel(
                        endsScored = app.container.preferences.endsScored,
                        preferences = app.container.preferences,
                        tipJar = app.container.tipJar,
                        installedAt = app.container.installedAt,
                    )
                }
            }
    }
}
