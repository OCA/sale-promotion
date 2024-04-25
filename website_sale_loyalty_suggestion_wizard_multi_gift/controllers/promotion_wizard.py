# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale


class WebsiteSaleLoyaltySuggestionWizardController(WebsiteSale):
    def _process_reward_line_options(self, wizard_id, reward_line_options):
        response = super()._process_reward_line_options(wizard_id, reward_line_options)
        if wizard_id.multi_gift_reward:
            selected_product_ids = reward_line_options.get("selected_product_ids")
            for gift_line, selected_product_id in zip(
                wizard_id.loyalty_gift_line_ids, selected_product_ids
            ):
                gift_line.selected_gift_id = int(selected_product_id)
        return response
