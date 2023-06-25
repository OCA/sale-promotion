# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleCoupon(models.Model):
    _inherit = "sale.coupon"

    def _check_coupon_code(self, order):
        """All the partners in the commercial entity can use their common coupons"""
        message = super()._check_coupon_code(order)
        # String comparison isn't a great way to check it, but we don't have a better
        # hook as there's no way to check if the error came before or after that fail
        if message.get("error", "") == _("Invalid partner."):
            if (
                self.partner_id.commercial_partner_id
                == order.partner_id.commercial_partner_id
            ):
                message.pop("error")
        return message
