from fasthtml.common import *
import requests

app, rt = fast_app(hdrs=(picolink))

# Fetch product data from the API
url = "https://taigatakahashi.com/page-data/collection/lot-7-denim/page-data.json"
response = requests.get(url)
data = response.json()

# Extract product information
products = data["result"]["serverData"]["data"]["collection"]["products"]["edges"]


@rt("/")
def get():
    product_cards = []

    for product in products:
        node = product["node"]
        title = node["title"]
        price = node["priceRange"]["minVariantPrice"]["amount"]
        # Build gallery: use featuredImage plus additionalImages if available
        gallery = []
        if node.get("featuredImage"):
            gallery.append(node["featuredImage"]["originalSrc"])
        if node.get("additionalImages"):
            for img in node["additionalImages"]:
                gallery.append(img["originalSrc"])

        # Create image content: a single image
        image_content = Img(
            src=gallery[0] if gallery else "",
            alt=title,
            style="width:100%; height:auto;",
        )

        # Process sizes and available inventory and build spans
        size_spans = []
        for option in node["options"]:
            if option["name"] == "SIZE":
                for size in option["values"]:
                    quantity = next(
                        (
                            variant["node"]["quantityAvailable"]
                            for variant in node["variants"]["edges"]
                            if variant["node"]["selectedOptions"][0]["value"] == size
                        ),
                        0,
                    )
                    text_color = "black" if quantity > 0 else "rgb(189,188,183)"
                    size_spans.append(
                        Span(
                            f"{size}",
                            style=f"color: {text_color}; font-size:18px; margin-right: 5px;",
                        )
                    )

        # Build a container for price and sizes, aligned appropriately
        price_sizes = Div(
            P(
                f"¥{float(price):,.0f}",
                style="font-size:18px; margin:0;",
            ),
            P(
                *size_spans,
                style="font-size:18px; margin:0;",
            ),
            style="display:flex; justify-content: space-between; align-items: center; width:100%;",
        )

        # Use the product's handle to create a product URL link.
        product_url = f"https://taigatakahashi.com/products/{node['handle']}/"

        # Wrap only the image and title in an anchor element linking to the corresponding product page.
        image_link = A(
            image_content,
            href=product_url,
            target="_blank",
            style="text-decoration: none; color: inherit;",
        )
        title_link = A(
            f"{title}",
            href=product_url,
            target="_blank",
            style="text-decoration: none; color: inherit;",
        )

        # Build the product card. Only the image and title are clickable.
        product_cards.append(
            Card(
                Group(
                    (
                        image_link,
                        P(
                            title_link,
                            style="font-size:18px;",
                        ),
                        price_sizes,
                    ),
                    style="display:flex; flex-direction: column; align-items: left; text-align: left;",
                ),
                style="width:100%; text-align:center; padding:0; margin:0; background: inherit; box-shadow: none; border: none;",
            )
        )

    return (
        Socials(
            title="Taiga Takahashi stock status",
            site_name="Vercel",
            description="A simple clone of the Taiga Takahashi website, showing a quick overview of the stocked items.",
            image="https://cdn.sanity.io/images/74v34t5m/production/edbf98b124e66f73c8c8eea6e32a098af6992e27-4597x2442.jpg?w=1024&h=544&auto=format",
            url="https://taiga-updates.vercel.app",
        ),
        P(
            "T.T stock status",
            style="text-align:center; margin:0px 0; font-size:36px;",
        ),
        P(
            "made by ",
            A(
                "apmnt",
                href="https://github.com/apmnt",
                style="color: inherit; text-decoration: underline;",
            ),
            style="text-align:center; margin:5px 5px; font-size:24px;",
        ),
        Container(
            *product_cards,
            style="display:flex; flex-wrap:wrap; justify-content:center; max-width:100%;",
        ),
        Link(
            rel="stylesheet",
            href="./global.css",
        ),
    )


serve()
