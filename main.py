from fasthtml.common import *
import requests

app, rt = fast_app(hdrs=(picolink))

collections = [
    "accessories",
    "lot-1-tops",
    "lot-2-trousers",
    "lot-3-jackets",
    "lot-4-outerwear",
    "lot-5-knitwear",
    "lot-6-jerseys",
    "lot-7-denim",
    "lot-8-leather",
]


def mk_opts(nm, cs):
    return (*map(lambda c: Option(c, value=c, selected=c == nm), cs),)


def get_products(col):
    # Fetch product data from the API
    url = f"https://taigatakahashi.com/page-data/collection/{col}/page-data.json"
    response = requests.get(url)
    data = response.json()

    # Extract product information
    products = data["result"]["serverData"]["data"]["collection"]["products"]["edges"]

    return products


def render_header(change_view_href, selected_collection):
    return (
        Title("Taiga Stock Status"),
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
            style="color: black; text-align:center; margin: 8px 5px; font-size:24px;",
        ),
        # Change view button
        Div(
            A(
                "Change view",
                href=change_view_href,
                style="text-decoration: underline; color: black;",
            ),
            style="text-align: center; padding-bottom: 20px; margin: 0 20px;",
        ),
        # Add collection dropdown
        Div(
            Label(
                "Collection:",
                for_="collection",
                style="padding-right: 10px; color: black;",
            ),
            Select(
                *mk_opts(selected_collection, collections),
                name="collection",
                onchange="location = this.value;",
                style="margin: 0; display: inline-block; max-width: 200px;",
            ),
            style="display: flex; flex-direction: row; justify-content: space-between; align-items: center; padding: 10px;",
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
            if option["name"].lower() == "size"
            for size in option["values"]
        ],
        "color": next(
            (
                option["values"][0]
                for option in node["options"]
                if option["name"].lower() == "color"
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


@rt("/{col}")
def get(col: str):

    if col is "":
        col = "lot-7-denim"

    products = get_products(col)

    product_cards = [
        create_product_card(extract_product_info(product["node"]))
        for product in products
    ]

    return (
        *render_header(change_view_href=f"/spreadsheet/{col}", selected_collection=col),
        Container(
            *product_cards,
            style="display: grid; gap: 16px; padding: 10px; grid-template-columns: repeat(auto-fit, minmax(300px, 2fr));",
        ),
        Link(
            rel="stylesheet",
            href="./global.css",
        ),
    )


@rt("/spreadsheet/{col}")
def spreadsheet_view(col: str):

    if col is "":
        col = "lot-7-denim"

    products = get_products(col)

    table_rows = [
        create_table_row(extract_product_info(product["node"])) for product in products
    ]

    return Div(
        *render_header(change_view_href=f"/{col}", selected_collection=col),
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
            href="../global.css",
        ),
    )


serve()
