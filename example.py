import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import cast

from ynab import BudgetDetailResponse


def main(argv: list[str]):
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--json", default="ynab-budget-2025-10-29.json")
    _ = parser.add_argument("--start", default="2024-01-01")
    args = parser.parse_args(argv)
    json_path = Path(cast(str, args.json))
    start = datetime.strptime(cast(str, args.start), "%Y-%m-%d").date()
    print(f"{start=}")

    with json_path.open("r") as f:
        budget_detail_response = BudgetDetailResponse.from_dict(json.load(f))  # pyright: ignore[reportAny]
    if budget_detail_response is None:
        msg = "Bad JSON"
        raise Exception(msg)
    budget = budget_detail_response.data.budget
    if (
        budget.first_month is None
        or budget.last_month is None
        or budget.payees is None
        or budget.category_groups is None
        or budget.categories is None
        or budget.months is None
        or budget.transactions is None
        or budget.subtransactions is None
        or budget.scheduled_transactions is None
        or budget.scheduled_subtransactions is None
    ):
        msg = "budget is missing key fields"
        raise Exception(msg)
    payees = budget.payees
    category_groups = budget.category_groups
    categories = budget.categories
    months = budget.months
    transactions = budget.transactions
    subtransactions = budget.subtransactions
    scheduled_transactions = budget.scheduled_transactions
    scheduled_subtransactions = budget.scheduled_subtransactions

    print(f"{budget.first_month=}")
    print(f"{budget.last_month=}")
    print(f"{len(payees)=}")
    print(f"{len(category_groups)=}")
    print(f"{len(categories)=}")
    print(f"{len(months)=}")
    print(f"{len(transactions)=}")
    print(f"{len(subtransactions)=}")
    print(f"{len(scheduled_transactions)=}")
    print(f"{len(scheduled_subtransactions)=}")
    # print(budget.months[-1].model_dump_json(indent=2))
    print(f"Last month in list={budget.months[-1].month}")
    print(transactions[-1].model_dump_json(indent=2))
    # print(subtransactions[0].model_dump_json(indent=2))

    filtered_transactions = [t for t in transactions if t.var_date >= start]
    ftdict = {t.id: t for t in filtered_transactions}
    pdict = {p.id: p for p in payees}
    deleted_amounts: defaultdict[str, int] = defaultdict(int)
    fake_payee_ids = [p.id for p in payees if p.name == "Fake"]
    if len(fake_payee_ids) != 1:
        msg = f"Wrong number of Fake payees {len(fake_payee_ids)}"
        raise Exception(msg)
    fake_payee_id = fake_payee_ids[0]
    inflow_category_ids = [
        c.id for c in categories if c.name == "Inflow: Ready to Assign"
    ]
    if len(inflow_category_ids) != 1:
        msg = f"Wrong number of Fake payees {len(inflow_category_ids)}"
        raise Exception(msg)
    inflow_category_id = inflow_category_ids[0]
    for t in transactions:
        if t.id not in ftdict:
            deleted_amounts[t.account_id] += t.amount
    filtered_subtransactions = [
        s for s in subtransactions if s.transaction_id in ftdict
    ]
    filtered_payee_ids = set(
        [t.payee_id for t in filtered_transactions if t.payee_id is not None]
        + [s.payee_id for s in filtered_subtransactions if s.payee_id is not None]
    )
    filtered_payees = [p for p in payees if p.id in filtered_payee_ids]
    filtered_months = [m for m in months if m.month >= start]

    print(f"{len(filtered_transactions)=}")
    print(f"{len(filtered_subtransactions)=}")
    print(f"{len(filtered_payees)=}")
    print(f"{len(filtered_months)=}")

    # TODO: fix first_month
    # TODONT: merge payees
    # TODONT: what about rules, where do those come from anyway?
    # TODO: add start transaction on day "start-1" for each account if non-zero
    #  id make it up
    #  var_date start - timedelta(days=1), basically
    #  amount from deleted_amounts
    #  memo = "Initial balance"
    #  cleared = "reconciled"
    #  approved = True
    #  payee_id = ???
    #  category_id = ???
    budget.transactions = filtered_transactions
    budget.subtransactions = filtered_subtransactions
    budget.payees = filtered_payees
    budget.months = filtered_months
    # print(json.dumps(sorted([p.name for p in filtered_payees]), indent=2))
    print(json.dumps(deleted_amounts, indent=2))
    print(f"{fake_payee_id=}")
    print(f"{inflow_category_id=}")

    # The end: print(budget_detail_response.model_dump_json())


if __name__ == "__main__":
    main(sys.argv[1:])
