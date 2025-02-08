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

        # Process sizes and available inventory
        size_boxes = []
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
                    size_boxes.append(
                        Div(
                            f"{size}",
                            # f"{size} ({quantity} left)",
                            style=f"display: table-cell; border:1px solid black; padding:2px; color:{text_color}; text-align:center; min-width:50px; font-size:18px;",
                        )
                    )

        # Wrap the size boxes in a table container so adjacent borders collapse
        sizes_table = Div(
            *size_boxes,
            style="display: table; border-collapse: collapse; margin: 0 auto;",
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
                        sizes_table,
                    ),
                    style="display:flex; flex-direction: column; align-items: left; text-align: left;",
                ),
                style="width:100%; text-align:center; padding:0; margin:0; background: inherit; box-shadow: none; border: none;",
            )
        )

    return (
        Socials(
            title="Vercel + FastHTML",
            site_name="Vercel",
            description="A demo of Vercel and FastHTML integration",
            image="https://vercel.fyi/fasthtml-og",
            url="https://fasthtml-template.vercel.app",
            twitter_site="@vercel",
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
