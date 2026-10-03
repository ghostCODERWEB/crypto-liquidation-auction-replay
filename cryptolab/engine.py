"""Settle descending-price collateral bids against debt with inventory caps and surplus reconciliation."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    collateral = integer(d["collateral"])
    debt = integer(d["debt"])
    start = integer(d["start"])
    duration = integer(d["duration"], 1)
    high = integer(d["start_price"], 1)
    low = integer(d["floor_price"], 1)
    if low > high:
        raise ValueError("floor above start price")
    initial = collateral
    raised = 0
    trace = []
    for e in chronology(d["bids"]):
        t = e["timestamp"]
        if t < start:
            raise ValueError("auction not started")
        elapsed = min(t - start, duration)
        price = high - (high - low) * elapsed // duration
        quantity = integer(e["quantity"], 1)
        maxprice = integer(e["max_price"], 1)
        fill = (
            0
            if maxprice < price or raised >= debt
            else min(quantity, collateral, (debt - raised + price - 1) // price)
        )
        cost = fill * price
        collateral -= fill
        raised += cost
        trace.append({"timestamp": t, "price": price, "filled": fill, "cost": cost})
    return {
        "trace": trace,
        "collateral_sold": initial - collateral,
        "collateral_remaining": collateral,
        "raised": raised,
        "debt_remaining": max(debt - raised, 0),
        "surplus": max(raised - debt, 0),
    }


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
