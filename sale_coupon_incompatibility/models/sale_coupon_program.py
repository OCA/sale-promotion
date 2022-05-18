# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class SaleCouponProgram(models.Model):
    _inherit = "sale.coupon.program"

    incompatible_promotion_ids = fields.Many2many(
        comodel_name="sale.coupon.program",
        relation="sale_coupon_program_incompatibility_rel",
        column1="program_id",
        column2="incompatible_program_id",
        inverse="_inverse_incompatible_promotion_ids",
        string="Incompatible Promotions",
    )

    def _inverse_incompatible_promotion_ids(self):
        """We'll be ensuring that any program that could have been removed from the
        field will be compatible again and that any new program in the field will
        be incompatible with this one. So we will ensure that A ⊥ B as B ⊥ A"""
        for program in self:
            incompatible_programs = self.search(
                [
                    ("incompatible_promotion_ids", "in", program.ids),
                    ("id", "!=", program.id),
                ]
            )
            to_remove_programs = (
                incompatible_programs - program.incompatible_promotion_ids
            )
            program.incompatible_promotion_ids.incompatible_promotion_ids |= program
            to_remove_programs.incompatible_promotion_ids -= program

    def _check_promo_code(self, order, coupon_code):
        """Promotion incompatibility rules. Check the error strings for a detailed case
        detail."""
        message = super()._check_promo_code(order, coupon_code)
        # Other errors may precede
        if message:
            return message
        order_programs = order.no_code_promo_program_ids + order.code_promo_program_id
        order_programs |= (
            order.applied_coupon_ids + order.generated_coupon_ids
        ).mapped("program_id")
        if any({x in order_programs for x in self.incompatible_promotion_ids}):
            message = {
                "error": _(
                    "This promotion is incompatible with other set already in the "
                    "order so it can't be applied."
                )
            }
        return message
