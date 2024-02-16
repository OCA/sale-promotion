# Copyright 2021-2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Store current program in memory for use in get_paid_order_lines
    current_program_id = fields.Many2one("coupon.program", store=False, copy=False)

    def _get_reward_values_discount(self, program):
        self.current_program_id = program
        rv = super()._get_reward_values_discount(program)
        self.current_program_id = None
        return rv

    def _get_skipped_paid_order_lines(self, paid_order_lines):
        if self.current_program_id.skip_discounted_products:
            return paid_order_lines.filtered(lambda line: line.discount == 0)
        return paid_order_lines

    def _get_paid_order_lines(self):
        paid_order_lines = super()._get_paid_order_lines()
        return self._get_skipped_paid_order_lines(paid_order_lines)
