# Copyright 2022 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _filter_not_ordered_reward_programs(self, order):
        """Inject the domain for the domain discount programs"""
        domain_discount_programs = self.filtered(
            lambda x: x.discount_apply_on_domain_product
            and x.discount_apply_on == "specific_products"
        )
        programs = super(
            CouponProgram, self - domain_discount_programs
        )._filter_not_ordered_reward_programs(order)
        order_products = order.order_line.product_id
        for program in domain_discount_programs:
            domain = program.rule_products_domain
            # In this case, we need to preevaluate the domain along with every line
            # affected
            if program.strict_per_product_limit:
                domain = order._get_reward_values_discount_strict_limit_lines(program)
            discount_specific_product_ids = program.with_context(
                promo_domain_product=domain
            ).discount_specific_product_ids
            if any(p in order_products for p in discount_specific_product_ids):
                programs += program
        return programs
