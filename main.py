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
        currency = node["priceRange"]["minVariantPrice"]["currencyCode"]
        image_url = (
            node["featuredImage"]["originalSrc"] if node.get("featuredImage") else ""
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

        sizes_field = P(
            *size_spans,
            style="font-size:18px;",
        )

        product_cards.append(
            Card(
                Group(
                    (
                        (
                            Img(
                                src=image_url,
                                alt=title,
                                style="width:100%; height:auto;",
                            )
                            if image_url
                            else ""
                        ),
                        P(
                            f"{title}",
                            style="font-size:18px;",
                        ),
                        P(
                            f"{price} {currency}",
                            style="font-size:18px;",
                        ),
                        sizes_field,
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
