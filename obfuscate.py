# Helpful for nuances of interpreting data (e.g. category.category_group_name):
# https://github.com/actualbudget/actual/blob/master/packages/loot-core/src/server/importers/ynab5.ts

# TODO: make sure to take allowed fields approach not excluded fields approach.

import argparse
import json
import random
import sys
from pathlib import Path
from typing import cast

from ynab import (
    Account,
    BudgetDetail,
    BudgetDetailResponse,
    Category,
    CategoryGroup,
    MonthDetail,
    Payee,
    SubTransaction,
    TransactionSummary,
)

from emojis import EMOJIS


CODEPOINT_RANGES = [(0x0020, 0xD800), (0xE000, 0xFDD0), (0xFDF0, 0xFFFE)]
CODEPOINT_COUNT = sum([r[1] - r[0] for r in CODEPOINT_RANGES])


def random_codepoint() -> int:
    index = random.randrange(CODEPOINT_COUNT)
    for start, end in CODEPOINT_RANGES:
        rlen = end - start
        if index < rlen:
            return start + index
        index -= rlen
    msg = "Internal error, ran out of codepoints"
    raise RuntimeError(msg)


def random_str() -> str:
    return random.choice(EMOJIS) + "".join(
        chr(random_codepoint()) for _ in range(random.randrange(10, 100))
    )


def random_mills() -> int:
    return random.randint(-5000 * 1000, 5000 * 1000)


def obfuscate_account(a: Account) -> Account:
    return Account(
        id=a.id,
        name=random_str(),
        note=random_str(),
        type=a.type,
        on_budget=a.on_budget,
        closed=a.closed,
        balance=0,
        cleared_balance=0,
        uncleared_balance=0,
        transfer_payee_id=a.transfer_payee_id,
        deleted=a.deleted,
    )


def obfuscate_budget(b: BudgetDetail) -> BudgetDetail:
    if (
        b.first_month is None
        or b.last_month is None
        or b.accounts is None
        or b.payees is None
        or b.payee_locations is None
        or b.category_groups is None
        or b.categories is None
        or b.months is None
        or b.transactions is None
        or b.subtransactions is None
        or b.scheduled_transactions is None
        or b.scheduled_subtransactions is None
    ):
        msg = "budget is missing key fields"
        raise Exception(msg)
    return BudgetDetail(
        id=b.id,
        name=random_str(),
        accounts=[obfuscate_account(a) for a in b.accounts],
        payees=[obfuscate_payee(p) for p in b.payees],
        payee_locations=[],
        category_groups=[obfuscate_category_group(g) for g in b.category_groups],
        categories=[obfuscate_category(c) for c in b.categories],
        months=[obfuscate_month(m) for m in b.months],
        transactions=[obfuscate_transaction(t) for t in b.transactions],
        subtransactions=[obfuscate_subtransaction(s) for s in b.subtransactions],
    )


def obfuscate_payee(p: Payee) -> Payee:
    return Payee(id=p.id, name=random_str(), deleted=p.deleted)


def obfuscate_category_group(g: CategoryGroup) -> CategoryGroup:
    return CategoryGroup(id=g.id, name=random_str(), hidden=g.hidden, deleted=g.deleted)


def obfuscate_category(c: Category) -> Category:
    return Category(
        id=c.id,
        category_group_id=c.category_group_id,
        name=random_str(),
        note=random_str(),
        hidden=c.hidden,
        budgeted=random_mills(),
        activity=0,
        balance=0,
        deleted=c.deleted,
    )


def obfuscate_month(m: MonthDetail) -> MonthDetail:
    return MonthDetail(
        month=m.month,
        note=random_str(),
        income=random_mills(),
        budgeted=random_mills(),
        activity=random_mills(),
        to_be_budgeted=0,
        deleted=m.deleted,
        categories=[obfuscate_category(c) for c in m.categories],
    )


def obfuscate_transaction(t: TransactionSummary) -> TransactionSummary:
    return TransactionSummary(
        id=t.id,
        date=t.var_date,
        amount=random_mills(),
        memo=random_str(),
        cleared=t.cleared,
        approved=t.approved,
        account_id=t.account_id,
        deleted=t.deleted,
    )


def obfuscate_subtransaction(s: SubTransaction) -> SubTransaction:
    return SubTransaction(
        id=s.id,
        transaction_id=s.transaction_id,
        amount=random_mills(),
        memo=random_str(),
        deleted=s.deleted,
    )


def main(argv: list[str]):
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--input", "-i", default="ynab-json/budget-in.json")
    _ = parser.add_argument("--output", "-o", default="ynab-json/budget-out.json")
    args = parser.parse_args(argv)
    input_path = Path(cast(str, args.input))
    output_path = Path(cast(str, args.output))

    with input_path.open("r") as f:
        budget_detail_response = BudgetDetailResponse.from_dict(json.load(f))  # pyright: ignore[reportAny]
    if budget_detail_response is None:
        msg = "Bad JSON"
        raise RuntimeError(msg)
    budget_in = budget_detail_response.data.budget
    budget_out = obfuscate_budget(budget_in)
    _ = output_path.write_text(
        budget_out.model_dump_json(by_alias=True, exclude_unset=True, indent=2)
    )


if __name__ == "__main__":
    main(sys.argv[1:])
