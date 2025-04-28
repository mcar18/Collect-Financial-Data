import pandas as pd
import numpy as np
from arch import arch_model
import matplotlib.pyplot as plt

# 1) Load daily prices
df = pd.read_csv(
    'cleaned fundamentals/AAPL/cleaned_fundamentals.csv',
    index_col='date',
    parse_dates=True
)
price = df['Close'].dropna()

# 2) Compute log returns (in percent)
logp      = np.log(price)
logr      = logp.diff().dropna() * 100  # scale ×100 for percentage

# Plot the series
plt.figure()
logr.plot(title='AAPL Daily Log Returns (%)')
plt.show()

# 3) Fit AR(1)-GARCH(1,1) on log returns
#    mean='AR', lags=1; vol='Garch', p=1, q=1
model = arch_model(logr,
                   mean='AR',
                   lags=1,
                   vol='Garch',
                   p=1,
                   q=1,
                   dist='normal')
res = model.fit(update_freq=10, disp='off')
print(res.summary())

# 4) Forecast next-day return and volatility
#    horizon=1 gives one-step ahead
fc = res.forecast(horizon=1, reindex=False)
mu_hat  = fc.mean.iloc[-1, 0] / 100
sigma_hat = np.sqrt(fc.variance.iloc[-1, 0]) / 100
print(f"\nNext-day ΔlogP forecast: {mu_hat:.4f}")
print(f"Next-day volatility forecast: {sigma_hat:.4f}")

# 5) (Optional) Rolling backtest
#    e.g., walk-forward refit every 250 days, compute forecast error metrics

# 6) Use these forecasts to project price:
#    P_hat = P_t * exp(mu_hat)
p_hat = price.iloc[-1] * np.exp(mu_hat)
print(f"\nNext-day price forecast: {p_hat:.2f}")