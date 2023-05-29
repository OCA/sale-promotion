# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        exception_msg = self.evaluate_risk_message(
            self.partner_invoice_id.commercial_partner_id
        )
        if exception_msg and not self.env.context.get("bypass_risk"):
            self = self.with_context(risk_exceeded=True)
        elif self.env.context.get("risk_exceeded"):
            self = self.with_context(risk_exceeded=False)
        return super().action_confirm()

    def _send_reward_coupon_mail(self):
        if self.env.context.get("risk_exceeded"):
            return
        return super()._send_reward_coupon_mail()
