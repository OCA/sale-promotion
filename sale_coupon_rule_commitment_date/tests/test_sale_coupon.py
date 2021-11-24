# Copyright 2021 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import SavepointCase


class TestSaleCouponCommitmentDate(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # Archive all existing programs just in case
        cls.env["coupon.program"].search([]).active = False
        # Prepare data
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Mr. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test", "list_price": 100.0}
        )
        cls.program = cls.env["coupon.program"].create(
            {
                "name": "Test Discount Program",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 50.0,
                "discount_apply_on": "on_order",
                "rule_date_from": fields.Datetime.now() + timedelta(days=1),
                "rule_date_to": fields.Datetime.now() + timedelta(days=2),
                "rule_date_field": "commitment_date",
            }
        )
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )

    def _apply_coupon(self, order, coupon_code):
        return self.env["sale.coupon.apply.code"].apply_coupon(order, coupon_code)

    def _generate_coupon(self, program):
        self.env["coupon.generate.wizard"].with_context(active_id=program.id).create(
            {}
        ).generate_coupon()
        return program.coupon_ids[-1]

    def test_promo_commitment_date(self):
        """Promo: Commitment date is in range"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.sale.recompute_coupon_lines()
        self.assertTrue(
            self.sale.order_line.filtered("is_reward_line"),
            "Reward should be here, as commitment_date is well in range",
        )

    def test_promo_commitment_date_not_in_range(self):
        """Promo: Commitment date is not in range"""
        self.sale.commitment_date = fields.Datetime.now()
        self.sale.recompute_coupon_lines()
        self.assertFalse(
            self.sale.order_line.filtered("is_reward_line"),
            "Reward shouldn't be here, as commitment_date is not in range",
        )

    def test_promo_date_order_not_in_range(self):
        """Promo: Commitment date is in range, but rule is based on date_order"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.program.rule_date_field = "date_order"
        self.sale.recompute_coupon_lines()
        self.assertFalse(
            self.sale.order_line.filtered("is_reward_line"),
            "Reward shouldn't be here, as date_order is not in range",
        )

    def test_promo_date_order(self):
        """Promo: Commitment date is not in range, but rule is based on date_order"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=10)
        self.sale.date_order = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.program.rule_date_field = "date_order"
        self.sale.recompute_coupon_lines()
        self.assertTrue(
            self.sale.order_line.filtered("is_reward_line"),
            "Reward should be here, as date_order is well in range",
        )

    def test_promo_code_commitment_date(self):
        """Promo Code: Commitment date is in range"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.program.promo_code_usage = "code_needed"
        self.program.promo_code = "#WhiteJanuary"
        self._apply_coupon(self.sale, self.program.promo_code)
        self.assertTrue(
            self.sale.order_line.filtered("is_reward_line"),
            "Reward should be here, as commitment_date is well in range",
        )

    def test_promo_code_commitment_date_not_in_range(self):
        """Promo Code: Commitment date is not in range"""
        self.sale.commitment_date = fields.Datetime.now()
        self.program.promo_code_usage = "code_needed"
        self.program.promo_code = "#WhiteJanuary"
        self._apply_coupon(self.sale, self.program.promo_code)
        self.assertFalse(
            self.sale.order_line.filtered("is_reward_line"),
            "Reward shouldn't be here, as commitment_date is not in range",
        )

    def test_promo_code_date_order_not_in_range(self):
        """Promo Code: Commitment date is in range, but rule is based on date_order"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.program.rule_date_field = "date_order"
        self.program.promo_code_usage = "code_needed"
        self.program.promo_code = "#WhiteJanuary"
        self._apply_coupon(self.sale, self.program.promo_code)
        self.assertFalse(
            self.sale.order_line.filtered("is_reward_line"),
            "Reward shouldn't be here, as date_order is not in range",
        )

    def test_promo_code_date_order(self):
        """Promo Code: Commitment date is not in range, but rule is based on date_order"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=10)
        self.sale.date_order = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.program.rule_date_field = "date_order"
        self.program.promo_code_usage = "code_needed"
        self.program.promo_code = "#WhiteJanuary"
        self._apply_coupon(self.sale, self.program.promo_code)
        self.assertTrue(
            self.sale.order_line.filtered("is_reward_line"),
            "Reward should be here, as date_order is well in range",
        )

    def test_coupon_commitment_date(self):
        """Coupon: Commitment date is in range"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.program.program_type = "coupon_program"
        self.program.promo_code_usage = "code_needed"
        coupon = self._generate_coupon(self.program)
        self._apply_coupon(self.sale, coupon.code)
        self.assertEqual(self.sale._get_valid_applied_coupon_program(), self.program)

    def test_coupon_commitment_date_not_in_range(self):
        """Coupon: Commitment date is not in range"""
        self.sale.commitment_date = fields.Datetime.now()
        self.program.program_type = "coupon_program"
        self.program.promo_code_usage = "code_needed"
        coupon = self._generate_coupon(self.program)
        self._apply_coupon(self.sale, coupon.code)
        self.assertFalse(self.sale._get_valid_applied_coupon_program())

    def test_coupon_date_order_not_in_range(self):
        """Coupon: Commitment date is in range, but rule is based on date_order"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.program.rule_date_field = "date_order"
        self.program.program_type = "coupon_program"
        self.program.promo_code_usage = "code_needed"
        coupon = self._generate_coupon(self.program)
        self._apply_coupon(self.sale, coupon.code)
        self.assertFalse(self.sale._get_valid_applied_coupon_program())

    def test_coupon_date_order(self):
        """Coupon: Commitment date is not in range, but rule is based on date_order"""
        self.sale.commitment_date = fields.Datetime.now() + timedelta(days=10)
        self.sale.date_order = fields.Datetime.now() + timedelta(days=1, hours=1)
        self.program.rule_date_field = "date_order"
        self.program.program_type = "coupon_program"
        self.program.promo_code_usage = "code_needed"
        coupon = self._generate_coupon(self.program)
        self._apply_coupon(self.sale, coupon.code)
        self.assertEqual(self.sale._get_valid_applied_coupon_program(), self.program)
