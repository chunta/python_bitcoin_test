import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 初始資金
cash = 2000.0
init_cash = cash
btc_holding = 0.0
buy_price = None
trades = []

# 只指定 start，下載到今天
btc = yf.download("BTC-USD", start="2020-01-01")

# 計算100日SMA
btc['SMA100'] = btc['Close'].rolling(window=100).mean()

# 取2022-01-01之後的資料
btc_2022 = btc.loc["2022-01-01":]

# 過濾掉 NaN 的 SMA100
btc_sma_valid = btc_2022[btc_2022['SMA100'].notna()]
print(btc_sma_valid)

# --- 回測策略 ---
buy_dates = []
buy_prices = []
sell_dates = []
sell_prices = []
buy_scale = 0.9
sell_scale = 1.1
lose_scale = 0.95
for date, row in btc_sma_valid.iterrows():
    close = float(row['Close'].iloc[0])
    sma = float(row['SMA100'].iloc[0])
    
    # 如果沒錢且沒有持倉，離開迴圈
    if cash <= 0 and btc_holding == 0:
        print(f"[EXIT] 目前現金: ${cash:.2f}, BTC持有量: {btc_holding:.6f}")
        break
    
    # 買入策略
    if btc_holding == 0:
        if close < sma * buy_scale:  # 低於 SMA100 20%
            btc_holding = cash / close
            buy_price = close
            cash -= btc_holding * close  # 扣掉實際購買成本
            trades.append({'Date': date, 'Type': 'BUY', 'Price': close, 'BTC': btc_holding})
            print(f"[BUY] BTC: {btc_holding:.6f} 單價: ${close:.2f}")
            buy_dates.append(date)
            buy_prices.append(close)
        else:
            print(f"close: {close} is no less than {sma} * {buy_scale}")

    # 賣出策略
    else:
        total_value = btc_holding * close
        origin_value = buy_price * btc_holding

        # 獲利條件
        if total_value >= origin_value * sell_scale:  # 賺 10%
            cash += total_value
            trades.append({'Date': date, 'Type': 'SELL_PROFIT', 'Price': close, 'BTC': btc_holding})
            print(f"[SELL - PROFIT] BTC: {btc_holding:.6f} 單價: ${close:.2f} 現金: ${cash:.2f}")
            btc_holding = 0
            buy_price = None
            sell_dates.append(date)
            sell_prices.append(close)

        # 止損條件
        elif total_value <= origin_value * lose_scale:  # 虧 10%
            cash += total_value
            trades.append({'Date': date, 'Type': 'SELL_LOSS', 'Price': close, 'BTC': btc_holding})
            print(f"[SELL - LOSS] BTC: {btc_holding:.6f} 單價: ${close:.2f} 現金: ${cash:.2f}")
            btc_holding = 0
            buy_price = None
            sell_dates.append(date)
            sell_prices.append(close)

# 計算最後持有價值
final_value = cash + btc_holding * btc_sma_valid['Close'].iloc[-1].values[0]

# 印出交易紀錄與最終資金
if trades:
    print("\n=== 交易紀錄 ===")
    for t in trades:
        trade_type = t['Type']
        date = t['Date'].strftime("%Y-%m-%d")
        price = t['Price']
        btc_amount = t['BTC']
        cash_amount = btc_amount * price if trade_type == 'SELL' else btc_amount * price
        print(f"{date} | {trade_type:4} | BTC: {btc_amount:.6f} | 金額: ${cash_amount:.2f} | 單價: ${price:.2f}")

print(f"\n最終資金價值: ${final_value:.2f} btc_holding: {btc_holding} 報酬率: {final_value / init_cash}")

# --- Matplotlib 畫圖 ---
plt.figure(figsize=(14,7))
plt.plot(btc_2022['Close'], label="BTC-USD Close", alpha=0.7)
plt.plot(btc_2022['SMA100'], label="SMA 100 Days", color="orange", linewidth=2)

# 標記買賣點
plt.scatter(buy_dates, buy_prices, marker="^", color="green", s=100, label="BUY")
plt.scatter(sell_dates, sell_prices, marker="v", color="red", s=100, label="SELL")

plt.title("BTC-USD Price with 100-Day SMA & Trades (2024-)")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.legend()
plt.grid(True)
plt.show()
