# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    suggested_promotion_ids = fields.Many2many(
        comodel_name="sale.coupon.program", compute="_compute_suggested_promotion_ids",
    )

    @api.depends("product_id")
    def _compute_suggested_promotion_ids(self):
        self.suggested_promotion_ids = False
        for line in self.filtered("product_id"):
            line.suggested_promotion_ids = line.order_id.with_context(
                product_id=line.product_id.id
            )._available_multi_criteria_multi_gift_programs()
