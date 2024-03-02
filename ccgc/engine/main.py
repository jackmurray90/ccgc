#!/usr/bin/env python3

from collections import defaultdict
from pathlib import Path
from datetime import datetime

from ccgc.engine.coinspot import Coinspot, CoinspotSendsReceives
from ccgc.engine.coinbase import Coinbase
from ccgc.engine.binance import Binance
from ccgc.engine.trezor import Trezor
from ccgc.engine.adjustments import Adjustments
from ccgc.engine.models import TaxableEvent, Type, SuperTransfer, ParseFileResult, CalculationResult, EventResult, Adjustment, UnaccountedForFunds, AnnualSummary, RemainingBalance

def calculate(csv_files):
    australian_tax_year = True
    current_rate = 95585
    super_monthly_payment = 1100

    exchanges = [
        Coinspot(),
        CoinspotSendsReceives(),
        Coinbase(),
        Binance(),
        Trezor(),
        Adjustments(),
    ]

    events = defaultdict(lambda: [])

    result = CalculationResult()

    for csv_file in csv_files:
        path = Path(csv_file.file.path)
        for exchange in exchanges:
            if exchange.can_load_events(path):
                try:
                    for event in exchange.load_events(path):
                        events[event.asset].append(event)
                    result.files.append(ParseFileResult(filename=csv_file.filename, parsed=True))
                    break
                except:
                    pass
        else:
            result.files.append(ParseFileResult(filename=csv_file.filename, parsed=False))

    total_profit = defaultdict(lambda: 0)
    total_discounted_profit = defaultdict(lambda: 0)
    remaining_buys = defaultdict(lambda: [])

    for asset in events:
        events[asset].sort(key=lambda x: x.timestamp)
        buys = []
        for event in events[asset]:
            if australian_tax_year:
                tax_year = (
                    event.timestamp.year - 1
                    if event.timestamp.month <= 6
                    else event.timestamp.year
                )
            else:
                tax_year = event.timestamp.year
            if isinstance(event, SuperTransfer):
                while event.asset_amount > 0:
                    if buys[-1].asset_amount <= event.asset_amount:
                        result.adjustments.append(
                            Adjustment(
                                timestamp=buys[-1].timestamp,
                                type=Type.buy,
                                asset_amount=buys[-1].asset_amount,
                                aud_amount=buys[-1].aud_amount,
                                comment='Buy on Coinspot',
                            ),
                        )
                        event.asset_amount -= buys[-1].asset_amount
                        buys = buys[:-1]
                    else:
                        fraction = event.asset_amount / buys[-1].asset_amount
                        result.adjustments.append(
                            Adjustment(
                                timestamp=buys[-1].timestamp,
                                type=Type.buy,
                                asset_amount=event.asset_amount,
                                aud_amount=buys[-1].aud_amount * fraction,
                                comment='Buy on Coinspot',
                            ),
                        )
                        buys[-1] = TaxableEvent(
                            timestamp=buys[-1].timestamp,
                            asset=asset,
                            type=Type.buy,
                            asset_amount=buys[-1].asset_amount * (1 - fraction),
                            aud_amount=buys[-1].aud_amount * (1 - fraction),
                        )
                        event.asset_amount = 0
            elif event.type == Type.transfer:
                result.all_total_profit -= event.aud_amount
                total_profit[tax_year] -= event.aud_amount
                total_discounted_profit[tax_year] -= event.aud_amount
                while event.asset_amount > 0:
                    if len(buys) == 0:
                        result.unaccounted_for_funds.append(
                            UnaccountedForFunds(
                                timestamp=event.timestamp,
                                asset=asset,
                                asset_amount=event.asset_amount,
                            ),
                        )
                        buys = [
                            TaxableEvent(
                                timestamp=event.timestamp,
                                asset=asset,
                                type=Type.buy,
                                asset_amount=event.asset_amount,
                                aud_amount=0,
                            )
                        ]
                    if buys[0].asset_amount <= event.asset_amount:
                        event.asset_amount -= buys[0].asset_amount
                        buys = buys[1:]
                    else:
                        fraction = event.asset_amount / buys[0].asset_amount
                        buys[0] = TaxableEvent(
                            timestamp=buys[0].timestamp,
                            asset=asset,
                            type=Type.buy,
                            asset_amount=buys[0].asset_amount - event.asset_amount,
                            aud_amount=buys[0].aud_amount * (1 - fraction),
                        )
                        event.asset_amount = 0
                        event.aud_amount = 0
            elif event.type == Type.buy:
                buys.append(event)
            else:
                selling_rate = event.aud_amount / event.asset_amount
                while event.asset_amount > 0:
                    if len(buys) == 0:
                        result.unaccounted_for_funds.append(
                            UnaccountedForFunds(
                                timestamp=event.timestamp,
                                asset=asset,
                                asset_amount=event.asset_amount,
                            ),
                        )
                        buys = [
                            TaxableEvent(
                                timestamp=event.timestamp,
                                asset=asset,
                                type=Type.buy,
                                asset_amount=event.asset_amount,
                                aud_amount=0,
                            )
                        ]
                    buying_rate = buys[0].aud_amount / buys[0].asset_amount
                    buying_timestamp = buys[0].timestamp
                    if buys[0].asset_amount <= event.asset_amount:
                        amount = buys[0].asset_amount
                        profit = (selling_rate - buying_rate) * buys[0].asset_amount
                        event.asset_amount -= buys[0].asset_amount
                        event.aud_amount -= selling_rate * buys[0].asset_amount
                        buys = buys[1:]
                    else:
                        amount = event.asset_amount
                        fraction = event.asset_amount / buys[0].asset_amount
                        profit = (selling_rate - buying_rate) * event.asset_amount
                        buys[0] = TaxableEvent(
                            timestamp=buys[0].timestamp,
                            asset=asset,
                            type=Type.buy,
                            asset_amount=buys[0].asset_amount - event.asset_amount,
                            aud_amount=buys[0].aud_amount * (1 - fraction),
                        )
                        event.asset_amount = 0
                        event.aud_amount = 0
                    discount = (
                        profit >= 0
                        and buying_timestamp.replace(year=buying_timestamp.year + 1)
                        < event.timestamp
                    )
                    result.events.append(
                        EventResult(
                            profit=profit,
                            amount=amount,
                            asset=asset,
                            buying_rate=buying_rate,
                            selling_rate=selling_rate,
                            buying_timestamp=buying_timestamp,
                            selling_timestamp=event.timestamp,
                            discount=discount,
                        ),
                    )
                    result.all_total_profit += profit
                    total_profit[tax_year] += profit
                    if discount:
                        profit /= 2
                    total_discounted_profit[tax_year] += profit
        remaining_buys[asset] = buys

    for year in sorted(total_profit.keys()):
        result.annual_summaries.append(
            AnnualSummary(
                year=f"{year}/{year+1}" if australian_tax_year else str(year),
                profit=total_profit[year],
                discounted_profit=total_discounted_profit[year],
            ),
        )

    for asset in remaining_buys:
        result.remaining_balances.append(
            RemainingBalance(
                asset=asset,
                asset_amount=sum([buy.asset_amount for buy in remaining_buys[asset]]),
                aud_amount=sum([buy.aud_amount for buy in remaining_buys[asset]]),
            ),
        )

    total_super_btc = 0
    while super_monthly_payment > 0:
        if not remaining_buys["BTC"]:
            break
        if remaining_buys["BTC"][-1].aud_amount >= super_monthly_payment:
            fraction = super_monthly_payment / remaining_buys["BTC"][-1].aud_amount
            total_super_btc += remaining_buys["BTC"][-1].asset_amount * fraction
            break
        else:
            total_super_btc += remaining_buys["BTC"][-1].asset_amount
            super_monthly_payment -= remaining_buys["BTC"][-1].aud_amount
            remaining_buys["BTC"] = remaining_buys["BTC"][:-1]
    result.next_super_payment = f"{datetime.now().strftime('%d/%m/%Y')},super,{round(total_super_btc, 8)},,Transfer to superannuation"

    return result
