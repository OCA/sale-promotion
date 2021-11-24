# Copyright 2021 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CouponRule(models.Model):
    _inherit = "coupon.rule"

    rule_date_field = fields.Selection(
        [
            ("date_order", "Order date"),
            ("commitment_date", "Commitment date"),
        ],
        string="Date Field",
        help="Which date to use to check coupon's validity",
        default="date_order",
        required=True,
    )
