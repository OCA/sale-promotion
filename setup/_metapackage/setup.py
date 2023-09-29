import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-sale-promotion",
    description="Meta package for oca-sale-promotion Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-coupon_chatter>=16.0dev,<16.1dev',
        'odoo-addon-sale_loyalty_order_line_link>=16.0dev,<16.1dev',
        'odoo-addon-website_sale_loyalty_page>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
