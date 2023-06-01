# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleCoupon(models.Model):
    _inherit = "coupon.coupon"

    can_be_applied_to_order = fields.Boolean(
        compute="_compute_can_be_applied_to_order",
        compute_sudo=True,
    )

    @api.depends_context("active_id")
    def _compute_can_be_applied_to_order(self):
        self.can_be_applied_to_order = False
        if self.env.context.get("active_model", "") != "sale.order":
            return
        order = self.env["sale.order"].browse(self.env.context.get("active_id"))
        for coupon in self:
            self.can_be_applied_to_order = not coupon._check_coupon_code(
                order.date_order.date(), order.partner_id.id, order=order
            )

    def action_apply_partner_coupon(self):
        if self.env.context.get("active_model", "") != "sale.order":
            return
        self.env["sale.coupon.apply.code"].sudo().new(
            {"coupon_code": self.code}
        ).process_coupon()
        return (
            self.env["sale.order"]
            .browse(self.env.context.get("active_id"))
            .get_formview_action()
        )
