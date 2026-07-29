import contextlib

from odoo.tests import tagged

from odoo.addons.loyalty.tests.test_loyalty import TestLoyalty


@tagged("-at_install", "post_install")
class TestLoyaltyMail(TestLoyalty):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.LoyaltyMail = cls.env["loyalty.mail"]
        cls.LoyaltyProgram = cls.env["loyalty.program"]
        cls.Mail = cls.env["mail.mail"]
        cls.default_mail_template = cls.env.ref(
            "loyalty.mail_template_loyalty_card", raise_if_not_found=False
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    @contextlib.contextmanager
    def _assert_mail_count_change(self, expected_delta, msg=""):
        """Helper to assert mail count change"""
        before = self.Mail.search_count([])
        yield
        after = self.Mail.search_count([])
        self.assertEqual(after - before, expected_delta, msg)

    def _generate_coupons(self, **wizard_vals):
        """Generate coupons with wizard for self.program"""
        return (
            self.env["loyalty.generate.wizard"]
            .with_context(active_id=self.program.id)
            .create(wizard_vals)
            .generate_coupons()
        )

    def test_trigger_field_has_never(self):
        """Test that the trigger field includes 'never' and defaults to it"""
        field = self.LoyaltyMail._fields["trigger"]
        selection_keys = [key for key, _ in field.selection]
        self.assertIn("never", selection_keys)
        record = self.LoyaltyMail.create({"program_id": self.program.id})
        self.assertEqual(record.trigger, "never")

    def test_mail_template_default(self):
        """Test default mail_template_id points to loyalty.mail_template_loyalty_card if available"""  # noqa: E501
        record = self.LoyaltyMail.create({"program_id": self.program.id})
        self.assertEqual(record.mail_template_id, self.default_mail_template)

    def test_program_type_default_values_sets_trigger_never(self):
        """Test that communication plan trigger is set to 'never' for coupons"""
        result = self.LoyaltyProgram._program_type_default_values()
        comm_plans = result["coupons"]["communication_plan_ids"]
        self.assertTrue(
            comm_plans, "Coupon program should have communication plan defaults"
        )
        for plan in comm_plans:
            if plan[0] == 0:
                self.assertEqual(plan[2].get("trigger"), "never")

    def test_generate_coupon_with_mail(self):
        """Test that mail is created when trigger is create (not 'never')."""
        self.program.write(
            {
                "program_type": "coupons",
                "communication_plan_ids": [(0, 0, {"trigger": "create"})],
            }
        )
        with self._assert_mail_count_change(
            1, "Should create 1 mail when trigger=create"
        ):
            self._generate_coupons(mode="selected", customer_ids=self.partner)

    def test_generate_coupon_no_mail(self):
        """Generating coupons must not send any mail"""
        self.program.write(
            {
                "program_type": "coupons",
                "communication_plan_ids": [(0, 0, {"trigger": "never"})],
            }
        )
        with self._assert_mail_count_change(
            0, "No mail should be created when trigger=never"
        ):
            self._generate_coupons(mode="selected", customer_ids=self.partner)
