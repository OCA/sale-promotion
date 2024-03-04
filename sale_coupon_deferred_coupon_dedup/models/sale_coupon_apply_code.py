# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleCouponApplyCode(models.TransientModel):
    _inherit = "sale.coupon.apply.code"

    def apply_coupon(self, order, coupon_code):
        # In case of applying a coupon to a draft / sent order
        # Do not add the coupon to the many2one applied_coupon_ids
        # but instead to a many2many unconfirmed_applied_coupon_ids
        # Keep the coupon state at new since it's not considered used yet

        coupon = self.env["coupon.coupon"].search([("code", "=", coupon_code)], limit=1)

        # We still need to prevent multiple coupon add on a single draft
        if coupon and coupon in order.unconfirmed_applied_coupon_ids:
            return {
                "error": _("This coupon has already been used in this order (%s).")
                % (coupon_code)
            }

        error_status = super().apply_coupon(order, coupon_code)

        # Only if it's a coupon and there was no errors
        if not error_status and not self.env["coupon.program"].search(
            [("promo_code", "=", coupon_code)], limit=1
        ):
            # And the order is not yet validated / locked / cancelled
            if order.state in ["draft", "sent"]:
                # Store it in unconfirmed_applied_coupon instead
                order.applied_coupon_ids -= coupon
                order.unconfirmed_applied_coupon_ids += coupon
                # Do not consider it used, set it back to new
                coupon.write({"state": "new"})

        return error_status
