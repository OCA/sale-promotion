from unittest.mock import MagicMock, patch

from odoo.tests import common, tagged

from ..controllers.promotion_wizard import WebsiteSaleLoyaltySuggestionWizardController


@tagged("post_install", "-at_install")
class TestWebsiteSaleLoyaltySuggestionWizardMultiGift(common.TransactionCase):
    def test_process_reward_line_options_multi_gift(self):
        controller = WebsiteSaleLoyaltySuggestionWizardController()
        cls = WebsiteSaleLoyaltySuggestionWizardController
        method = cls._process_reward_line_options
        controller._process_reward_line_options = method.__get__(controller)

        with patch(
            "odoo.addons.website_sale_loyalty.controllers.main.WebsiteSale._process_reward_line_options",
            create=True,
            return_value={"status": "ok"},
        ):
            with patch(
                "odoo.addons.website_sale_loyalty_suggestion_wizard.controllers.promotion_wizard.WebsiteSale._process_reward_line_options",
                create=True,
                return_value={"status": "ok"},
            ):
                wizard_id = MagicMock()
                wizard_id.multi_gift_reward = True

                gift_line_1 = MagicMock()
                gift_line_2 = MagicMock()
                wizard_id.loyalty_gift_line_ids = [gift_line_1, gift_line_2]

                reward_line_options = {"selected_product_ids": [10, 20]}

                res = controller._process_reward_line_options(
                    wizard_id, reward_line_options
                )

                self.assertEqual(res, {"status": "ok"})
                self.assertEqual(gift_line_1.selected_gift_id, 10)
                self.assertEqual(gift_line_2.selected_gift_id, 20)

    def test_process_reward_line_options_not_multi_gift(self):
        controller = WebsiteSaleLoyaltySuggestionWizardController()

        with patch(
            "odoo.addons.website_sale_loyalty.controllers.main.WebsiteSale._process_reward_line_options",
            create=True,
            return_value={"status": "ok"},
        ):
            with patch(
                "odoo.addons.website_sale_loyalty_suggestion_wizard.controllers.promotion_wizard.WebsiteSale._process_reward_line_options",
                create=True,
                return_value={"status": "ok"},
            ):
                wizard_id = MagicMock()
                wizard_id.multi_gift_reward = False

                reward_line_options = {"selected_product_ids": [10, 20]}

                res = controller._process_reward_line_options(
                    wizard_id, reward_line_options
                )

                self.assertEqual(res, {"status": "ok"})
