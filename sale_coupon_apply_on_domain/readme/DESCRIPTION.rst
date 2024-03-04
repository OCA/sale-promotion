This module adds a new option in coupon/promotion programs that allows to specify a domain on which it will apply.

TODO: As of now coupon email will display `n% off on your next order` which is wrong if your domain do not match all sold products.
As the domain is evaluated at promotion generation, when sending mail we cannot know all the included products.
We should override the template to tell on which domain is the promotion.
