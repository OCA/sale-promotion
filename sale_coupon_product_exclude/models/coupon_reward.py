# Copyright 2022 Dinar Gabbasov
# Copyright 2022 Ooops404
# Copyright 2022 Cetmix
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    exclude_products_domain = fields.Char(
        string="Exclude Products",
    )
