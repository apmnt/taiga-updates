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


def extract_product_info(node):
    return {
        "title": node["title"],
        "price": node["priceRange"]["minVariantPrice"]["amount"],
        "url": f"https://taigatakahashi.com/products/{node['handle']}/",
        "src": (
            node["featuredImage"]["originalSrc"] if node.get("featuredImage") else ""
        ),
        "sizes": [
            {
                "size": size,
                "quantity": next(
                    (
                        variant["node"]["quantityAvailable"]
                        for variant in node["variants"]["edges"]
                        if variant["node"]["selectedOptions"][0]["value"] == size
                    ),
                    0,
                ),
            }
            for option in node["options"]
            if option["name"] == "SIZE"
            for size in option["values"]
        ],
        "color": next(
            (
                option["values"][0]
                for option in node["options"]
                if option["name"] == "COLOR"
            ),
            "",
        ),
    }


def create_product_card(info):
    image_content = Img(
        src=info["src"],
        alt=info["title"],
        style="width:100%; height:auto;",
    )

    size_spans = [
        Span(
            f"{size_info['size']}",
            style=f"color: {'black' if size_info['quantity'] > 0 else 'rgb(189,188,183)'}; margin-right: 5px;",
        )
        for size_info in info["sizes"]
    ]

    price_sizes = Div(
        P(
            f"¥{float(info['price']):,.0f}",
            style="margin:0; color: black;",
        ),
        P(
            *size_spans,
            style="margin:0; color: black;",
        ),
        style="display:flex; justify-content: space-between; align-items: center; width:100%;",
    )

    image_link = A(
        image_content,
        href=info["url"],
        target="_blank",
        style="text-decoration: none; color: black;",
    )
    title_link = A(
        f"{info['title']}",
        href=info["url"],
        target="_blank",
        style="text-decoration: none; color: black;",
    )

    return Card(
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


def create_table_row(info):
    title_with_color = f"{info['title']} ({info['color']})"

    sizes = ", ".join(
        size_info["size"] for size_info in info["sizes"] if size_info["quantity"] > 0
    )

    return Tr(
        Td(
            A(
                title_with_color,
                href=info["url"],
                target="_blank",
                style="text-decoration: none; color: black;",
            )
        ),
        Td(sizes),
        Td(f"¥{float(info['price']):,.0f}"),
    )


@rt("/")
def get():
    product_cards = [
        create_product_card(extract_product_info(product["node"]))
        for product in products
    ]

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
    table_rows = [
        create_table_row(extract_product_info(product["node"])) for product in products
    ]

    return Div(
        *render_header(change_view_href="/"),
        Table(
            Tr(
                Th("Title", className="th"),
                Th("Sizes", className="th"),
                Th("Price", className="th"),
            ),
            *table_rows,
            className="table",
        ),
        Link(
            rel="stylesheet",
            href="./global.css",
        ),
    )


serve()
