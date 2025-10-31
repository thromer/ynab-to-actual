import argparse
import json
import sys
from collections import defaultdict
from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from collections.abc import Mapping

from datetime import date, datetime, timedelta
from operator import itemgetter
from pathlib import Path
from uuid import uuid4

from ynab import (
    Account,
    BudgetDetailResponse,
    TransactionClearedStatus,
    TransactionSummary,
)


def account_names_to_ids(
    account_name_dict: Mapping[str, Account], account_names: set[str]
):
    missing: list[str] = []
    for a in account_names:
        if a not in account_name_dict:
            missing.append(a)
    if missing:
        message = f"No such account(s): {missing}"
        raise Exception(message)
    return set([a.id for a in account_name_dict.values() if a.name in account_names])


def main(argv: list[str]):
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--input", "-i", default="ynab-json/budget-in.json")
    _ = parser.add_argument("--output", "-o", default="ynab-json/budget-out.json")
    _ = parser.add_argument(
        "--start", "-s", required=True, help="Start date in YYYY-MM-DD format"
    )
    _ = parser.add_argument(
        "--accounts",
        "-a",
        default="",
        help="Comma-separated list of account names to filter. If omitted filters all accounts",
    )
    _ = parser.add_argument(
        "--exclude",
        "-x",
        default="",
        help="Comma-separated list of account names to exclude from filtering.",
    )
    _ = parser.add_argument(
        "--drop", "-d", action="store_true", help="Drop accounts with no transactions"
    )
    _ = parser.add_argument("--unapproved_prefix", "-u", default="#review")
    args = parser.parse_args(argv)
    input_path = Path(cast(str, args.input))
    output_path = Path(cast(str, args.output))
    start = datetime.strptime(cast(str, args.start), "%Y-%m-%d").date()
    unapproved_prefix = cast(str, args.unapproved_prefix).strip()
    target_account_names = set(
        [a.strip() for a in cast(str, args.accounts).split(",") if a]
    )
    exclude_account_names = set(
        [a.strip() for a in cast(str, args.exclude).split(",") if a]
    )
    if bool(target_account_names) and bool(exclude_account_names):
        msg = "Specify at most one of --accounts or --exclude"
        raise Exception(msg)
    drop = cast(bool, args.drop)

    with input_path.open("r") as f:
        budget_detail_response = BudgetDetailResponse.from_dict(json.load(f))  # pyright: ignore[reportAny]
    if budget_detail_response is None:
        msg = "Bad JSON"
        raise Exception(msg)
    budget = budget_detail_response.data.budget
    if (
        budget.first_month is None
        or budget.last_month is None
        or budget.accounts is None
        or budget.payees is None
        or budget.payee_locations is None
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
    accounts = budget.accounts
    payees = budget.payees
    category_groups = budget.category_groups
    categories = budget.categories
    months = budget.months
    transactions = budget.transactions
    subtransactions = budget.subtransactions
    scheduled_transactions = budget.scheduled_transactions
    scheduled_subtransactions = budget.scheduled_subtransactions
    account_name_dict = {a.name: a for a in accounts}
    target_accounts = account_names_to_ids(account_name_dict, target_account_names)
    exclude_accounts = account_names_to_ids(account_name_dict, exclude_account_names)
    if not target_accounts:
        keep_accounts = exclude_accounts
    else:
        keep_accounts = set([a.id for a in accounts if a.id not in target_accounts])

    # For stats only (AFAIK)
    adict = {a.id: a for a in accounts}
    tcount: defaultdict[str, int] = defaultdict(int)
    latest: defaultdict[str, date] = defaultdict(lambda: date.min)
    for t in transactions:
        tcount[t.account_id] += 1
        if t.var_date > latest[t.account_id]:
            latest[t.account_id] = t.var_date
    # for a in accounts:
    #  print(f"{a.name} {tcount[a.id]} transactions")
    for a_id, count in sorted(tcount.items(), key=itemgetter(1), reverse=True):
        print(f"{adict[a_id].name}: {count} transactions, latest {latest[a_id]}")

    print(f"{budget.first_month=}")
    print(f"{budget.last_month=}")
    print(f"{len(accounts)=}")
    print(f"{len(payees)=}")
    print(f"{len(category_groups)=}")
    print(f"{len(categories)=}")
    print(f"{len(months)=}")
    print(f"{len(transactions)=}")
    print(f"{len(subtransactions)=}")
    print(f"{len(scheduled_transactions)=}")
    print(f"{len(scheduled_subtransactions)=}")
    # print(budget.months[-1].model_dump_json(by_alias=True, exclude_unset=True, indent=2))
    print(f"Last month in list={budget.months[-1].month}")
    print(transactions[-1].model_dump_json(by_alias=True, exclude_unset=True, indent=2))
    # print(subtransactions[0].model_dump_json(by_alias=True, exclude_unset=True, indent=2))

    filtered_transactions = [
        t for t in transactions if t.account_id in keep_accounts or t.var_date >= start
    ]
    if unapproved_prefix:
        for t in filtered_transactions:
            if not t.approved:
                orig_memo = (t.memo or "").strip()
                t.memo = f"{unapproved_prefix}{f' {orig_memo}' if orig_memo else ''}"
    ftdict = {t.id: t for t in filtered_transactions}
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
        [fake_payee_id]
        + [t.payee_id for t in filtered_transactions if t.payee_id is not None]
        + [s.payee_id for s in filtered_subtransactions if s.payee_id is not None]
    )
    filtered_payees = [p for p in payees if p.id in filtered_payee_ids]
    filtered_months = [m for m in months if m.month >= start]

    if drop:
        ftcount: defaultdict[str, int] = defaultdict(int)
        for t in filtered_transactions:
            ftcount[t.account_id] += 1
        filtered_accounts = [a for a in accounts if ftcount[a.id] > 0]
    else:
        filtered_accounts = accounts

    print(f"{len(filtered_accounts)=}")
    print(f"{len(filtered_transactions)=}")
    print(f"{len(filtered_subtransactions)=}")
    print(f"{len(filtered_payees)=}")
    print(f"{len(filtered_months)=}")

    balance_forward_transactions = [
        TransactionSummary(
            id=str(uuid4()),
            date=start - timedelta(days=1),
            amount=amount,
            cleared=TransactionClearedStatus.RECONCILED,
            approved=True,
            account_id=account_id,
            deleted=False,
            payee_id=fake_payee_id,
            category_id=inflow_category_id,
            memo="Balance forward",
        )
        for account_id, amount in deleted_amounts.items()
        if amount != 0
    ]

    budget.first_month = max(
        filtered_months[-1].month, date(start.year, start.month, 1)
    )
    budget.accounts = filtered_accounts
    budget.transactions = filtered_transactions + balance_forward_transactions
    budget.subtransactions = filtered_subtransactions
    budget.payees = filtered_payees
    budget.months = filtered_months
    # print(json.dumps(sorted([p.name for p in filtered_payees]), indent=2))
    for t in balance_forward_transactions:
        print(
            adict[t.account_id].name,
            t.model_dump_json(by_alias=True, exclude_unset=True, indent=2),
        )

    _ = output_path.write_text(
        budget_detail_response.model_dump_json(
            by_alias=True, exclude_unset=True, indent=2
        )
    )


if __name__ == "__main__":
    main(sys.argv[1:])
