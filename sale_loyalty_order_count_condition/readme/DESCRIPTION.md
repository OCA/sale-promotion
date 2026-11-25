Adds an order-count condition to loyalty rules and programs: a program or rule
can be restricted to the customer's first order ever, the first order using
that code, or repeat orders in either scope. Counts confirmed sale orders
only. A program-level condition applies to all its rules — e.g. every code
minted under a referral program.

Typical uses: a promo code usable once per customer, a welcome discount on the
first purchase, or an offer reserved to returning customers.

Known limitation: when a program mixes conditioned and unconditioned rules, a
failing conditioned rule does not block the program — the unconditioned rule
still applies. POS promo-code entry (pos_loyalty) evaluates rules client-side
and does not enforce this condition.
