# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    reward_type = fields.Selection(
        selection_add=[("discount_line", "Discount in Line")],
    )
