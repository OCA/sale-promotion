# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleCouponProgram(models.Model):
    _inherit = "sale.coupon.program"

    next_order_program_id = fields.Many2one(
        comodel_name="sale.coupon.program",
        domain=[("program_type", "=", "coupon_program")],
    )

    @api.onchange("promo_applicability")
    def _onchange_promo_applicability(self):
        """Remove the destination program on as all would behave in unexpected ways"""
        if self.promo_applicability == "on_current_order":
            self.next_order_program_id = False

    def _compute_coupon_count(self):
        """Hook the destination program coupon counter"""
        next_programs = self.filtered("next_order_program_id")
        for program in next_programs:
            program.coupon_count = program.next_order_program_id.coupon_count
        return super(SaleCouponProgram, (self - next_programs))._compute_coupon_count()

    def _compute_order_count(self):
        """Hook the destination program sales counter"""
        next_programs = self.filtered("next_order_program_id")
        for program in next_programs:
            program.order_count = program.next_order_program_id.order_count
        return super(SaleCouponProgram, (self - next_programs))._compute_order_count()

    def action_next_order_program_coupons(self):
        """Hook the destination program coupon action"""
        action = self.env["ir.actions.act_window"].for_xml_id(
            "sale_coupon", "sale_coupon_action"
        )
        action["domain"] = [("program_id", "=", self.next_order_program_id.id)]
        return action

    def action_view_sales_orders(self):
        """Hook the destination program sales action"""
        if self.next_order_program_id:
            return self.next_order_program_id.action_view_sales_orders()
        return super().action_view_sales_orders()
