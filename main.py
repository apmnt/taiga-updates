from fasthtml.common import *
import requests

app, rt = fast_app(hdrs=(picolink))

# Fetch product data from the API
url = "https://taigatakahashi.com/page-data/collection/lot-7-denim/page-data.json"
response = requests.get(url)
data = response.json()

# Extract product information
products = data["result"]["serverData"]["data"]["collection"]["products"]["edges"]


def render_header(change_view_href):
    return (
        Socials(
            title="Taiga Takahashi stock status",
            site_name="Vercel",
            description="A simple FastHTML clone of the Taiga Takahashi website, showing a quick overview of the stocked items.",
            w=1024,
            h=544,
            creator="apmnt",
            image="https://cdn.sanity.io/images/74v34t5m/production/edbf98b124e66f73c8c8eea6e32a098af6992e27-4597x2442.jpg?w=1024&h=544&auto=format",
            url="https://taiga-updates.vercel.app",
        ),
        P(
            "T.T stock status",
            style="text-align:center; margin:0px 0; font-size:36px; color: black;",
        ),
        P(
            "made by ",
            A(
                "apmnt",
                href="https://github.com/apmnt",
                style="color: black; text-decoration: underline;",
            ),
            style=f"color: black; text-align:center; margin: 8px 5px; font-size:24px;",
        ),
        Div(
            A(
                "Change view",
                href=change_view_href,
                style="text-decoration: underline; color: black;",
            ),
            style="text-align: center; padding-bottom: 20px",
        ),
    )


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
                            style=f"color: {text_color}; margin-right: 5px;",
                        )
                    )

        # Build a container for price and sizes, aligned appropriately
        price_sizes = Div(
            P(
                f"¥{float(price):,.0f}",
                style="margin:0; color: black;",
            ),
            P(
                *size_spans,
                style="margin:0; color: black;",
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
            style="text-decoration: none; color: black;",
        )
        title_link = A(
            f"{title}",
            href=product_url,
            target="_blank",
            style="text-decoration: none; color: black;",
        )

        # Build the product card. Only the image and title are clickable.
        product_cards.append(
            Card(
                Group(
                    (
                        image_link,
                        P(title_link),
                        price_sizes,
                    ),
                    style="display:flex; flex-direction: column; align-items: left; text-align: left;",
                ),
                style="text-align:center; padding:0; margin:0; background: inherit; box-shadow: none; border: none;",
            )
        )

    return (
        *render_header(change_view_href="/spreadsheet"),
        Container(
            *product_cards,
            style="display: grid; gap: 16px; padding: 10px; grid-template-columns: repeat(auto-fit, minmax(300px, 2fr));",
        ),
        Link(
            rel="stylesheet",
            href="./global.css",
        ),
    )


@rt("/spreadsheet")
def spreadsheet_view():
    table_rows = []

    for product in products:
        node = product["node"]
        title = node["title"]
        price = node["priceRange"]["minVariantPrice"]["amount"]
        product_url = f"https://taigatakahashi.com/products/{node['handle']}/"

        # Extract color
        color = next(
            (
                option["values"][0]
                for option in node["options"]
                if option["name"] == "COLOR"
            ),
            "",
        )

        # Append color to title
        title_with_color = f"{title} ({color})"

        # Extract sizes that are in stock
        sizes = ", ".join(
            size
            for option in node["options"]
            if option["name"] == "SIZE"
            for size in option["values"]
            if any(
                variant["node"]["selectedOptions"][0]["value"] == size
                and variant["node"]["quantityAvailable"] > 0
                for variant in node["variants"]["edges"]
            )
        )

        table_rows.append(
            Tr(
                Td(
                    A(
                        title_with_color,
                        href=product_url,
                        target="_blank",
                        style="text-decoration: none; color: black;",
                    )
                ),
                Td(sizes),
                Td(f"¥{float(price):,.0f}"),
            )
        )

    return Div(
        *render_header(change_view_href="/"),
        Table(
            Tr(
                Th("Title", style="min-width: 100px;"),
                Th("Sizes", style="min-width: 100px;"),
                Th("Price", style="min-width: 100px;"),
            ),
            *table_rows,
            style="width: 100%; border-collapse: collapse;",
        ),
        Link(
            rel="stylesheet",
            href="./global.css",
        ),
    )


serve()
