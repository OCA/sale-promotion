from odoo import models
from odoo.http import Response, request

from .res_partner import REFERRAL_COOKIE, REFERRAL_SESSION_KEY


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _set_referral(cls, response):
        # Capture ?referral=<code> on any request, like utm cookies do. The referrer
        # goes to the session and a long-lived cookie so attribution survives
        # redirects, mid-flow login and browser restarts.
        code = request.httprequest.args.get("referral")
        if not code:
            return
        link = (
            request.env["loyalty.referral"]
            .sudo()
            .search([("code", "=", code.strip().upper())], limit=1)
        )
        if not link:
            return
        partner = link.partner_id
        request.session[REFERRAL_SESSION_KEY] = partner.id
        days = link.program_id.referral_retention_days
        if days is None or days < 0:
            days = 31
        if not days:
            # Session-only attribution: no persistent cookie.
            return
        response = Response.load(response)
        response.set_cookie(
            REFERRAL_COOKIE,
            partner.referral_code,
            max_age=days * 24 * 3600,
            domain=request.httprequest.host,
            cookie_type="optional",
        )

    @classmethod
    def _post_dispatch(cls, response):
        cls._set_referral(response)
        return super()._post_dispatch(response)
