To configure free product rewards from domains:

#. Go to *Sales > Products > Coupon Programs* and select or create a new one.
#. Choose the criteria of appliance you want to use and the minimum quantities, that
   will be used to calculate the times the rewards can be applied.
#. On the *Reward Type* field choose *Free Product Domain*.
#. Set the proper domain and rules.
#. If you want to apply the limits for every product in the promotion limit, set the
   *Strict per product limit* checkbox.

An example with the domain `[("id", "in", [1, 2])]`, strict limits and minimum quantity
of 2 units:


 ===== ==================
  Qty      Products
 ===== ==================
    4   `product.product(1,)`
    2   `product.product(2,)`
    6   `product.product(3,)`
 ===== ==================

For `product.product(1,)` we'll get 2 units as reward.
For `product.product(2,)` we'll get just 1.
We'll get nothing from `product.product(3,)`
