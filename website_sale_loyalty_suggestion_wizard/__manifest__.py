# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Website Sale Loyalty Suggestion Wizard",
    "summary": "Suggests promotions and allows you to configure and apply these "
    "promotions directly from the website",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "category": "eCommerce",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": [
        "sale_loyalty",
        "sale_loyalty_order_suggestion",
        "website_sale_loyalty_page",
    ],
    "data": ["templates/promotion_templates.xml", "templates/wizard_templates.xml"],
    "assets": {
        "web.assets_frontend": [
            "/website_sale_loyalty_suggestion_wizard/static/src/scss/"
            "website_sale_loyalty_suggestion_wizard.scss",
            "/website_sale_loyalty_suggestion_wizard/static/src/js/*",
        ]
    },
}
