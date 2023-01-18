# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Promotion Discounts on Selected Attributes",
    "summary": "Allow attribute prices to not be subject to promotion discounts",
    "version": "16.0.0.0.0",
    "maintainers": ["diogocsc"],
    "website": "https://github.com/OCA/sale-promotion",
    "category": "Sales",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sale_loyalty"],
    "data": ["views/loyalty_reward_views.xml"],
}
