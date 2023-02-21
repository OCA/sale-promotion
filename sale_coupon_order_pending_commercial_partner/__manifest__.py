# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Pending Commercial Entity Coupons",
    "summary": "Glue module to show pending coupons of the commercial entity",
    "version": "13.0.1.0.0",
    "development_status": "Beta",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "auto_install": True,
    "depends": [
        "sale_coupon_commercial_partner_applicability",
        "sale_coupon_order_pending",
    ],
}
