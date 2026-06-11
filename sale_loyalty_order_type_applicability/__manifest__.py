# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Loyalty Order Type Applicability",
    "summary": "Configure the order types where your loyalty programs are available",
    "version": "18.0.1.0.0",
    "category": "Sales/Sales",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sale_loyalty", "sale_order_type"],
    "data": [
        "views/loyalty_program_views.xml",
    ],
}
