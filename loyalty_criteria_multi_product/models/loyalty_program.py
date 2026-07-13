# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    @api.model
    def _program_type_default_values(self):
        res = super()._program_type_default_values()
        program_types_to_update = [
            "promotion",
            "loyalty",
            "promo_code",
            "buy_x_get_y",
            "next_order_coupons",
        ]
        for program_type in program_types_to_update:
            res[program_type]["rule_ids"][1][2].update({"loyalty_criteria": "domain"})
        return res
