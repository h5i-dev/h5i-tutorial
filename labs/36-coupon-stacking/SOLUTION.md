# Lab 36 — Checkout

## The bug

```python
for code in coupons:
    if code not in COUPONS:
        return js({"error": "unknown coupon"}, 400)
percent = sum(COUPONS[c] for c in coupons)
total = PRICES[item] * (100 - percent) // 100
```

Every individual field is validated. The item exists, the coupons exist, the
list is a list. What is missing is a *rule*: a coupon may be used once, the
total discount is capped, and a price may not go below zero.

That rule lives in a marketing document and in everybody's head. It was never
written as code, so it is not enforced, and nothing about the code looks wrong.

## The exploit

```bash
h5i websec replay req_0 --session lab36 --create \
    --set method=POST --set path=/api/checkout \
    --set header.Content-Type=application/json \
    --set json.item=enterprise-license \
    --set 'json.coupons=["FRIEND25","FRIEND25","FRIEND25","FRIEND25"]'
```

Note the JSON typing again (Lab 09, Lab 15): the value parses as JSON, so it is
sent as an **array**. Sent as a string it would fail the `isinstance` check and
you would wrongly conclude the endpoint was strict.

## Why logic bugs are the ones scanners miss

There is no dangerous function here. No `eval`, no concatenated SQL, no
untrusted deserialisation. A scanner sees a well-validated JSON API. The bug is
visible only to someone who knows what the feature is *supposed* to mean — which
is why business logic testing is where a human, or an agent with the application
in front of it, beats a tool.

The method is to state the invariants out loud and then attack each one:

> "A coupon can be used once." → send it twice
> "You cannot discount below zero." → stack until it is negative
> "You cannot buy what you cannot afford." → make the total negative or zero
> "Steps happen in order." → skip step two (Lab 39)
> "This can only happen once." → race it (Lab 35)
> "Quantity is a positive integer." → send `-3`, `0`, `1e9`, `1.5`, `"1"`

## The checklist for a checkout

Every one of these has been a real, paid bug bounty:

* repeat the same coupon; combine coupons marked exclusive
* negative quantity, negative price, negative shipping
* integer overflow on quantity × price
* currency confusion — pay in a currency worth less, receive in one worth more
* rounding: buy 100 items at 0.4 cents each, rounded down per item
* apply the discount, then change the basket, then pay
* cancel an order after shipping; refund to a different account
* re-use a payment confirmation token for a second order
* change the price parameter (Lab 02) — always try the simple one first

## The fix

Write the rule as code, in one place, and make it a property of the data:

```python
codes = set(coupons)                       # once each
if len(codes) > 1 and not stackable(codes):
    reject()
percent = min(sum(COUPONS[c] for c in codes), MAX_DISCOUNT)
total = max(PRICES[item] * (100 - percent) // 100, 0)
```

Then mark coupons as redeemed transactionally (Lab 35), and re-price the whole
basket server-side at the moment of payment rather than trusting anything the
client accumulated.

## h5i technique

JSON arrays as `--set` values; and the habit of asking what the feature *means*
before asking what it does.
