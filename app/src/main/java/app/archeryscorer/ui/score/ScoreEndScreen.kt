package app.archeryscorer.ui.score

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import app.archeryscorer.R
import app.archeryscorer.theme.Spacing
import app.archeryscorer.ui.appViewModelExtras

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScoreEndScreen(
    onOpenSupport: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ScoreEndViewModel =
        viewModel(factory = ScoreEndViewModel.Factory, extras = appViewModelExtras()),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        modifier = modifier,
        topBar = { TopAppBar(title = { Text(stringResource(R.string.score_end_title)) }) },
    ) { insets ->
        Column(modifier = Modifier.fillMaxSize().padding(insets)) {
            if (state.showTipAsk) {
                TipAskCard(
                    onTip = {
                        viewModel.answerTipAsk()
                        onOpenSupport()
                    },
                    onDecline = viewModel::answerTipAsk,
                    modifier = Modifier.padding(start = Spacing.base, end = Spacing.base, top = Spacing.base),
                )
            }
            Column(
                modifier = Modifier.weight(1f).fillMaxSize().padding(Spacing.block),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(Spacing.base, Alignment.CenterVertically),
            ) {
                Text(
                    text = stringResource(R.string.score_end_purpose),
                    style = MaterialTheme.typography.bodyLarge,
                    textAlign = TextAlign.Center,
                )
                Button(onClick = {}, enabled = false) {
                    Text(stringResource(R.string.score_end_take_photo))
                }
                Text(
                    text = stringResource(R.string.score_end_not_ready),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}
