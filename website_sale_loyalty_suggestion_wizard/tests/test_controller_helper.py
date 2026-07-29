from unittest.mock import MagicMock, patch

import odoo.http
from odoo.tests import common, tagged

from ..controllers import main as m
from ..controllers.main import (  # noqa: E501
    WebsiteSaleLoyaltySuggestionWizard,
)


@tagged("post_install", "-at_install")
class TestControllerHelper(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env["res.partner"].create({"name": "Helper Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Helper Product", "list_price": 10}
        )
        cls.program = cls.env["loyalty.program"].create(
            {
                "name": "Helper Promo",
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
                            "minimum_qty": 1,
                            "product_ids": [(6, 0, [cls.product.id])],
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

    def _get_ctrl(self, mock_req):
        m.request = mock_req
        return (
            WebsiteSaleLoyaltySuggestionWizard.__new__(
                WebsiteSaleLoyaltySuggestionWizard
            ),
            m,
        )

    def _restore_request(self):
        m.request = odoo.http.request

    def test_confirmed_order_resets_cart(self):
        confirmed = self.env["sale.order"].create(
            {"partner_id": self.partner.id, "state": "sale"}
        )
        fresh = self.env["sale.order"].create({"partner_id": self.partner.id})
        mock_site = MagicMock()
        mock_site._get_and_cache_current_cart.return_value = fresh
        mock_req = MagicMock()
        mock_req.cart = confirmed
        mock_req.website = mock_site
        ctrl, _ = self._get_ctrl(mock_req)
        try:
            order, redirect = ctrl._get_order_for_promotion(self.program)
            mock_site.sale_reset.assert_called_once()
            mock_site._get_and_cache_current_cart.assert_called_once()
            self.assertEqual(order, fresh)
            self.assertFalse(redirect)
        finally:
            self._restore_request()

    def test_duplicate_program_redirects(self):
        draft = self.env["sale.order"].create({"partner_id": self.partner.id})
        mock_req = MagicMock()
        mock_req.cart = draft
        ctrl, _ = self._get_ctrl(mock_req)
        try:
            with patch.object(
                type(draft),
                "_get_reward_programs",
                return_value=self.program,
            ):
                _, redirect = ctrl._get_order_for_promotion(self.program)
            self.assertTrue(redirect)
        finally:
            self._restore_request()
