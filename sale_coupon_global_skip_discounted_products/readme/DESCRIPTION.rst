This module adds a new option in promotion/coupon programs that allows to skip discounted products in global discounts computation.

/!\ This module is not compatible with the module sale_coupon_delivery /!\
It can be fixed by using the patches from base_sale_coupon_chainable that restores
the super() call in get_paid_order_lines() 
