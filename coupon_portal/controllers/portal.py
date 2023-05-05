# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class PortalCoupon(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "coupon_count" in counters:
            coupon_count = (
                request.env["coupon.coupon"]
                .sudo()
                .search_count(self._get_coupons_domain())
            )
            values["coupon_count"] = coupon_count
        return values

    def _get_coupons_domain(self):
        return [("partner_id", "=", request.env.user.partner_id.id)]

    @http.route(
        ["/my/coupons", "/my/coupons/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_coupons(
        self, page=1, sortby=None, filterby=None, search=None, search_in="code", **kw
    ):
        values = self._prepare_portal_layout_values()
        Coupon = request.env["coupon.coupon"].sudo()
        domain = self._get_coupons_domain()
        searchbar_sortings = {
            "date_recived": {"label": _("Recived on"), "order": "create_date desc"},
            "date_expires": {"label": _("Expires on"), "order": "create_date asc"},
            "state": {"label": _("Status"), "order": "state"},
        }
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
            "reserved": {
                "label": _("Pending"),
                "domain": [("state", "=", "reserved")],
            },
            "valid": {"label": _("Valid"), "domain": [("state", "=", "new")]},
            "use": {"label": _("Used"), "domain": [("state", "=", "used")]},
            "expire": {"label": _("Expired"), "domain": [("state", "=", "expired")]},
            "cancel": {"label": _("Cancelled"), "domain": [("state", "=", "cancel")]},
            "sent": {"label": _("Sent"), "domain": [("state", "=", "sent")]},
        }
        searchbar_inputs = {
            "code": {"input": "code", "label": _("Search by Coupon Code")},
            "program": {"input": "program", "label": _("Search by Program")},
        }
        # default sort
        if not sortby:
            sortby = "date_recived"
        order = searchbar_sortings.get(sortby, searchbar_filters.get("date_recived"))[
            "order"
        ]
        # default filter
        if not filterby:
            filterby = "all"
        domain = expression.AND(
            [
                domain,
                searchbar_filters.get(filterby, searchbar_filters.get("all"))["domain"],
            ]
        )
        # search options
        if search and search_in:
            search_domain = []
            if search_in == "code":
                search_domain = [("code", "ilike", search)]
            if search_in == "program":
                search_domain = [("program_id", "ilike", search)]
            domain = expression.AND([domain, search_domain])
        # count for pager
        coupon_count = Coupon.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/coupons",
            url_args={
                "sortby": sortby,
                "filterby": filterby,
                "search": search,
                "search_in": search_in,
            },
            total=coupon_count,
            page=page,
            step=self._items_per_page,
        )
        # content according to pager and archive selected
        coupons = Coupon.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_coupon_history"] = coupons.ids[:100]
        values.update(
            {
                "coupons": coupons,
                "page_name": "coupon",
                "pager": pager,
                "default_url": "/my/coupons",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                "searchbar_filters": searchbar_filters,
                "filterby": filterby,
                "searchbar_inputs": searchbar_inputs,
                "search_in": search_in,
                "search": search,
            }
        )
        return request.render("coupon_portal.portal_my_coupons", values)
