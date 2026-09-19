# Codebase Map – ThoughtTronix Store

## 1. The apps and what each owns
- accounts: handles custom user model and authentication. Customers are regular users, while staff has 'is_staff', and admins have 'is_superuser'.
- products: Owns catalog. Category, Product, and tag models. Owns public pages for products and staff tools for managing them.
- orders: Manages shopping cart and the order process.
- dashboard: Provides the analytics page for staff.
- config: controlls the settings and urls for everything.

## 2. The path of one request
When a browser requests the home page (`/`), `config/urls.py` includes the products app’s URLs.  
In `products/urls.py` the empty path matches `CatalogView`.  
That view (in `products/views.py`) queries the products and renders the template `products/catalog.html`, which extends `base.html`.

## 3. A model you read
The user model is the single user model for the website. Staff and admins are 'is_staff' and 'is_superuser'. 

## 4. Deleting a category
If a category is deleted and there is still products within the category, the category is not deleted. The deletion is blocked. The line of code that decides this is products/models.py:70

## 5. Where the tests live
Test files are kept alongside the app they cover. They are then seperated by concern.
`conftest.py` is the project root file. It is the only source of test data. Fixtures are received through dependency rejection. 

## 6. One thing you're still working to understand
A little bit of everything. I thing I ahve a bsaic understanding of things, I just don't feel too confident in understanding what everything does exactly. It's a bit too much for me. 