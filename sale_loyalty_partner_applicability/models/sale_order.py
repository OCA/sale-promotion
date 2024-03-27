# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import ast

from odoo import _, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_partner_domain(self, rule, partner_id):
        domain = []
        if rule.rule_partners_domain and rule.rule_partners_domain != "[]":
            allow_sharing = (
                self.env["ir.config_parameter"].sudo().get_param("allow_coupon_sharing")
            )
            if allow_sharing:
                domain = [
                    ("commercial_partner_id", "=", partner_id.commercial_partner_id.id)
                ]
            else:
                domain = [("id", "=", partner_id.id)]
            domain = expression.AND(
                [ast.literal_eval(rule.rule_partners_domain), domain]
            )
        return domain

    def _is_valid_partner(self, program):
        """
        Check if the partner is eligible for a loyalty program based on partner domains.
        This method iterates through the loyalty program's rules and their partner
        domains. It verifies if the partner meets the eligibility criteria specified
        in the partner domain of each rule. When the partner is found eligible for a
        rule, the program is considered valid.
        Args:
            program (recordset): The loyalty program for which partner eligibility is checked.
        Returns:
            bool: True if the partner is eligible for the program, False otherwise.
        """
        for rule in program.rule_ids:
            partner_domain = self._get_partner_domain(rule, self.partner_id)
            if self.env["res.partner"].search_count(partner_domain):
                return True
        return False

    def _program_check_compute_points(self, programs):
        """
        Check and ensure partner eligibility for loyalty programs.
        This method extends the behavior of checking and computing loyalty program
        points. It checks if the customer meets the partner eligibility criteria
        for each program. If a customer does not meet the criteria, an error is
        added to the results for that program.
        """
        res = super()._program_check_compute_points(programs)
        for program, result in res.items():
            if result.get("error", False):
                continue
            if not self._is_valid_partner(program):
                res[program] = {
                    "error": _("The customer doesn't have access to this reward.")
                }
        return res

    def _try_apply_code(self, code):
        res = super()._try_apply_code(code)
        base_domain = self._get_trigger_domain()
        domain = expression.AND(
            [base_domain, [("mode", "=", "with_code"), ("code", "=", code)]]
        )
        program = self.env["loyalty.rule"].search(domain).program_id
        if not program:
            program = self.env["loyalty.card"].search([("code", "=", code)]).program_id
        # Check that the partner is valid when applying the coupon code.
        if not self._is_valid_partner(program):
            return {"error": _("The customer doesn't have access to this reward.")}
        return res
