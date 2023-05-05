import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-sale-promotion",
    description="Meta package for oca-sale-promotion Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-coupon_chatter>=15.0dev,<15.1dev',
        'odoo-addon-coupon_criteria_multi_product>=15.0dev,<15.1dev',
        'odoo-addon-coupon_domain_free_product>=15.0dev,<15.1dev',
        'odoo-addon-coupon_domain_product_discount>=15.0dev,<15.1dev',
        'odoo-addon-coupon_incompatibility>=15.0dev,<15.1dev',
        'odoo-addon-coupon_limit>=15.0dev,<15.1dev',
        'odoo-addon-coupon_mass_mailing>=15.0dev,<15.1dev',
        'odoo-addon-coupon_multi_gift>=15.0dev,<15.1dev',
        'odoo-addon-coupon_multiplier_free_product>=15.0dev,<15.1dev',
        'odoo-addon-coupon_portal>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_auto_refresh>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_criteria_multi_product>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_criteria_order_based>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_delivery_auto_refresh>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_domain_free_product>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_domain_product_discount>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_incompatibility>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_limit>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_multi_gift>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_multiple_code_program>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_multiplier_free_product>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_order_line_link>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_order_suggestion>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_partner>=15.0dev,<15.1dev',
        'odoo-addon-sale_coupon_selection_wizard>=15.0dev,<15.1dev',
        'odoo-addon-website_sale_coupon_page>=15.0dev,<15.1dev',
        'odoo-addon-website_sale_coupon_restrict>=15.0dev,<15.1dev',
        'odoo-addon-website_sale_coupon_selection_wizard>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
