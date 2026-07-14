from unittest.mock import MagicMock, patch

import odoo.http
from odoo.tests import common, tagged

from ..controllers import main as m
from ..controllers import promotion_wizard as w
from ..controllers.main import (
    WebsiteSaleLoyaltySuggestionWizardMultiProductController,
)
from ..controllers.promotion_wizard import (
    WebsiteSaleLoyaltySuggestionWizardController,
)


@tagged("post_install", "-at_install")
class TestWebsiteSaleLoyaltySuggestionWizardMultiProduct(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "list_price": 50,
                "sale_ok": True,
                "website_published": True,
            }
        )

        cls.multi_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Multi Product Promo",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "is_published": True,
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "loyalty_criteria": "multi_product",
                            "loyalty_criteria_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_ids": [(6, 0, [cls.product_a.id])],
                                    },
                                )
                            ],
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )

    def _get_ctrl_main(self, mock_req):
        m.request = mock_req
        return WebsiteSaleLoyaltySuggestionWizardMultiProductController.__new__(
            WebsiteSaleLoyaltySuggestionWizardMultiProductController
        ), m

    def _get_ctrl_wizard(self, mock_req):
        w.request = mock_req
        return WebsiteSaleLoyaltySuggestionWizardController.__new__(
            WebsiteSaleLoyaltySuggestionWizardController
        ), w

    def _restore_request(self):
        m.request = odoo.http.request
        w.request = odoo.http.request

    def test_main_cart(self):
        order = self.env["sale.order"].create(
            {"partner_id": self.env.user.partner_id.id}
        )
        order.order_line.create(
            {
                "order_id": order.id,
                "product_id": self.product_a.id,
                "product_uom_qty": 1,
            }
        )

        mock_req = MagicMock()
        mock_req.session = {
            "promotion_id": self.multi_program.id,
            "sale_order_id": order.id,
        }
        mock_req.env = self.env

        ctrl, _ = self._get_ctrl_main(mock_req)

        response_mock = MagicMock()
        response_mock.qcontext = {}

        with patch(
            "odoo.addons.website_sale_loyalty_suggestion_wizard_multi_product.controllers.main.WebsiteSale.cart",
            return_value=response_mock,
            create=True,
        ):
            wizard_mock = MagicMock()
            wizard_mock.loyalty_rule_line_ids = [MagicMock()]
            wizard_mock.selected_reward_id.program_id = self.multi_program

            with patch.object(
                ctrl,
                "_get_sale_loyalty_reward_wizard",
                return_value=wizard_mock,
                create=True,
            ):
                res = ctrl.cart.original_endpoint(ctrl)

                self.assertIn("mandatory_program_options", res.qcontext)
                self.assertEqual(
                    res.qcontext["mandatory_program_options"],
                    wizard_mock.loyalty_rule_line_ids,
                )
                self.assertEqual(
                    mock_req.session["multi_product_id"], wizard_mock.product_id
                )
                wizard_mock._compute_loyalty_rule_line_ids.assert_called_once()

        self._restore_request()

    def test_main_cart_with_product_in_cart(self):
        order = self.env["sale.order"].create(
            {"partner_id": self.env.user.partner_id.id}
        )
        line = order.order_line.create(
            {
                "order_id": order.id,
                "product_id": self.product_a.id,
                "product_uom_qty": 1,
            }
        )
        # Mock the suggested_promotion_ids logic
        mock_program = MagicMock()
        mock_program.is_published = True
        mock_program.id = 5  # The hardcoded 5 in main.py
        mock_filtered = MagicMock()
        mock_filtered.__getitem__.return_value = mock_program
        type(line).suggested_promotion_ids = property(
            lambda self: MagicMock(filtered=lambda x: mock_filtered)
        )

        mock_req = MagicMock()
        mock_req.session = {
            "promotion_id": self.multi_program.id,
            "sale_order_id": order.id,
        }
        mock_req.env = self.env

        ctrl, _ = self._get_ctrl_main(mock_req)
        response_mock = MagicMock()
        response_mock.qcontext = {}

        with patch(
            "odoo.addons.website_sale_loyalty_suggestion_wizard_multi_product.controllers.main.WebsiteSale.cart",
            return_value=response_mock,
            create=True,
        ):
            wizard_mock = MagicMock()
            wizard_mock.loyalty_rule_line_ids = [MagicMock()]
            wizard_mock.selected_reward_id.program_id = self.multi_program

            with patch.object(
                ctrl,
                "_get_sale_loyalty_reward_wizard",
                return_value=wizard_mock,
                create=True,
            ):
                ctrl.cart.original_endpoint(ctrl)
                self.assertEqual(wizard_mock.product_id, self.product_a.id)

        self._restore_request()

    def test_promotion_wizard_process(self):
        mock_req = MagicMock()
        mock_req.session = {
            "multi_product_id": self.product_a.id,
        }

        ctrl, _ = self._get_ctrl_wizard(mock_req)

        wizard_mock = MagicMock()
        wizard_mock.multi_criteria = True
        line_mock1 = MagicMock()
        line_mock1.units_included = 0
        line_mock1.units_required = 1
        line_mock2 = MagicMock()
        line_mock2.units_included = 2
        line_mock2.units_required = 1

        wizard_mock.loyalty_rule_line_ids = [line_mock1, line_mock2]

        with patch(
            "odoo.addons.website_sale_loyalty_suggestion_wizard_multi_product.controllers.promotion_wizard.WebsiteSale._process_promotion_lines",
            return_value={},
            create=True,
        ):
            ctrl._process_promotion_lines(wizard_mock, {})

            self.assertEqual(wizard_mock.product_id, self.product_a.id)
            wizard_mock._compute_loyalty_rule_line_ids.assert_called_once()
            self.assertEqual(line_mock1.units_to_include, 1)

        self._restore_request()
