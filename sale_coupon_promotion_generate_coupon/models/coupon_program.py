# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _compute_order_count(self):
        """Hook the destination program sales counter"""
        next_programs = self.filtered("next_order_program_id")
        for program in next_programs:
            program.order_count = program.next_order_program_id.order_count
        return super(CouponProgram, (self - next_programs))._compute_order_count()

    def action_view_sales_orders(self):
        """Hook the destination program sales action"""
        if self.next_order_program_id:
            return self.next_order_program_id.action_view_sales_orders()
        return super().action_view_sales_orders()
