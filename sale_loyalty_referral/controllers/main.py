from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class ReferralCustomerPortal(CustomerPortal):
    @route(
        "/my/referral/generate",
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
    )
    def portal_referral_generate(self, **_kw):
        request.env.user.partner_id.ensure_referral_code()
        return request.redirect(request.httprequest.referrer or "/my")
