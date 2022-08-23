from collections import defaultdict
import numpy as np
import pandas as pd


def calculate_pnl_2(wallet_trades):
    """
    B(<t) := amount bought before t.
    S(t) := amount sold at t
    S_adj(t) = min(token_balance, S(t)) := adjusted amount sold at t (you can't sell more than you bought)

    In order to sell you must have made an investment at some point.

    I(t) = S_adj(t) * b_avg(t) := investment you made to sell S_adj(t).
    b_avg(t) := average buy price of token until t.

    - b_avg = curr_buy_amount * buy_price + prev_token_balance * prev_avg_buy_price
    - buying tokens increment balance vs. selling tokens decrement balance

    Gain(t) = (S_adj(t) * price_sell - I(t))
    """

    stats = defaultdict(lambda: [])

    for d in wallet_trades:
        for coin_id in [d["buy_coin_id"], d["sell_coin_id"]]:

            if len(stats[coin_id]) == 0:
                stats[coin_id].append({
                    # "time": datetime.utcfromtimestamp(0),
                    "token_balance": 0,
                    "avg_buy_price": None,
                    "buy_amount": 0,
                    "sell_amount": 0,
                    "sell_amount_adj": 0,
                    "price_sold": None,
                })

            if coin_id == d["sell_coin_id"]:
                prev_token_balance = stats[coin_id][-1]["token_balance"]  # note: can be 0.

                # note: you can't sell more than (we know) you have:
                sell_amount = d["sell_amount"]
                sell_amount_adj = min(sell_amount, prev_token_balance)  # = 0 if prev_token_balance = 0

                if prev_token_balance == 0:
                    avg_buy_price = None
                else:
                    avg_buy_price = stats[coin_id][-1]["avg_buy_price"]  # = prev_avg_buy_price

                price_sold = d["amount_usd"] / sell_amount

                if avg_buy_price is not None:
                    investment = sell_amount_adj * avg_buy_price  # = 0 if sell_amount_adj = 0
                else:
                    investment = 0

                gain = sell_amount_adj * price_sold - investment  # = 0 if sell_amount_adj = 0
                curr_token_balance = prev_token_balance - sell_amount_adj  # is >= 0

                stats[coin_id].append({
                    # "time": datetime.utcfromtimestamp(d["timestamp_block"]),  # done.
                    "token_balance": curr_token_balance,  # done.
                    "avg_buy_price": avg_buy_price,  # done.
                    "buy_amount": 0,  # done.
                    "sell_amount": sell_amount,  # done.
                    "sell_amount_adj": sell_amount_adj,  # done.
                    "price_sold": price_sold,  # done.
                    "gain": gain,
                    "investment": investment
                })

            if coin_id == d["buy_coin_id"]:
                buy_amount = d["buy_amount"]
                prev_token_balance = stats[coin_id][-1]["token_balance"]
                curr_token_balance = buy_amount + prev_token_balance
                prev_avg_buy_price = stats[coin_id][-1]["avg_buy_price"]  # can be None
                buy_price = d["amount_usd"] / buy_amount

                if prev_avg_buy_price is not None:
                    num = (buy_amount * buy_price + prev_token_balance * prev_avg_buy_price)
                    avg_buy_price = num / curr_token_balance
                else:
                    avg_buy_price = buy_price

                stats[coin_id].append({
                    # "time": datetime.utcfromtimestamp(d["timestamp_block"]),
                    "token_balance": curr_token_balance,
                    "avg_buy_price": avg_buy_price,
                    "buy_amount": buy_amount,
                    "sell_amount": 0,
                    "sell_amount_adj": 0,
                    "price_sold": None,
                    "gain": None,
                    "investment": None
                })

    total_gain = 0
    total_investment = 0
    for coin_id in stats:
        records = pd.DataFrame(stats[coin_id]).to_dict("list")
        total_gain += np.nansum(records["gain"])
        total_investment += np.nansum(records["investment"])
    if total_investment > 0:
        wallet_pnl = total_gain / total_investment
    else:
        wallet_pnl = None
    return wallet_pnl