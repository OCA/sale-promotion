import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-sale-promotion",
    description="Meta package for oca-sale-promotion Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-sale_coupon_auto_refresh',
        'odoo14-addon-sale_coupon_criteria_order_based',
        'odoo14-addon-sale_coupon_delivery_auto_refresh',
        'odoo14-addon-sale_coupon_order_line_link',
        'odoo14-addon-sale_coupon_reward_fixed_price',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
