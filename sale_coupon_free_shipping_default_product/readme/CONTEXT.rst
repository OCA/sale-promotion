BUSINESS NEED:
This module addresses the issue of multiple "Free Shipping" products being 
created whenever new promotion programs are configured. This redundancy leads 
to inefficiencies and unnecessary clutter in the product database. Additionally, 
while the "Free Shipping" product is set in the reward line product field, it is 
not configured as a default product for free shipping.

APPROACH
The apporach that we use was to inherit the couponProgram class and then change 
the functionality of the create function.
The method checks if the reward_type in the vals dictionary is set to 
"free_shipping".
If the condition is met, it retrieves the default "free shipping" product 
configured at the company level using self.env.company.free_shipping_product_default.
If a default product is found, its ID is assigned to the discount_line_product_id
field in vals.


USEFUL INFORMATION:
This module depends on modules sale and coupon.
Different companies can choose different default products for free shipping.



