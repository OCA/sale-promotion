# Copyright 2025 Kencove
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Loyalty Coupon No Mail",
    "summary": "Generate coupons without triggering email notifications",
    "version": "18.0.1.0.0",
    "category": "web",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Kencove, Odoo Community Association (OCA)",
    "maintainers": ["natuan9"],
    "license": "AGPL-3",
    "depends": [
        "loyalty",
    ],
    "data": [
        "views/loyalty_program_views.xml",
        "views/loyalty_mail_views.xml",
    ],
    "assets": {},
}
