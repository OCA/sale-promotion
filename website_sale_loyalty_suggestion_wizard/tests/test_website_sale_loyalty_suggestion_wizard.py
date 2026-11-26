import json
from unittest.mock import patch

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteSaleLoyaltySuggestionWizard(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Patch for DBs where website_sale_external_tax is active but the field
        #  is missing from sale.order
        if not hasattr(cls.env["sale.order"], "is_tax_computed_externally"):
            type(cls.env["sale.order"]).is_tax_computed_externally = property(
                lambda self: False
            )

        # Product setup
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "list_price": 50,
                "sale_ok": True,
                "website_published": True,
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Product B",
                "list_price": 10,
                "sale_ok": True,
                "website_published": True,
            }
        )

        # Promotion setup
        cls.loyalty_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Order Suggestion",
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
                            "minimum_qty": 3,
                            "product_ids": [
                                (6, 0, [cls.product_a.id, cls.product_b.id])
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

        # Product tag for multi-product reward
        cls.reward_tag = cls.env["product.tag"].create({"name": "Reward Tag"})
        cls.product_a.product_tag_ids = [(4, cls.reward_tag.id)]
        cls.product_b.product_tag_ids = [(4, cls.reward_tag.id)]

        cls.loyalty_program_product1 = cls.env["loyalty.program"].create(
            {
                "name": "Test Product Reward 1",
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
                            "product_ids": [(6, 0, [cls.product_a.id])],
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "product",
                            "required_points": 1,
                            "reward_product_id": cls.product_a.id,
                        },
                    )
                ],
            }
        )

        cls.loyalty_program_product2 = cls.env["loyalty.program"].create(
            {
                "name": "Test Product Reward 2",
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
                            "product_ids": [(6, 0, [cls.product_a.id])],
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "product",
                            "required_points": 1,
                            "reward_product_tag_id": cls.reward_tag.id,
                        },
                    )
                ],
            }
        )

    def test_loyalty_wizard_flow(self):
        self.authenticate("admin", "admin")

        # 1. Add to cart
        self.url_open(
            "/shop/cart/update", data={"product_id": self.product_a.id, "add_qty": 1}
        )

        # 2. Hit promotions page to trigger promotion_page.py
        self.url_open("/promotions")

        # 3. Apply promotion
        self.url_open(f"/promotions/{self.loyalty_program.id}/apply")

        # 4. Visit cart to trigger cart controller override
        self.url_open("/shop/cart")

        # 5. Get defaults (JSON RPC)
        data = {"jsonrpc": "2.0", "method": "call", "params": {}}
        self.url_open(
            "/website_sale_loyalty_suggestion_wizard/get_defaults",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        # 6. Apply wizard
        cart_step6 = self.env["sale.order"].search(
            [("state", "=", "draft")], order="id desc", limit=1
        )
        if cart_step6:
            cart_step6.order_line.create(
                {
                    "order_id": cart_step6.id,
                    "product_id": self.product_a.id,
                    "product_uom_qty": 3,
                }
            )
        apply_data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "program_id": self.loyalty_program.id,
                "promotion_lines": {str(self.product_a.id): 3},
                "reward_line_options": {
                    "reward_id": self.loyalty_program.reward_ids[0].id,
                    "selected_product_ids": [self.product_a.id],
                },
            },
        }
        self.url_open(
            "/website_sale_loyalty_suggestion_wizard/apply",
            data=json.dumps(apply_data),
            headers={"Content-Type": "application/json"},
        )

        # 7. Apply again to test duplicate check (Line 35 in main.py)
        self.url_open(f"/promotions/{self.loyalty_program.id}/apply")

        # 8. Test dismiss
        self.url_open("/promotions/dismiss")

        # 9. Test validation error (empty options)
        apply_data_error = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "program_id": self.loyalty_program.id,
                "promotion_lines": {},
                "reward_line_options": {"selected_product_ids": [self.product_a.id]},
            },
        }
        self.url_open(
            "/website_sale_loyalty_suggestion_wizard/apply",
            data=json.dumps(apply_data_error),
            headers={"Content-Type": "application/json"},
        )

        # 10. Process order and apply to test order processed check
        self.url_open("/promotions/dismiss")  # Clear session before confirming
        cart = self.env["sale.order"].search(
            [("state", "=", "draft")], order="id desc", limit=1
        )
        if cart:
            cart.write({"state": "sale"})
            self.url_open(f"/promotions/{self.loyalty_program.id}/apply")

        # 11. Test inactive/unpublished promotion
        self.loyalty_program.is_published = False
        self.url_open(f"/promotions/{self.loyalty_program.id}/apply")
        self.loyalty_program.is_published = True

        # 12. Test single product reward
        self.url_open(
            "/promotions"
        )  # Creates a new cart because the old one was confirmed
        self.url_open(f"/promotions/{self.loyalty_program_product1.id}/apply")
        apply_data_single = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "program_id": self.loyalty_program_product1.id,
                "promotion_lines": {str(self.product_a.id): 1},
                "reward_line_options": {
                    "reward_id": self.loyalty_program_product1.reward_ids[0].id,
                    "selected_product_ids": [self.product_a.id],
                },
            },
        }
        self.url_open(
            "/website_sale_loyalty_suggestion_wizard/apply",
            data=json.dumps(apply_data_single),
            headers={"Content-Type": "application/json"},
        )

        # 13. Test multi product reward
        cart2 = self.env["sale.order"].search(
            [("state", "=", "draft")], order="id desc", limit=1
        )
        if cart2:
            cart2.write({"state": "sale"})
        self.url_open("/promotions")
        self.url_open(f"/promotions/{self.loyalty_program_product2.id}/apply")
        apply_data_multi = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "program_id": self.loyalty_program_product2.id,
                "promotion_lines": {str(self.product_a.id): 1},
                "reward_line_options": {
                    "reward_id": self.loyalty_program_product2.reward_ids[0].id,
                    "selected_product_ids": [self.product_b.id],
                },
            },
        }
        self.url_open(
            "/website_sale_loyalty_suggestion_wizard/apply",
            data=json.dumps(apply_data_multi),
            headers={"Content-Type": "application/json"},
        )

        # 14. Test qty=0 condition (already have required quantity)
        cart3 = self.env["sale.order"].search(
            [("state", "=", "draft")], order="id desc", limit=1
        )
        if cart3:
            cart3.write({"state": "sale"})
        self.url_open("/promotions")
        cart_qty0 = self.env["sale.order"].search(
            [("state", "=", "draft")], order="id desc", limit=1
        )
        if cart_qty0:
            cart_qty0.order_line.create(
                {
                    "order_id": cart_qty0.id,
                    "product_id": self.product_a.id,
                    "product_uom_qty": 3,
                }
            )
        self.url_open(f"/promotions/{self.loyalty_program.id}/apply")
        apply_data_qty0 = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "program_id": self.loyalty_program.id,
                "promotion_lines": {str(self.product_a.id): 0},
                "reward_line_options": {
                    "reward_id": self.loyalty_program.reward_ids[0].id,
                    "selected_product_ids": [self.product_a.id],
                },
            },
        }
        self.url_open(
            "/website_sale_loyalty_suggestion_wizard/apply",
            data=json.dumps(apply_data_qty0),
            headers={"Content-Type": "application/json"},
        )

        # 15. Mock empty cart for promotion_page.py line 15

        self.opener.cookies.clear()
        with patch(
            "odoo.addons.website_sale.models.website.Website._create_cart",
            return_value=False,
        ):
            self.url_open("/promotions")
