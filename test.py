import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 初始資金
cash = 2000.0
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

for date, row in btc_sma_valid.iterrows():
    close = float(row['Close'])
    sma = float(row['SMA100'])
    # 如果沒錢且沒有持倉，離開迴圈
    if cash <= 0:
        print(f"目前現金: ${cash:.2f}, BTC持有量: {btc_holding:.6f}")

    # 買入策略
    if btc_holding == 0:
        if close < sma * 0.8:  # 低於 SMA100 20%
            btc_holding = cash / close
            buy_price = close
            cash -= btc_holding * close  # 扣掉實際購買成本
            trades.append({'Date': date, 'Type': 'BUY', 'Price': close, 'BTC': btc_holding})
            print(f"我買了 BTC: {btc_holding:.6f} 單價: ${close:.2f}")
            buy_dates.append(date)
            buy_prices.append(close)

    # 賣出策略
    else:
        profit_cond = close > sma * 1.15 and close > buy_price * 1.05  # 高於SMA15%且高於買入成本5%
        total_value = btc_holding * close
        profit_cond = total_value >= cash * 1.1 # 總收入超過本金10%
        loss_cond = total_value <= cash * 0.8
        if profit_cond or loss_cond:
            cash += btc_holding * close  # 賣出得到現金
            trades.append({'Date': date, 'Type': 'SELL', 'Price': close, 'BTC': btc_holding})
            btc_holding = 0
            buy_price = None
            print(f"我賣了 BTC: {btc_holding:.6f} 單價: ${close:.2f} 現金: ${cash:.2f}")
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

print(f"\n最終資金價值: ${final_value:.2f} btc_holding: {btc_holding}")

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
