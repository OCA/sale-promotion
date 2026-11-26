# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    sale_order_type_ids = fields.Many2many(
        comodel_name="sale.order.type",
        string="Sales Order Types",
        help="Restrict the loyalty program to those sale order types.",
    )
