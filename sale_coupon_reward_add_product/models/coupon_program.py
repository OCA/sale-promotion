# Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _check_promo_code(self, order, coupon_code):
        # OVERRIDE to skip the _is_reward_in_order_lines check
        if self.reward_product_add_if_missing:
            order = order.with_context(check_reward_in_order_lines=False)
        return super()._check_promo_code(order, coupon_code)

    def _filter_programs_on_products(self, order):
        # OVERRIDE
        records = super()._filter_programs_on_products(order)
        # Just like super, map ordered product quantities
        order_lines = (
            order.order_line.filtered("product_id") - order._get_reward_lines()
        )
        products = order_lines.product_id
        products_qties = dict.fromkeys(products, 0)
        for line in order_lines:
            products_qties[line.product_id] += line.product_uom_qty
        # Handle discarded programs by super()
        for rec in self:
            if (
                rec.promo_applicability == "on_current_order"
                and rec.promo_code_usage == "code_needed"
                and rec.reward_type == "product"
                and rec.reward_product_add_if_missing
                and rec not in records
            ):
                # The original method will discard the program if the reward product
                # is not included in the current order's products.
                # But since we're adding it automatically, we need to account for the
                # reward product that's going to be added too.
                valid_products = rec._get_valid_products(products)
                ordered_rule_products_qty = sum(
                    products_qties[product] for product in valid_products
                )
                required_products_qty = (
                    rec.rule_min_quantity - rec.reward_product_quantity
                )
                if ordered_rule_products_qty >= required_products_qty:
                    records += rec
        return records

    def _filter_not_ordered_reward_programs(self, order):
        # OVERRIDE to avoid filtering out programs where the reward is missing but
        # it's going to be added automatically anyways.
        records_to_keep = self.filtered(
            lambda rec: (
                rec.reward_type == "product"
                and rec.promo_code_usage == "code_needed"
                and rec.reward_product_add_if_missing
            )
        )
        records_to_filter = self - records_to_keep
        programs = super(
            CouponProgram, records_to_filter
        )._filter_not_ordered_reward_programs(order)
        return programs | records_to_keep
