# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Link loyalty programs to order lines",
    "summary": "Adds a link between loyalty programs and their generated order lines"
    "for easing tracking",
    "version": "16.0.1.0.1",
    "development_status": "Production/Stable",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": ["sale_loyalty"],
    "data": ["reports/sale_report_views.xml", "views/sale_order_views.xml"],
}
