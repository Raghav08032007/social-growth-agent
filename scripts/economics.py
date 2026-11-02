"""Illustrative contribution model, not vendor quotes or financial advice."""
from decimal import Decimal, ROUND_CEILING

arpa = Decimal('1349')
fee_rate = Decimal('0.035')
usage = Decimal('300')
for accounts, fixed in ((10, 15000), (100, 15000), (1000, 105000)):
    revenue = arpa * accounts
    fees = revenue * fee_rate
    contribution = revenue - usage * accounts - fees - fixed
    print(f'{accounts:4} accounts: revenue INR {revenue:,.2f}; contribution INR {contribution:,.2f} ({contribution/revenue:.1%})')
for cost in ('150', '300', '600'):
    unit = arpa * (1 - fee_rate) - Decimal(cost)
    breakeven = (Decimal(15000) / unit).to_integral_value(rounding=ROUND_CEILING)
    print(f'Usage INR {cost}: {breakeven} accounts to cover INR 15,000 listed fixed costs')
