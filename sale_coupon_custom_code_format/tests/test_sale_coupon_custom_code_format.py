# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError

from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


class TestSaleCouponCustomCodeFormat(TestSaleCouponCommon):
    def test_sale_coupon_custom_code_format_disabled(self):
        self.code_promotion_program.reward_type = "discount"
        self.code_promotion_program.custom_code = False

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.code_promotion_program.id
        ).create(
            {
                "generation_type": "nbr_customer",
                "partners_domain": "[('id', 'in', [%s])]" % (self.steve.id),
            }
        ).generate_coupon()
        coupon = self.code_promotion_program.coupon_ids
        self.assertRegex(
            coupon.code, r"[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{3}"
        )

    def test_sale_coupon_custom_code_format_normal(self):
        self.code_promotion_program.reward_type = "discount"

        for _ in range(5):  # Check 5 times to be sure since it's random
            self.env["coupon.generate.wizard"].with_context(
                active_id=self.code_promotion_program.id
            ).create(
                {
                    "generation_type": "nbr_customer",
                    "partners_domain": "[('id', 'in', [%s])]" % (self.steve.id),
                }
            ).generate_coupon()
            coupon = self.code_promotion_program.coupon_ids
            self.assertRegex(coupon.code, r"[A-Z]{6}-\d{2}")
            coupon.unlink()

    def test_sale_coupon_custom_code_other_format(self):
        self.code_promotion_program.reward_type = "discount"
        self.code_promotion_program.custom_code_mask = "000000/xX"

        for _ in range(5):  # Check 5 times to be sure since it's random
            self.env["coupon.generate.wizard"].with_context(
                active_id=self.code_promotion_program.id
            ).create(
                {
                    "generation_type": "nbr_customer",
                    "partners_domain": "[('id', 'in', [%s])]" % (self.steve.id),
                }
            ).generate_coupon()
            coupon = self.code_promotion_program.coupon_ids
            self.assertRegex(coupon.code, r"\d{2}/[a-z][A-Z]")
            coupon.unlink()

    def test_sale_coupon_custom_code_forbidden_characters(self):
        self.code_promotion_program.reward_type = "discount"
        self.code_promotion_program.custom_code_mask = "XXXXXXXXXXXX"
        self.code_promotion_program.custom_code_forbidden_characters = (
            "BCDFGHJKLMNPQRSTVWXZ"
        )

        for _ in range(5):  # Check 5 times to be sure since it's random
            self.env["coupon.generate.wizard"].with_context(
                active_id=self.code_promotion_program.id
            ).create(
                {
                    "generation_type": "nbr_customer",
                    "partners_domain": "[('id', 'in', [%s])]" % (self.steve.id),
                }
            ).generate_coupon()
            coupon = self.code_promotion_program.coupon_ids
            self.assertRegex(coupon.code, r"[AEIOUY]{12}")
            coupon.unlink()

    def test_sale_coupon_custom_code_retries(self):
        self.code_promotion_program.reward_type = "discount"
        self.code_promotion_program.custom_code_mask = "0"
        self.code_promotion_program.custom_code_forbidden_characters = "39"

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.code_promotion_program.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 8,
            }
        ).generate_coupon()
        coupons = self.code_promotion_program.coupon_ids
        self.assertEqual(len(coupons), 8)
        self.assertEqual(set(coupons.mapped("code")), set("01245678"))

    def test_sale_coupon_custom_code_too_much_retries(self):
        self.code_promotion_program.reward_type = "discount"
        self.code_promotion_program.custom_code_mask = "0"
        self.code_promotion_program.custom_code_forbidden_characters = "39"

        with self.assertRaises(ValidationError):
            self.env["coupon.generate.wizard"].with_context(
                active_id=self.code_promotion_program.id
            ).create(
                {
                    "generation_type": "nbr_coupon",
                    "nbr_coupons": 9,
                }
            ).generate_coupon()
