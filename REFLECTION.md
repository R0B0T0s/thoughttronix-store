## PRODUCT IMAGES
Q1- The question Claude gave me was: Where else should product images appear? I answered with: Back-office list (Recommended), Order history, Cart. I thought that haviing images show up in the cart and order history was goiing to be great, oh how I was wrong. I later reverted it so that images only show up in the catalog and in the item description. 
Q2-There are two imagefields one in products/models.py line 82 and another in products/forms.py line 61.     image = models.ImageField(upload_to="products/", blank=True) /
class ProductImageForm(forms.Form):
Upload_to is how you can direct files to be stored in specific locations.
Reguarding the <form>,                            <form method="post"
                    action="{% url 'products:manage_product_image' product.pk %}"
                    enctype="multipart/form-data"
                    class="space-y-4">  ,  
can be found in products/manage_product_form.html on line 49. Enctype is needed because it packages file data together into a http request without ruining the contents. 
Q3- Path on disc is thoughttronix-store/media/products/Watermellon_robot.webp. The value is in products/Watermellon_robot.webp, and the url requested is http://127.0.0.1:8000/media/products/Watermellon_robot.webp.

## FEATURED PRODUCTS
Q1- Line 68 in products\models.py , lines 22 & 23 in products\admin.py , line 56 in products\forms.py , and all of products/migrations/0003_product_is_featured.py were created to have the Featured tag exist. Lines 73-75 and 28-31 of templates\products\catalog.html and templates\products\detail.html implemented the ability of the Featured badge. So the first three sections of code allow the admin to make a product "featured" while the last the last two make it shown to everyone else. Light switch and light bulb. Specifically, products\admin.py is out switch while templates\products\catalog.html is our bulb. The rest of the code is the wires connecting the two and color/size of the bulb. 
Q2- I checked the edit product page, the default product catalog page, and the product detail page. First, had to make sure that the product was marked as "Featured" on the edit product page. Second, I went to the second and third pages of the catalog and saw that all 3 items were marked as featured. Lastly, I clicked on each product's specific product description page, all were marked. 
Q3- The first time I checked the website to make sure that it was working, I had a display error. So I asked the ai to make migrations, it did and the display error went away. 


## Discount Coupons
Q1- One question Claude asked was "Should a coupon have any usage limits, beyond its active window?" I said that we should have a one coupon per customer limit. Claude recommended that we set no coupon limit at all. Now, if someone used the same code over and over again to get 100% off an order, you have made a terrible shopping website.
Q2- The product selection section was poorly handled by the AI on it's first attempt. Text was overlapping, and areas where products could be selected was difficult to properly select what you wanted. The fix is similar to the origional choice, except we now all options can be read and selected options have a checkmark. 