# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Coupon Limit",
    "summary": "Restrict number of promotions per customer or salesman",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": [
        "coupon_limit",
        "sale_commercial_partner",
        "sale_coupon_order_line_link",
    ],
    "data": ["security/ir.model.access.csv"],
}
