import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-sale-promotion",
    description="Meta package for oca-sale-promotion Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-coupon_chatter>=16.0dev,<16.1dev',
        'odoo-addon-loyalty_incompatibility>=16.0dev,<16.1dev',
        'odoo-addon-loyalty_initial_date_validity>=16.0dev,<16.1dev',
        'odoo-addon-loyalty_limit>=16.0dev,<16.1dev',
        'odoo-addon-loyalty_mass_mailing>=16.0dev,<16.1dev',
        'odoo-addon-loyalty_partner_applicability>=16.0dev,<16.1dev',
        'odoo-addon-sale_loyalty_incompatibility>=16.0dev,<16.1dev',
        'odoo-addon-sale_loyalty_initial_date_validity>=16.0dev,<16.1dev',
        'odoo-addon-sale_loyalty_limit>=16.0dev,<16.1dev',
        'odoo-addon-sale_loyalty_order_info>=16.0dev,<16.1dev',
        'odoo-addon-sale_loyalty_order_line_link>=16.0dev,<16.1dev',
        'odoo-addon-sale_loyalty_partner>=16.0dev,<16.1dev',
        'odoo-addon-sale_loyalty_partner_applicability>=16.0dev,<16.1dev',
        'odoo-addon-website_sale_loyalty_page>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
