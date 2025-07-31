# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    incompatible_promotion_ids = fields.Many2many(
        comodel_name="loyalty.program",
        relation="sale_loyalty_program_incompatibility_rel",
        column1="program_id",
        column2="incompatible_program_id",
        inverse="_inverse_incompatible_promotion_ids",
        string="Incompatible Promotions",
        domain="[('id', '!=', id)]",
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
            if not self.env.context.get("avoid_incompatibility_loop", False):
                for other in incompatible_programs:
                    if other not in program.incompatible_promotion_ids:
                        other.incompatible_promotion_ids -= program
            for incompatible in program.incompatible_promotion_ids:
                incompatible.with_context(
                    avoid_incompatibility_loop=True
                ).incompatible_promotion_ids |= program
