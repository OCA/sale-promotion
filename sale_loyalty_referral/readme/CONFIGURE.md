1. Enable loyalty: Sales > Settings > Pricing > "Promotions, Loyalty & Gift Card".
2. Create the referral program from the **Referral** tile (Sales > Products >
   Discount & Loyalty > New). It is a "Discount Code" program with a preset
   reward; adjust the reward to taste.
3. In Sales > Settings > "Customer Referrals", select the program as
   "Referral Program" and set "Referral Base URL" (default `/`; any Odoo
   page works — a landing page, `/appointment`, etc.).
4. The selected program shows a "Default Referral Program" ribbon on its
   form, a "Referral Codes" smart button listing minted codes, and a
   "Generate Referral Code" button.
5. To let partners generate their own link, drag the "Invite a Friend" building
   block (Social category) onto a website page in the editor. It is only
   rendered for logged-in users.

With `sale_loyalty_order_count_condition` installed, the program gains an
"Order Count Condition" field — set it once at program level (e.g.
"Customer's first order") and every minted code shares the policy. It relies
on partner identity: guest checkouts create fresh partners, so repeated
anonymous visitors may still pass a "first order" check.
