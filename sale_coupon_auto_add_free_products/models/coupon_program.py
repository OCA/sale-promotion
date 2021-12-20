# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    auto_add_free_products = fields.Boolean(
        "Automatically adds free products",
        default=False,
        help="Allow this program to automatically adds free products.",
    )

    always_reward_product = fields.Boolean(
        "Always reward product",
        default=False,
        help="This program should always reward product regardless of the "
        "products domain. (i.e. This is not a 1+1 free program)",
    )

    def _get_valid_products(self, products):
        # If always reward product is set, we always consider it does not apply
        # to itself
        if self.auto_add_free_products and self.always_reward_product:
            return self.env["product.product"].browse()
        return super()._get_valid_products(products)

    def _filter_programs_on_products(self, order):
        programs = super()._filter_programs_on_products(order)
        for program in self:
            # If always reward product is set, we need to consider
            # it as a valid program
            if program.auto_add_free_products and program.always_reward_product:
                programs |= program
        return programs
