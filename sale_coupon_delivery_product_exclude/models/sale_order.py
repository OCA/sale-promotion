# Copyright 2022 Dinar Gabbasov
# Copyright 2022 Ooops404
# Copyright 2022 Cetmix
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_cheapest_line(self):
        program = self.env.context.get("current_coupon_program")
        if program:
            return min(
                self.order_line.filtered(
                    lambda x: not x.is_reward_line
                    and not x.is_delivery
                    and x.price_reduce > 0
                    and not program._is_excluded_product(x.product_id)
                ),
                key=lambda x: x["price_reduce"],
            )
        else:
            return super(SaleOrder, self)._get_cheapest_line()
