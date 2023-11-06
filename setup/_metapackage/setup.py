import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-sale-promotion",
    description="Meta package for oca-sale-promotion Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-sale_coupon_auto_refresh',
        'odoo13-addon-sale_coupon_chatter',
        'odoo13-addon-sale_coupon_commercial_partner_applicability',
        'odoo13-addon-sale_coupon_criteria_multi_product',
        'odoo13-addon-sale_coupon_criteria_order_based',
        'odoo13-addon-sale_coupon_delivery_auto_refresh',
        'odoo13-addon-sale_coupon_domain_free_product',
        'odoo13-addon-sale_coupon_domain_product_discount',
        'odoo13-addon-sale_coupon_financial_risk',
        'odoo13-addon-sale_coupon_incompatibility',
        'odoo13-addon-sale_coupon_limit',
        'odoo13-addon-sale_coupon_mass_mailing',
        'odoo13-addon-sale_coupon_multi_gift',
        'odoo13-addon-sale_coupon_multiple_code_program',
        'odoo13-addon-sale_coupon_multiplier_free_product',
        'odoo13-addon-sale_coupon_order_line_link',
        'odoo13-addon-sale_coupon_order_pending',
        'odoo13-addon-sale_coupon_order_pending_commercial_partner',
        'odoo13-addon-sale_coupon_order_suggestion',
        'odoo13-addon-sale_coupon_partner',
        'odoo13-addon-sale_coupon_portal',
        'odoo13-addon-sale_coupon_portal_commercial_partner_applicability',
        'odoo13-addon-sale_coupon_promotion_generate_coupon',
        'odoo13-addon-sale_coupon_selection_wizard',
        'odoo13-addon-website_sale_coupon_page',
        'odoo13-addon-website_sale_coupon_restrict',
        'odoo13-addon-website_sale_coupon_selection_wizard',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
