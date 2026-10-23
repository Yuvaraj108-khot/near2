# The Solver Race

**Category** Web / **Difficulty** Medium-Hard / **Points** 300 / **Flag format** `NEAR{...}`

> On NEAR Intents, a user broadcasts what they *want* and a crowd of **solvers**
> race to fill it. The settlement pool pays the best quote — the lowest ask —
> and the ledger swears each intent settles **only once**.
>
> You are a solver. The pool in front of you holds more than every open intent
> is worth. Honest work will never empty it. But the pool keeps its promise of
> "only once" with a receipt... and a receipt is only as good as what it
> commits to.
>
> Drain the pool to exactly **0** and the sealed settlement receipt is yours.

## How to run

The challenge is a live HTTP service. Point your tools at the URL the
organizers give you (below written as `$URL`, e.g. `http://HOST:5000`).

```
GET  $URL/            # service info + endpoint list
POST $URL/register    # {} -> your own fresh, isolated pool + a solver token
POST $URL/quote       # {token, intent_id, ask} -> post or revise your quote
POST $URL/settle      # {token, intent_id} -> the pool pays you an intent's reward
POST $URL/withdraw    # {token} -> sweep your credited balance
GET  $URL/state       # ?token=... -> inspect pool / intents / balance
GET  $URL/receipt     # ?token=... -> the sealed receipt; unseals at pool == 0
```

Every registration gets its own pool, so you can experiment freely without
stepping on other teams. Example first move:

```
curl -s $URL/register -XPOST -H 'content-type: application/json' -d '{}'
```

## Hints

1. Register and read the `note`. Add up every intent's reward. Compare that to
   the pool. Honest settling leaves money on the table — on purpose.
2. Watch the `/settle` response. What exactly does the pool hand back, and what
   does it decide to remember so it won't pay you twice?
3. "Only once" is enforced against a *receipt*, not against an intent. What goes
   into that receipt? Which of those parts can you change?
4. `/quote` lets a solver *revise* a quote they are already winning. A revision
   changes one of the ingredients of the receipt.
5. So settle, revise, settle, revise. Each fresh quote is a fresh receipt the
   pool has never paid before.
6. The pool pays a fixed reward per settle and the pool is a whole multiple of
   it. Land on exactly 0, then `GET /receipt`.
