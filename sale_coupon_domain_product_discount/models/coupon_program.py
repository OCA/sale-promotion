# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleCouponProgram(models.Model):
    _inherit = "sale.coupon.program"

    def _filter_not_ordered_reward_programs(self, order):
        """
        Returns the programs when the reward is actually in the order lines
        """
        domain_discount_programs = self.filtered(
            lambda x: x.discount_apply_on_domain_product
            and x.discount_apply_on == "specific_products"
        )
        programs = super(
            SaleCouponProgram, self - domain_discount_programs
        )._filter_not_ordered_reward_programs(order)
        for program in domain_discount_programs:
            discount_specific_product_ids = program.with_context(
                promo_domain_product=program.rule_products_domain
            ).discount_specific_product_ids
            if not order.order_line.filtered(
                lambda line: line.product_id in discount_specific_product_ids
            ):
                continue
            programs |= program
        return programs
