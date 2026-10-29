import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    referred_by_id = fields.Many2one(
        "res.partner",
        string="Referred By",
        copy=False,
        index=True,
        help="Customer whose referral code brought this order.",
    )

    def _try_apply_code(self, code):
        # Referral codes alias the program's shared referral rule: resolve the
        # code to its link, then run the standard apply path with the rule's
        # code so all promotion semantics stay intact.
        Referral = self.env["loyalty.referral"].sudo()
        link = Referral.search([("code", "=", (code or "").strip().upper())], limit=1)
        if not link:
            # A shared referral rule's own code only applies to orders that
            # already carry a referrer; otherwise it is not a valid code.
            Rule = self.env["loyalty.rule"].sudo()
            rule = Rule.search([("code", "=", code)], limit=1)
            if rule.is_referral_rule and not self.referred_by_id:
                return {
                    "error": self.env._("This code is invalid (%s).", code),
                    "not_found": True,
                }
            return super()._try_apply_code(code)
        res = super()._try_apply_code(link.rule_id.code)
        for order in self:
            if not order.referred_by_id and link.partner_id != order.partner_id:
                order.referred_by_id = link.partner_id
            cp = order.coupon_point_ids.filtered(
                lambda c: c.coupon_id.program_id == link.program_id
                and not c.coupon_id.partner_id
            )
            if cp:
                # core creates promo-code cards anonymously; tag the
                # referred customer so claims can be reported per partner.
                cp.coupon_id.partner_id = order.partner_id
        return res

    def _apply_referral_code(self):
        """Apply the referrer's promotion code to this order. Failures are
        logged, never blocking: an expired or invalid code must not break a
        checkout."""
        for order in self:
            referrer = order.referred_by_id
            if (
                not referrer
                or referrer == order.partner_id
                or not order._referral_is_eligible()
            ):
                continue
            referrer.ensure_referral_code()
            link = referrer.referral_code_ids[:1]
            if not link or not link.program_id.reward_ids:
                # Tracking-only referral: attribution is recorded, nothing
                # to apply.
                continue
            try:
                status = order._try_apply_code(referrer.referral_code)
            except Exception:
                _logger.exception(
                    "Referral code application raised on order %s.", order.id
                )
                order.message_post(
                    body=self.env._(
                        "Referral code %(code)s could not be applied "
                        "(unexpected error — see logs).",
                        code=referrer.referral_code,
                    )
                )
                continue
            if "error" in status or status.get("not_found"):
                order.message_post(
                    body=self.env._(
                        "Referral code %(code)s was not applied: %(reason)s",
                        code=referrer.referral_code,
                        reason=status.get("error") or "not found",
                    )
                )
                continue
            # Auto-claim the reward when there is exactly one claimable reward,
            # like the eCommerce pending-coupon flow does. Ambiguous programs
            # stay unclaimed for a human to choose via the reward wizard.
            if len(status) == 1:
                coupon, rewards = next(iter(status.items()))
                if len(rewards) == 1 and not rewards.multi_product:
                    try:
                        order._apply_program_reward(rewards, coupon)
                    except Exception:
                        _logger.exception(
                            "Referral reward claim raised on order %s.", order.id
                        )
                        order.message_post(
                            body=self.env._(
                                "The referral reward could not be claimed "
                                "(unexpected error — see logs)."
                            )
                        )
        return True

    def _referral_is_eligible(self):
        """Whether the referral reward may be applied on this order.
        Integrations override this to add per-surface rules."""
        self.ensure_one()
        return True
