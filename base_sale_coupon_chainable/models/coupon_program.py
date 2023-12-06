# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def sorted(self, key=None, reverse=False):
        # Prevent this patch
        # https://github.com/odoo/odoo/commit/03fb134b89c6739e14ed9426930c91d50b25d896
        # from ignoring applied programs order and putting fixed_amount at bottom
        # https://github.com/odoo/odoo/blob/14.0/addons/sale_coupon/models/sale_order.py#L437
        # since programs can be ordered:
        if (
            key
            and callable(key)
            and key.__module__ == "odoo.addons.sale_coupon.models.sale_order"
        ):
            return self

        return super().sorted(key=key, reverse=reverse)
