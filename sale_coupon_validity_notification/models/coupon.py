# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class CouponCoupon(models.Model):
    _inherit = "coupon.coupon"

    def write(self, vals):
        if vals.get("state", "") == "expired":
            for coupon in self.filtered(lambda r: r.order_id and r.sales_order_id):
                order = coupon.sales_order_id
                # Post a note on the chatter and create an activity.
                order.message_post(
                    body=_(
                        "Coupon <a href=# data-oe-model=coupon.coupon data-oe-id=%(id)s>"
                        "%(coupon)s</a> has expired.",
                        id=coupon.program_id,
                        coupon=coupon.program_id.name,
                    )
                )
                order.activity_schedule(
                    "mail.mail_activity_data_warning",
                    summary=_("Coupon expired"),
                    user_id=order.user_id.id,
                    note=_(
                        "Coupon %(coupon)s has expired. You should remove the coupon "
                        "from the order %(order)s.",
                        coupon=coupon.program_id.name,
                        order=order.name,
                    ),
                )
        return super().write(vals)
