# Copyright 2024 Moka Tourisme
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Gift Card limited to',
    'version': '15.0.1.0.0',
    'author' : 'Moka Tourisme',
    "website": "https://www.mokatourisme.fr",
    'description' : "Limite l'utilisation des cartes cadeaux sur des articles",
    'category': 'Sales',
    "license": "AGPL-3",
    'summary': 'Gift card personalisation module',
    'depends': ['gift_card', 'point_of_sale', 'sale'],
    'data': [
        'views/gift_card_view.xml',
        'views/gift_card_design_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}