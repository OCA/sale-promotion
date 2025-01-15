from odoo.tests import common


class TestSaleCouponFreeShippingDefaultProduct(common.TransactionCase):
    @classmethod
    def setUpClass(cls):

        super(TestSaleCouponFreeShippingDefaultProduct, cls).setUpClass()

        cls.coupon_program_model = cls.env["loyalty.program"]
        cls.product_model = cls.env["product.product"]

        # Create a test default product for free shipping
        cls.free_shipping_product_default = cls.product_model.create(
            {
                "name": "Free Shipping Product default",
                "detailed_type": "service",
                "list_price": 0.0,
            }
        )

        # Set the company"s default free shipping product
        cls.env.company.write(
            {"free_shipping_product_default": cls.free_shipping_product_default.id}
        )

    def test_create_coupon_with_free_shipping(self):
        """Test coupon creation with reward_type set to "free_shipping"."""

        vals_list = {
            "name": "Free Shipping Test Program",
            "program_type": "coupons",
            "reward_ids": [(0, 0, {"reward_type": "shipping"})],
        }

        program = self.coupon_program_model.create(vals_list)

        self.assertEqual(program.reward_ids[0].reward_type, "shipping")

        # Check if the default free shipping product is set
        self.assertEqual(
            program.reward_ids[0].discount_line_product_id.id,
            self.free_shipping_product_default.id,
            "no free shipping product set",
        )
