from odoo.tests import TransactionCase, tagged


@tagged("sale_loyalty_referral", "post_install", "-at_install")
class TestPartnerReferral(TransactionCase):
    """Referral codes: a customer shares a link, a friend buys through it, and
    the friend's order gets the configured discount."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.program = cls.env["loyalty.program"].create(
            {
                "name": "Referral Program",
                "program_type": "promo_code",
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 10,
                            "discount_mode": "per_order",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        cls.referrer = cls.env["res.partner"].create({"name": "Referrer"})
        cls.friend = cls.env["res.partner"].create({"name": "Friend"})
        cls.env["ir.config_parameter"].set_param(
            "sale_loyalty_referral.referral_program_id", cls.program.id
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Haircut", "lst_price": 50.0}
        )

    def _create_order(self, partner):
        return self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "price_unit": 50.0})
                ],
            }
        )

    def test_referral_code_is_opt_in(self):
        """Codes are only minted on demand — the partner's portal button or the
        partners list action — never by reading the partner."""
        self.assertFalse(self.referrer.referral_code)
        self.assertFalse(self.referrer.referral_url)
        self.referrer.ensure_referral_code()
        code = self.referrer.referral_code
        url = self.referrer.referral_url
        self.assertTrue(code)
        self.assertTrue(url.endswith(f"?referral={code}"))
        link = self.env["loyalty.referral"].search([("code", "=", code)])
        self.assertEqual(len(link), 1)
        self.assertEqual(link.partner_id, self.referrer)
        self.assertTrue(link.rule_id.is_referral_rule)
        # Generating again reuses the same code instead of minting a new one.
        self.referrer.ensure_referral_code()
        self.assertEqual(self.referrer.referral_code, code)

    def test_code_resolves_back_to_partner(self):
        """Typing a shared code anywhere resolves to the customer who owns it."""
        self.referrer.ensure_referral_code()
        found = self.env["res.partner"]._get_partner_by_referral_code(
            self.referrer.referral_code
        )
        self.assertEqual(found, self.referrer)

    def test_referred_order_gets_reward_line(self):
        """A friend ordering through the link sees the discount on their
        order."""
        self.referrer.ensure_referral_code()
        order = self._create_order(self.friend)
        order.referred_by_id = self.referrer
        order._apply_referral_code()
        reward_lines = order.order_line.filtered("is_reward_line")
        self.assertEqual(len(reward_lines), 1)
        self.assertAlmostEqual(reward_lines.price_total, -10.0)

    def test_self_referral_is_dropped(self):
        """A customer cannot claim their own referral discount."""
        self.referrer.ensure_referral_code()
        order = self._create_order(self.referrer)
        order.referred_by_id = self.referrer
        order._apply_referral_code()
        self.assertFalse(order.order_line.filtered("is_reward_line"))

    def test_apply_failure_is_not_blocking(self):
        """An unresolvable code leaves the order untouched instead of breaking
        checkout."""
        order = self._create_order(self.friend)
        order.referred_by_id = self.referrer
        self.env["ir.config_parameter"].search(
            [("key", "=", "sale_loyalty_referral.referral_program_id")]
        ).unlink()
        self.assertTrue(order._apply_referral_code())
        self.assertFalse(order.order_line.filtered("is_reward_line"))

    def test_no_program_means_no_code(self):
        """Without a flagged program, opting in generates nothing."""
        self.env["ir.config_parameter"].search(
            [("key", "=", "sale_loyalty_referral.referral_program_id")]
        ).unlink()
        self.assertFalse(self.referrer.ensure_referral_code())
        self.assertFalse(self.referrer.referral_url)
        self.assertFalse(self.referrer.referral_code)
