# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _compute_order_count(self):
        """Relay on the order line link for these programs instead of the discount
        products"""
        multi_gift_programs = self.filtered(lambda x: x.reward_type == "multi_gift")
        super(CouponProgram, self - multi_gift_programs)._compute_order_count()
        for program in multi_gift_programs:
            orders = self.env["sale.order.line"].read_group(
                [
                    ("state", "not in", ["draft", "sent", "cancel"]),
                    ("coupon_program_id", "=", program.id),
                ],
                ["order_id"],
                ["order_id"],
            )
            program.order_count = len(orders)

    def action_view_sales_orders(self):
        res = super().action_view_sales_orders()
        if self.reward_type != "multi_gift":
            return res
        orders = (
            self.env["sale.order.line"]
            .search([("coupon_program_id", "=", self.id)])
            .mapped("order_id")
        )
        res["domain"] = [
            ("id", "in", orders.ids),
            ("state", "not in", ["draft", "sent", "cancel"]),
        ]
        return res
