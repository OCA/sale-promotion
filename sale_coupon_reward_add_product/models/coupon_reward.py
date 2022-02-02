# Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    reward_product_add_if_missing = fields.Boolean(
        string="Add reward product to the order automatically",
        help="If checked, the reward product will be automatically added to the order",
    )
