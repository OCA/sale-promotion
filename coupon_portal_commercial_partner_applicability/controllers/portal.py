# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.http import request
from odoo.osv import expression

from odoo.addons.sale_coupon_portal.controllers.portal import PortalCoupon


class PortalCouponCommercialPartner(PortalCoupon):
    def _get_coupons_domain(self):
        domain = super()._get_coupons_domain()
        return expression.OR(
            [
                domain,
                [("partner_id", "child_of", request.env.user.commercial_partner_id.id)],
            ]
        )
