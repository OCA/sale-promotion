# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleCouponProgram(models.Model):
    _inherit = "coupon.program"

    def _compute_order_count(self):
        """Relay on the order line link for these programs instead of the discount
        products"""
        free_product_domain_programs = self.filtered(
            lambda x: x.reward_type == "free_product_domain"
        )
        res = super(
            SaleCouponProgram, self - free_product_domain_programs
        )._compute_order_count()
        for program in free_product_domain_programs:
            orders = self.env["sale.order.line"].read_group(
                [("coupon_program_id", "=", program.id)],
                ["order_id"],
                ["order_id"],
            )
            program.order_count = len(orders)
        return res

    def action_view_sales_orders(self):
        res = super().action_view_sales_orders()
        if self.reward_type != "free_product_domain":
            return res
        orders = (
            self.env["sale.order.line"]
            .search([("coupon_program_id", "=", self.id)])
            .mapped("order_id")
        )
        res["domain"] = [("id", "in", orders.ids)]
        return res
