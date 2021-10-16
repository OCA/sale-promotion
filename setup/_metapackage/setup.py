import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-sale-promotion",
    description="Meta package for oca-sale-promotion Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-sale_coupon_auto_refresh',
        'odoo13-addon-sale_coupon_criteria_multi_product',
        'odoo13-addon-sale_coupon_limit',
        'odoo13-addon-sale_coupon_mass_mailing',
        'odoo13-addon-sale_coupon_multi_gift',
        'odoo13-addon-sale_coupon_multiplier_free_product',
        'odoo13-addon-sale_coupon_order_line_link',
        'odoo13-addon-sale_coupon_partner',
        'odoo13-addon-website_sale_coupon_page',
        'odoo13-addon-website_sale_coupon_restrict',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
