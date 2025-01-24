# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import _, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    _override_cache = {}

    def _get_partner_domain(self, rule, partner_id):
        # This method is no longer used and should be removed. It has been
        # moved to the loyalty program model.
        pass

    def _is_valid_partner(self, program):
        # This method is no longer used and should be removed. It has been
        # moved to the loyalty program model.
        self._get_partner_domain(self.env["loyalty.rule"].browse(), self.partner_id)

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
        if not rules:
            program = self.env["loyalty.card"].search([("code", "=", code)]).program_id
            rules = program.rule_ids
        for rule in rules:
            if not rule._is_partner_valid(self.partner_id):
                return {"error": _("The customer doesn't have access to this reward.")}
        return res
