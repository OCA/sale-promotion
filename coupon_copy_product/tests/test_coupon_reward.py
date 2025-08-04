# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestCouponReward(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.coupon_program_obj = cls.env["coupon.program"]
        cls.product_obj = cls.env["product.product"]
        cls.discount_product = cls.product_obj.create(
            {
                "name": "Discount Product for Test Coupon Program",
                "type": "service",
            }
        )
        cls.coupon_program = cls.coupon_program_obj.create(
            {
                "name": "Test Coupon Program",
                "discount_line_product_id": cls.discount_product.id,
            }
        )

    def test_duplicate_coupon_program(self):
        """
        Check that when the promotional program is duplicated, the product set in the
        discount_line_product_id field is not duplicated (the discount_line_product_id
        field of the two promotional programs refer to the same record).
        """

        self.coupon_program_copy = self.coupon_program.copy(
            default={
                "name": "Test Coupon Program (copy)",
            }
        )

        # check if both coupon programs have the same discount product
        self.assertEqual(
            self.coupon_program.discount_line_product_id.id,
            self.coupon_program_copy.discount_line_product_id.id,
            """When duplicating a coupon program, the discount
            product should not be duplicated.""",
        )
