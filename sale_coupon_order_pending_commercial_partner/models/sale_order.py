# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _partner_coupon_domain(self):
        """Override to do a broader search"""
        return [("partner_id", "child_of", self.partner_id.commercial_partner_id.id)]
