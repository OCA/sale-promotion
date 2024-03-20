# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.http import request, route

from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale


class WebsiteSaleLoyaltySuggestionWizardController(WebsiteSale):
    @route()
    def apply_promotion_public(
        self, program_id, promotion_lines, reward_line_options, **kw
    ):
        wizard_id = request.session.get("wizard_id")
        wiz = request.env["sale.loyalty.reward.wizard"].sudo().browse(wizard_id)
        if wiz.multi_criteria:
            for line in wiz.loyalty_rule_line_ids:
                if line.units_included >= line.units_required:
                    continue
                line.units_to_include = line.units_required
            try:
                wiz.action_apply()
            except ValidationError as e:
                request.session["error_promo_code"] = str(e)
                return
            request.session.pop("promotion_id", None)
            request.session.pop("error_promo_code", None)
            request.session.pop("wizard_id", None)
        else:
            return super().apply_promotion_public(
                program_id, promotion_lines, reward_line_options, **kw
            )
