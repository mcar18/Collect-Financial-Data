import pandas as pd
import numpy as np
from arch import arch_model

# 1) Load cleaned fundamentals for one ticker
df = pd.read_csv('cleaned fundamentals/AAPL/cleaned_fundamentals.csv',
                 index_col='date', parse_dates=True)

# 2) Compute log P/E
pe = df['PE'].replace([np.inf, -np.inf], np.nan).ffill().dropna()
log_pe = np.log(pe)

# 3) Difference to stationarize (first difference)
dlog_pe = log_pe.diff().dropna()

# 4) Fit AR(1)-GARCH(1,1) on the differenced series
#    mean='AR' with lags=1, vol='Garch', p=1, q=1
model = arch_model(dlog_pe*100,  # scale ×100 for percent units
                   mean='AR',
                   lags=1,
                   vol='Garch',
                   p=1,
                   q=1,
                   dist='normal')
res = model.fit(update_freq=5)
print(res.summary())

# 5) One-step-ahead forecast
forecasts = res.forecast(horizon=1, reindex=False)
mu_forecast   = forecasts.mean.iloc[-1, 0] / 100
vol_forecast  = np.sqrt(forecasts.variance.iloc[-1, 0]) / 100

print(f"Next Δlog PE forecast: {mu_forecast:.4f}")
print(f"Next volatility forecast: {vol_forecast:.4f}")

# 6) (Later) Combine with earnings forecast:
#    price_forecast = exp(log_pe.iloc[-1] + mu_forecast) * earnings_forecast