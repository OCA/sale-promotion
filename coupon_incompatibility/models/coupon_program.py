# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    incompatible_promotion_ids = fields.Many2many(
        comodel_name="coupon.program",
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
