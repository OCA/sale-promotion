Gift Card Settings
=====================
Settings
-----------
In Sales > Configuration
-  Settings > Pricing Section : activate "Gift Cards" and select a default journal

Gift Cards Template
---------------------------------
All the gift cards of one template will inherit its template parameters.

In Sales > Products >  Gift Cards Template : Create or select a gift card template
- **Code Mask** : configure the code format. Default value (XXXXXX-00): x means a random lowercase letter, X means a random uppercase letter, 0 means a random digit. From `base_generate_code <https://github.com/OCA/server-tools//>`_.
- **Duration** : In months. Set to 0 in order to have no duration limitation.
- **Divisible** : If true, the gift card amount can be used in several times, if not, only one time.
- **Initial amount** : Choose the initial amount


Buy a Gift Card
================
- Order a gift card, the gift card amount will be equal to the Initial amount  of the gift card template by default or the sale line price.
- The gift card will be activated at invoice confirmation.

Use Gift Card as Payment
========================
In Invoicing >  Register a Payment >  Gift Card Payment
Select a validation :
- From partner (if partner previously buy / is beneficiary of gift card) or enter a valid code.
- Select amount and validate payment.
Then, a gift card line is created and linked to the gift card.
