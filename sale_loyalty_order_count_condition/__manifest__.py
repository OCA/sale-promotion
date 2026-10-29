{
    "name": "Sale Loyalty Order Count Condition",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "development_status": "Beta",
    "license": "AGPL-3",
    "summary": "Restrict loyalty rules to first or repeat customer orders, "
    "counted on order history or per promotion code",
    "author": "Daniel Reis, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": ["sale_loyalty"],
    "data": [
        "views/loyalty_program_views.xml",
        "views/loyalty_rule_views.xml",
    ],
    "installable": True,
    "application": False,
}
