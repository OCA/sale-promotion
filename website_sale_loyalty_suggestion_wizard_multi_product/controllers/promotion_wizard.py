# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request

from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale


class WebsiteSaleLoyaltySuggestionWizardController(WebsiteSale):
    def _process_promotion_lines(self, wizard_id, promotion_lines):
        response = super()._process_promotion_lines(wizard_id, promotion_lines)
        if wizard_id.multi_criteria:
            wizard_id.product_id = request.session.get("multi_product_id")
            wizard_id._compute_loyalty_rule_line_ids()
            for line in wizard_id.loyalty_rule_line_ids:
                if line.units_included >= line.units_required:
                    continue
                line.units_to_include = line.units_required
        return response
