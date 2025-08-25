# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import _, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    _override_cache = {}

    def _get_applicable_partner_for_loyalty_program(self):
        """Return the partner to use for the loyalty program.

        In some context you could want to use a different partner than the one
        on the order (for example, the commercial entity). This method allows
        to override the partner to use to check the applicability of the loyalty
        program.
        """
        self.ensure_one()
        return self.partner_id

    def _program_check_compute_points(self, programs):
        self.ensure_one()
        # We add the order to the context to be able to filter the rules based on the
        # partner domain.
        # This is needed to check the partner of the order and filter the rules based
        # on the partner domain.
        return super()._program_check_compute_points(programs.with_context(order=self))

    def _try_apply_code(self, code):
        res = super()._try_apply_code(code)
        base_domain = self._get_trigger_domain()
        domain = expression.AND(
            [base_domain, [("mode", "=", "with_code"), ("code", "=", code)]]
        )
        rules = self.env["loyalty.rule"].search(domain)
        applicable_partner = self._get_applicable_partner_for_loyalty_program()
        if not rules:
            program = self.env["loyalty.card"].search([("code", "=", code)]).program_id
            rules = program.rule_ids
        for program in rules.mapped("program_id"):
            if not program._is_partner_valid(applicable_partner):
                return {"error": _("The customer doesn't have access to this reward.")}
        return res
