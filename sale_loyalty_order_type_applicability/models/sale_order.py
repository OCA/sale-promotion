# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _filter_programs(self, programs):
        self.ensure_one()
        return programs.filtered(
            lambda p, self=self: (
                not p.sale_order_type_ids or self.type_id in p.sale_order_type_ids
            )
        )

    def _program_check_compute_points(self, programs):
        valid_programs = self._filter_programs(programs)
        not_valid_programs = programs - valid_programs
        res = super()._program_check_compute_points(
            self._filter_programs(valid_programs)
        )
        for program in not_valid_programs:
            res.setdefault(program, {"points": [0]})
        return res

    def _try_apply_code(self, code):
        base_domain = self._get_trigger_domain()
        domain = expression.AND(
            [base_domain, [("mode", "=", "with_code"), ("code", "=", code)]]
        )
        rules = self.env["loyalty.rule"].search(domain)
        if not rules:
            program = self.env["loyalty.card"].search([("code", "=", code)]).program_id
            rules = program.rule_ids
        for program in rules.mapped("program_id"):
            if not self._filter_programs(program):
                return {
                    "error": _("This reward can not be accesed with this order type.")
                }
        return super()._try_apply_code(code)
