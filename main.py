from fasthtml.common import *
import requests
import os
from datetime import datetime, timezone

app, rt = fast_app()

# Default collection shown when none is specified.
DEFAULT_COLLECTION = "men-new"

# Taiga Takahashi now runs on Shopify, so these are Shopify collection handles
# served by https://taigatakahashi.com/collections/<handle>/products.json
collections = [
    "all",
    "men-new",
    "women-new",
    "men-denim",
    "men-tops",
    "men-toursers",
    "men-jackets",
    "men-outerwear",
    "men-knitwear",
    "men-jerseys",
    "men-leather",
    "men-accessories",
    "men-core",
    "men-archive",
    "women-denim",
    "women-tops",
    "women-toursers",
    "women-dress",
    "women-jackets",
    "women-outerwear",
    "women-knitwear",
    "women-jerseys",
    "women-leather",
    "women-accessories",
    "bags",
]


def mk_opts(nm, cs):
    return (*map(lambda c: Option(c, value=c, selected=c == nm), cs),)


def get_products(col):

    if col == "":
        col = DEFAULT_COLLECTION

    # Shopify exposes a public products.json per collection (including a native
    # "all" collection), paginated at 250 items per page.
    products = []
    page = 1
    while True:
        url = f"https://taigatakahashi.com/collections/{col}/products.json"
        response = requests.get(url, params={"limit": 250, "page": page})
        response.raise_for_status()
        batch = response.json().get("products", [])
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 250:
            break
        page += 1

    products.sort(key=lambda product: product["title"].lower())
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
                "",
                for_="collection",
                style="padding-right: 10px; color: black;",
            ),
            Select(
                *mk_opts(selected_collection, collections),
                name="collection",
                onchange="location = this.value;",
                style="margin: 0; display: inline-block; max-width: 200px;",
            ),
            style="display: flex; flex-direction: row; justify-content: space-between; align-items: center; padding: 10px; max-width: 1450px; margin: 0 auto;",
        ),
    )


def extract_product_info(product):
    options = product.get("options", [])
    variants = product.get("variants", [])
    images = product.get("images", [])

    # Shopify no longer exposes exact inventory counts to unauthenticated
    # clients, so availability is a boolean per variant. We map it to a
    # quantity of 1 (in stock) or 0 (sold out) to keep the rest of the UI,
    # which only checks quantity > 0, working unchanged.
    def size_quantity(size_option, size):
        position = size_option["position"]
        variant = next(
            (v for v in variants if v.get(f"option{position}") == size),
            None,
        )
        return 1 if (variant and variant.get("available")) else 0

    size_option = next(
        (o for o in options if o["name"].lower() == "size"),
        None,
    )

    prices = [float(v["price"]) for v in variants if v.get("price") is not None]

    product_info = {
        "title": product["title"],
        "price": min(prices) if prices else 0,
        "handle": product["handle"],
        "url": f"https://taigatakahashi.com/products/{product['handle']}/",
        "src": images[0]["src"] if images else "",
        "sizes": (
            [
                {"size": size, "quantity": size_quantity(size_option, size)}
                for size in size_option["values"]
            ]
            if size_option
            else []
        ),
        "color": next(
            (
                option["values"][0]
                for option in options
                if option["name"].lower() == "color"
            ),
            "",
        ),
    }

    return product_info


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
                P(f"{info['color']}"),
                price_sizes,
            ),
            style="display:flex; flex-direction: column; align-items: left; text-align: left;",
        ),
        style="text-align:center; padding:0; margin:0; background: inherit; box-shadow: none; border: none;",
    )


def create_small_product_card(info):
    # Render a card with a small image on the left and details on the right
    image_content = Img(
        src=info["src"],
        alt=info["title"],
        style="width:auto; height:150px; margin-right: 10px;",
    )

    size_spans = [
        Span(
            f"{size_info['size']}",
            style=f"color: {'black' if size_info['quantity'] > 0 else 'rgb(189,188,183)'}; margin-right: 5px;",
        )
        for size_info in info["sizes"]
    ]

    sizes_colour_price = Div(
        P(
            *size_spans,
            style="margin:0; color: black;",
        ),
        P(
            f"{info['color']}",
            style="margin:0; color:black;",
        ),
        P(
            f"¥{float(info['price']):,.0f}",
            style="margin:0; color: black;",
        ),
        style="",
    )

    text_content = Div(
        P(
            A(
                info["title"],
                href=info["url"],
                target="_blank",
                style="text-decoration: none; color: black; font-size: 18px;",
            ),
            style="margin: 0; margin-top: -5px;",
        ),
        *sizes_colour_price,
        style="display:flex; flex-direction: column; justify-content: start; height: 150px;",  # Set the height to match the image
    )
    return Card(
        Div(
            image_content,
            text_content,
            style="display:flex; align-items:center;",
        ),
        style="text-align:left; padding:10px; margin:0; background:inherit; box-shadow:none; border:none; height: 100%;",
    )


def create_table_row(info, show_quantity=False):
    title_with_color = f"{info['title']} ({info['color']})"
    sizes = ", ".join(
        (
            f"{size_info['size']}-{size_info['quantity']}"
            if show_quantity
            else size_info["size"]
        )
        for size_info in info["sizes"]
        if size_info["quantity"] > 0
    )
    row_elements = [
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
    ]
    return Tr(*row_elements)


@rt("/{col}")
def get(col: str, small: str = "false", hide_sold: str = "false"):

    if col == "":
        col = DEFAULT_COLLECTION

    small_bool = small.lower() == "true"
    hide_sold_bool = hide_sold.lower() == "true"
    small_param = "true" if small_bool else "false"

    # Toggle for product card view
    toggle_href = (
        f"/{col}?small={'false' if small_bool else 'true'}&hide_sold={hide_sold}"
    )
    toggle_text = "Large images" if small_bool else "Small images"

    # Toggle for hide sold-out items
    toggle_hide_sold = "false" if hide_sold_bool else "true"
    hide_sold_text = "Show sold‑out items" if hide_sold_bool else "Hide sold‑out items"
    toggle_hide_sold_href = f"/{col}?small={small_param}&hide_sold={toggle_hide_sold}"

    products = get_products(col)

    # Filter products if hide_sold_bool is True
    product_cards = []
    for product in products:
        info = extract_product_info(product)
        if hide_sold_bool and not any(s["quantity"] > 0 for s in info["sizes"]):
            continue
        card = (create_small_product_card if small_bool else create_product_card)(info)
        product_cards.append(card)

    return (
        *render_header(change_view_href=f"/spreadsheet/{col}", selected_collection=col),
        Div(
            Div(
                A(
                    hide_sold_text,
                    href=toggle_hide_sold_href,
                    style="text-decoration: underline; color: black;",
                ),
                style="padding-bottom: 12px;",
            ),
            Div(
                A(
                    toggle_text,
                    href=toggle_href,
                    style="text-decoration: underline; color: black;",
                ),
                style="padding-bottom: 12px;",
            ),
            style="text-align: right; padding-right: 10px; max-width: 1450px; margin: 0 auto;",
        ),
        Container(
            *product_cards,
            style=(
                "display: grid; gap: 16px; padding: 10px; grid-template-columns: "
                "repeat(auto-fit, minmax(300px, 2fr));"
                if not small_bool
                else "display: grid; gap: 16px; padding: 10px; grid-template-columns: "
                "repeat(auto-fit, minmax(400px, 1fr));"
            ),
        ),
        Link(
            rel="stylesheet",
            href="./global.css",
        ),
    )


@rt("/spreadsheet/{col}")
def spreadsheet_view(col: str, show_qty: str = "false", hide_sold: str = "false"):
    show_qty_bool = show_qty.lower() == "true"
    hide_sold_bool = hide_sold.lower() == "true"
    show_qty_param = "true" if show_qty_bool else "false"

    # Toggle for table view quantities
    toggle_href = f"/spreadsheet/{col}?show_qty={'false' if show_qty_bool else 'true'}&hide_sold={hide_sold}"
    toggle_text = "Hide Quantities" if show_qty_bool else "Show Quantities"

    # Toggle for hide sold-out items
    toggle_hide_sold = "false" if hide_sold_bool else "true"
    hide_sold_text = "Show sold‑out items" if hide_sold_bool else "Hide sold‑out items"
    toggle_hide_sold_href = (
        f"/spreadsheet/{col}?show_qty={show_qty_param}&hide_sold={toggle_hide_sold}"
    )

    products = get_products(col)
    table_rows = []
    for product in products:
        info = extract_product_info(product)
        if hide_sold_bool and not any(s["quantity"] > 0 for s in info["sizes"]):
            continue
        table_rows.append(create_table_row(info, show_quantity=show_qty_bool))

    return Div(
        *render_header(change_view_href=f"/{col}", selected_collection=col),
        Div(
            Div(
                A(
                    hide_sold_text,
                    href=toggle_hide_sold_href,
                    style="text-decoration: underline; color: black;",
                ),
                style="padding-bottom: 12px;",
            ),
            Div(
                A(
                    toggle_text,
                    href=toggle_href,
                    style="text-decoration: underline; color: black;",
                ),
                style="padding-bottom: 12px;",
            ),
            style="text-align: right; padding-right: 10px; max-width: 1450px; margin: 0 auto;",
        ),
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
