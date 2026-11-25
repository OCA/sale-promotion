{
    "name": "Partner Referral",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "development_status": "Beta",
    "license": "AGPL-3",
    "summary": "Personal referral links and codes for customers, backed by loyalty "
    "programs",
    "author": "Daniel Reis, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": ["portal", "website", "sale_loyalty"],
    "assets": {
        "web.assets_frontend": [
            "sale_loyalty_referral/static/src/js/referral_share.esm.js",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/loyalty_program.xml",
        "data/ir_actions_server.xml",
        "data/snippet_filter.xml",
        "views/res_config_settings_views.xml",
        "views/loyalty_program_views.xml",
        "views/sale_loyalty_referral_views.xml",
        "views/snippets.xml",
        "views/portal_templates.xml",
        "views/res_partner_views.xml",
        "wizard/sale_loyalty_referral_generate_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "post_init_hook": "_post_init_seed",
}
