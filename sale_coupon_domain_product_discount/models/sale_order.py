# Copyright 2022 Ooops404
# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_reward_values_discount(self, program):
        """We simply inject the context in order to gather the proper discounted
        products according to the current domain"""
        if (
            program.discount_apply_on_domain_product
            and program.discount_apply_on == "specific_products"
        ):
            return super()._get_reward_values_discount(
                program.with_context(promo_domain_product=program.rule_products_domain)
            )
        return super()._get_reward_values_discount(program)
