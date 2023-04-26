# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Coupon Portal",
    "summary": "Add possibility to see your coupons on portal",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["CarlosRoca13"],
    "license": "AGPL-3",
    "depends": ["sale_coupon"],
    "data": ["templates/coupon_portal_templates.xml"],
    "assets": {
        "web.assets_tests": ["/coupon_portal/static/src/js/tour_coupon_portal.js"]
    },
}
