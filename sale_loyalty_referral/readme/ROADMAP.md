**Status:** shipped

## Decisions
- Referral codes live as `with_code` rules on a `promo_code` program — the
  only loyalty type where one code serves unlimited distinct consumers.
  - Rejected: `loyalty.card` per referrer — card `partner_id` means
    holder-as-spender, and its point entries are zeroed when the spender
    differs; points balance is finite, referrals need unlimited uses.
  - Rejected: `program_type='referral'` — every `program_type` branch in
    Python and POS JS would need extending; a 'referral' template tile gives
    the same UX with zero behavioral surface.
- Participation is a `loyalty.referral` link record (partner × program,
  mirroring `loyalty.card`'s shape) owning the promo rule. *2026-10 —
  supersedes "rejected: dedicated referral.code model": the model is not a
  duplicate registry but the referral-domain object; the rule stays pure
  promo plumbing. Gives multi-code/multi-program per partner for free.*
- `?referral=` query param captured on `ir.http._post_dispatch` — works on
  any landing page, survives navigation; replaces the dedicated
  `/referral/<code>` route idea. UTM is kept as optional analytics only.
- Code generation is opt-in (portal button, partner Action menu, program
  button). *2026-10 — supersedes lazy mint-on-read.*
- Referral program is selected in Sales Settings (`ir.config_parameter`).
  *2026-10 — supersedes the `is_referral` flag + `referral_base_url` field on
  `loyalty.program`: explicit selection beats "first flagged wins".*
- One rule per customer carries `referrer_id` — the code registry and the
  owner link in one place. `_try_apply_code` stamps `referred_by_id` on
  orders, covering manually typed codes too.
- Application failures post a chatter note on the order rather than only
  logging; no exception activity (too much noise for expected outcomes).
- Seed program via XML + post-init hook for params/reward — the reward's
  discount product needs conditional handling for `website_sale`'s required
  `publish_date`, which XML cannot express portably.

## Plan
- Iteration 1: generic engine (codes, links, capture, portal, apply helper).
- Iteration 2: surface bridges (website_sale cart, appointment/POS layer in
  `brb_appointment_referral`).
- Iteration 3: referrer reward (issue the referrer a `next_order_coupons`/
  eWallet card on friend conversion — `loyalty.card` is the right model for
  that direction).

## Tasks
- [ ] OCA contribution: port to OCA/sale-promotion (naming `sale_loyalty_referral`
      under consideration), OCA CLA.
- [ ] Verify POS loyalty bookkeeping (`loyalty.history`, usage counts) when a
      `pos.order` consumes an SO reward line.
- [ ] Referrer reward program (see Iteration 3).
- [ ] Multi-company/multi-website semantics if needed (program-level
      company/website scoping is the escape hatch).
