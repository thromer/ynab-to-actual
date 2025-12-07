# Notes

## Logic
* Accounts are all added (not sure what happens if name already exists).
* Category groups are all added, with unique suffix (-1, -2, etc).
* Categories are all added, with unique suffix (-1, -2, etc).
* Payees are unconditionally added (not sure what happens if name exists).
* Transactions are complicated

## Importing on top of existing budget

Proposal: copy ynab5.ts, get it to compile standalone, modify it to
check for existing accounts, category groups, categories, and payees
instead of unconditionally adding them. This won't play nice if the
source budget actually had duplicate category group names and
duplicate categories. (In that case you should probably rename them in
YNAB before producing your json file).

## Importer code

* https://github.com/actualbudget/actual/blob/master/packages/loot-core/src/server/importers/ynab5.ts


