This module allows for customizable coupon code generation. It allows you to 
generate coupon codes based on custom format defined by a mask and a list of
forbidden characters.

Mask format is a string that can contain the following characters:
* X means a random uppercase letter
* x means a random lowercase letter
* 0 means a random digit
all other characters are used literally.
