# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Coupon Limit",
    "summary": "Restrict number of promotions per customer or salesman",
    "version": "13.0.1.1.4",
    "development_status": "Beta",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": [
        "sale_coupon",
        "sale_commercial_partner",
        "sale_coupon_order_line_link",
    ],
    "data": ["views/sale_coupon_program_views.xml", "security/ir.model.access.csv"],
}
