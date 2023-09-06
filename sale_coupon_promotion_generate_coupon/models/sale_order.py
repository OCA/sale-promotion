# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_reward_coupon(self, program):
        """Check if the program is set to generate the coupon in other promotion"""
        if program.next_order_program_id:
            program = program.next_order_program_id
        return super()._create_reward_coupon(program)

    def _remove_invalid_reward_lines(self):
        """Ensure that the generated coupons for the next program are expired. The
        original method relies on the original promo discount product ids so we
        have to take an alternative approach expiring those remaining generated
        coupons with no applied promo"""
        res = super()._remove_invalid_reward_lines()
        applied_programs = (
            self.no_code_promo_program_ids
            + self.code_promo_program_id
            + self.applied_coupon_ids.mapped("program_id")
        )
        applied_programs += applied_programs.next_order_program_id
        not_applicable_generated_coupons = self.generated_coupon_ids.filtered(
            lambda x: x.program_id not in applied_programs
        )
        not_applicable_generated_coupons.write({"state": "expired"})
        self.generated_coupon_ids -= not_applicable_generated_coupons
        return res
