# Helpful for nuances of interpreting data (e.g. category.category_group_name):
# https://github.com/actualbudget/actual/blob/master/packages/loot-core/src/server/importers/ynab5.ts

# TODO: make sure to take allowed fields approach not excluded fields approach.

from ynab import (
    Account,
    BudgetDetail,
    Category,
    CategoryGroup,
    MonthDetail,
    Payee,
    PayeeLocation,
    ScheduledSubTransaction,
    ScheduledTransactionSummary,
    SubTransaction,
    TransactionSummary,
)


def main():
    budget = BudgetDetail()
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

    a: Account = budget.accounts[-1]
    p: Payee = budget.payees[-1]
    pl: PayeeLocation = budget.payee_locations[-1]
    cg: CategoryGroup = budget.category_groups[-1]
    c: Category = budget.categories[-1]
    m: MonthDetail = budget.months[-1]
    t: TransactionSummary = budget.transactions[-1]
    st: SubTransaction = budget.subtransactions[-1]
    s_t: ScheduledTransactionSummary = budget.scheduled_transactions[-1]
    s_st: ScheduledSubTransaction = budget.scheduled_subtransactions[-1]

    # obfuscate these
    # Budget obf
    # name

    # Account obf:
    # name
    # note

    # Account del, ignored by importer:
    # balance
    # cleared_balance
    # uncleared_balance
    # debt_original_balance
    # debt_interest_rates
    # debt_minimum_payments
    # debt_escrow_amounts
    # last_reconciled_at

    # Payee obf:
    # name

    # PayeeLocation del: budget.payee_locations = []

    # CategoryGroup obf:
    # name

    # Category: obf
    # name
    # note
    # budgeted

    # Cateory: del
    # category_group_name = None
    # activity = 0
    # balance = 0
    # goal_creation_month = None
    # goal_target = None
    # goal_target_month = None
    # goal_percentage_complete = None
    # goal_months_to_budget = None
    # goal_under_funded = None
    # goal_overall_funded = None
    # goal_overall_left = None
    # goal_snoozed_at = None

    # MonthDetail obf
    # note
    # budgeted
    # income
    # activity

    # MonthDetail del
    # activity = 0
    # to_be_budgeted = 0
    # age_of_money = None

    # TransactionSummary: obf
    # amount
    # memo

    # TransactionSummary: del
    # flag_color = None
    # flag_name = None
    # import_payee_name = None
    # import_payee_name_original = None

    # SubTransaction: obf
    # amount
    # memo

    # SubTransaction: del
    # payee_name = None
    # category_name = None

    # ScheduledTransactionSummary del: budget.scheduled_transactions = []
    # ScheduledSubTransaction del: budget.scheduled_subtransactions = []
