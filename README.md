# gta6-twitch-ccu-forecast-01

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/gemblongjos3-cmyk/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/gemblongjos3-cmyk/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

A deterministic, offline Python program forecasting GTA VI's launch-day Twitch concurrent viewers for hours 2–24. Each hour has five quantiles: 5%, 25%, 50%, 75%, and 95%. It uses only the Python 3.13 standard library and the data supplied in each input case; no network access or third-party dependencies are needed.

The method pools comparable launch-day shapes, normalised by each launch's hour-1 viewers. Comparables labelled “before release” are excluded, and a curve must contain hour 1 and at least 20 valid release-day hourly points. Missing hours are interpolated linearly in log space, with the nearest observed value used at either end.

A Gaussian kernel with bandwidth 1.0 weights each comparable by the similarity of its hour-1 scale to the observed GTA VI hour-1 audience. Console-only launches receive a 2.0× weight boost. Launches whose hour-1 viewers are less than 15% of their daily peak receive a 0.15× downweight, reducing the influence of delayed-peak launch shapes.

For each forecast hour, weighted empirical quantiles are computed from the pooled log ratios, with neighbouring hours contributing half weight. The quantile spread around the median is shrunk by 0.85, then the ratios are scaled to the observed hour-1 audience and rounded half up to two decimal places. These log-space quantiles target the competition's log-scale pinball loss. If no comparable qualifies, the persistence fallback keeps the median at hour 1 and widens uncertainty with `0.15 * sqrt(hour - 1)`.

## Run it

Place JSON case files ending in `.in` in `input/`, then run:

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Files are read in filename order. Each case produces `<id>.out` containing compact JSON followed by a newline, with forecast hours in the input's order. The default directories are `/input` and `/output` when the environment variables are unset. Quantile levels must be exactly `[0.05, 0.25, 0.5, 0.75, 0.95]`; other levels raise an error.

<sub>Entered on [make.fun](https://make.fun/?ref=a12adhf8&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
