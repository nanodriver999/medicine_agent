# Offline checkpoint / resume

```bash
amo resume --input data/fixtures/smiles.csv --policy rules --seed 42 \
  --budget 5 --out outputs/resumable_rules
# The same command resumes using checkpoint.json, if present.
```

The atomic JSON checkpoint stores evaluated canonical structures, a call ledger
and immutable identity containing policy/seed/budget/input hash/oracle revision.
A repeat invocation refuses altered parameters and skips already-evaluated inputs.

**Scope boundary:** this is an *offline fixture* recovery test. It does not
yet guarantee exactly-once external ADMET inference/billing if the process dies
after contacting a provider but before a checkpoint is written. Future production
use requires a durable pre-call journal and provider idempotency/cache semantics.

`max_new_calls` is exposed only as a Python test hook to simulate interruption.
