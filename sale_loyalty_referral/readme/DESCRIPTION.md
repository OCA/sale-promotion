Personal referral links for partners — customers, influencers, ambassadors.

Use cases:

- Classic referral: a customer shares their link; the friend's first order
  gets a discount.
- Influencer code: an ambassador's link tracks and discounts the sales they
  drive.
- Tracking only: a referral program without rewards keeps pure attribution —
  `referred_by_id` on orders, no discount.

How it works:

- Each partner can get a unique referral code and a shareable link, 
  from the referral program's "Generate Referral Code" button,
  the partner form/list (for a default referral program),
  or the partner's portal (same).
- The code is a "Discount Code" program, so it works everywhere promo codes
  do: sale order coupon wizard and eCommerce promo box. In POS it applies
  automatically on the carried-over sale order; typing a referral code at the
  POS till needs a pos_loyalty extension.
- Each referral program owns one internal "Conditional Rule" with a random
  code. It is plumbing, not a user code: typed referral codes alias it behind
  the scenes, and it refuses to apply on orders without a referrer. Do not
  share or edit it — put shared conditions on it instead.
- Referral links land on a configurable base URL with `?referral=<code>`, 
  captured on any page (session + cookie): attribution can survive navigation,
  logins and browser restarts.
- Orders record the referrer in `referred_by_id`, whether the code came from
  the link or was typed at checkout.
