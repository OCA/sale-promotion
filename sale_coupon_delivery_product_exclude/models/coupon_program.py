# Copyright 2022 Dinar Gabbasov
# Copyright 2022 Ooops404
# Copyright 2022 Cetmix
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _is_excluded_product(self, products):
        self.ensure_one()
        if (
            self.reward_type not in ["free_shipping", "product"]
            and self.exclude_products_domain
            and self.exclude_products_domain != "[]"
        ):
            domain = ast.literal_eval(self.exclude_products_domain)
            return bool(products.filtered_domain(domain))
        return super()._is_excluded_product(products)
