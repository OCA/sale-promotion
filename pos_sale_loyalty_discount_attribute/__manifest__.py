# Copyright (C) 2023 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "POS - Promotion Discounts on Selected Attributes",
    "version": "16.0.1.0.0",
    "summary": """Allow attribute prices to not be subject to promotion discounts in POS.""",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Point of Sale",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": ["pos_loyalty", "sale_loyalty_discount_attribute"],
    "maintainers": ["ursais"],
    "installable": True,
    "assets": {
        "point_of_sale.assets": [
            "pos_sale_loyalty_discount_attribute/static/src/js/**/*.js",
        ],
    },
}
