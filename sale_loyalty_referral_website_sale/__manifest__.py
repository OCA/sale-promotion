{
    "name": "Partner Referral - eCommerce",
    "version": "19.0.1.0.0",
    "category": "Website",
    "development_status": "Beta",
    "license": "AGPL-3",
    "summary": "Auto-apply referral codes on eCommerce carts and attribute "
    "orders to the referrer",
    "author": "Daniel Reis, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": ["sale_loyalty_referral", "website_sale"],
    "data": [
        "views/website_sale_templates.xml",
    ],
    "installable": True,
    "auto_install": True,
    "application": False,
}
