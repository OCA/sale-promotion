# Copyright 2022 Ooops404
# Copyright 2022 Dinar Gabbasov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _set_reward_discount_for_lines(self, program):
        if (
            program.discount_apply_on == "specific_products"
            and program.discount_apply_on_domain_product
        ):
            domain = program.rule_products_domain
            super()._set_reward_discount_for_lines(
                program.with_context(promo_domain_product=domain)
            )
        else:
            super()._set_reward_discount_for_lines(program)
