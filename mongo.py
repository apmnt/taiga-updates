import requests
import concurrent.futures
import os
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection setup
MONGODB_USER = os.environ.get("MONGODB_USER")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD")
MONGODB_URI = f"mongodb+srv://{MONGODB_USER}:{MONGODB_PASSWORD}@taiga.q8szlsh.mongodb.net/?retryWrites=true&w=majority&appName=taiga"
MONGODB_DB = os.environ.get("MONGODB_DB")
MONGODB_HISTORY_COLLECTION = os.environ.get("MONGODB_HISTORY_COLLECTION")
MONGODB_EVENTS_COLLECTION = os.environ.get("MONGODB_EVENTS_COLLECTION")
MONGODB_SNAPSHOTS_COLLECTION = "stock_history_timeseries"


# Initialize MongoDB client
mongo_client = None
db = None
collection = None
events_collection = None
snapshot_collection = None

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


def connect_to_mongodb():
    global mongo_client, db, collection, events_collection, snapshot_collection
    try:
        mongo_client = MongoClient(MONGODB_URI)
        db = mongo_client[MONGODB_DB]
        collection = db[MONGODB_HISTORY_COLLECTION]
        events_collection = db[MONGODB_EVENTS_COLLECTION]
        snapshot_collection = db[MONGODB_SNAPSHOTS_COLLECTION]
        print("Connected to MongoDB successfully")
        return True
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return False


def update_stock_history(products):
    """Update the stock history for a product in MongoDB
    sizes_data: A list of dictionaries, each containing 'size' and 'quantity'"""
    if collection is None and not connect_to_mongodb():
        print("MongoDB connection not available, skipping stock history update")
        return

    for product in products:
        try:
            info = extract_product_info(product["node"])

            product_id = info["handle"]
            sizes_data = info["sizes"]

            # Get current timestamp as a datetime object
            current_time = datetime.now(timezone.utc)

            # Check if this product exists
            product_record = collection.find_one({"product_id": product_id})

            # Convert sizes_data to a dictionary for easier storage
            sizes_stock = {item["size"]: item["quantity"] for item in sizes_data}

            # Flag to force event creation on first load
            is_first_load = False

            if product_record:
                # Get the last recorded stock snapshot
                stock_history = product_record.get("stock_history", [])

                # Check if stock has changed since last record
                if stock_history:
                    last_entry = stock_history[-1]
                    last_sizes_stock = last_entry.get("sizes", {})

                    # Only update if the quantities have changed
                    if last_sizes_stock != sizes_stock:

                        print(
                            f"Stock change detected for product {product_id} with change from {last_sizes_stock} to {sizes_stock}"
                        )

                        # Track stock change events
                        for size, new_stock in sizes_stock.items():
                            old_stock = last_sizes_stock.get(size, 0)
                            if new_stock != old_stock:
                                # Create an event record for this stock change
                                if events_collection is not None:
                                    events_collection.insert_one(
                                        {
                                            "timestamp": current_time,
                                            "product_id": product_id,
                                            "size": size,
                                            "old_stock": old_stock,
                                            "new_stock": new_stock,
                                        }
                                    )
                                    print(
                                        f"Stock change event recorded for {product_id}, size {size}: {old_stock} -> {new_stock}"
                                    )

                        # Add new snapshot with timestamp and all sizes
                        collection.update_one(
                            {"product_id": product_id},
                            {
                                "$push": {
                                    "stock_history": {
                                        "timestamp": current_time,
                                        "sizes": sizes_stock,
                                    }
                                }
                            },
                        )
                        print(
                            f"Updated stock history for product {product_id} with new quantities"
                        )
                    else:
                        print(
                            f"No stock change for product {product_id}, skipping update"
                        )
                else:
                    # No history yet but product exists - add the first entry
                    collection.update_one(
                        {"product_id": product_id},
                        {
                            "$push": {
                                "stock_history": {
                                    "timestamp": current_time,
                                    "sizes": sizes_stock,
                                }
                            }
                        },
                    )
                    print(f"Added first stock history entry for product {product_id}")
                    is_first_load = True
            else:
                # Product doesn't exist yet, create it
                collection.insert_one(
                    {
                        "product_id": product_id,
                        "stock_history": [
                            {"timestamp": current_time, "sizes": sizes_stock}
                        ],
                    }
                )
                print(f"Created new stock history for product {product_id}")
                is_first_load = True

            # When creating a new product or first load, treat all stock as new (from 0)
            if is_first_load and events_collection is not None:
                for size, quantity in sizes_stock.items():
                    # Record all sizes, not just those with stock > 0
                    events_collection.insert_one(
                        {
                            "timestamp": current_time,
                            "product_id": product_id,
                            "size": size,
                            "old_stock": 0,
                            "new_stock": quantity,
                        }
                    )
                    print(
                        f"Stock event recorded for {product_id}, size {size}: 0 -> {quantity}"
                    )
        except Exception as e:
            print(f"Error updating stock history: {e}")


def add_snapshot():
    """Add a stock snapshot for all products in the current collection"""
    if not connect_to_mongodb():
        print("MongoDB connection not available, skipping snapshot")
        return

    try:
        for col in collections[1:]:
            products = get_products(col)
            for product in products:
                node = product["node"]
                product_info = extract_product_info(node)
                update_stock_history(product_info["handle"], product_info["sizes"])
        print("Stock snapshot added for all products")
    except Exception as e:
        print(f"Error adding stock snapshot: {e}")


def build_snapshot_docs(products, ts):
    """
    Flatten products into per-size time-series docs:
    One document per product-size so dashboard can filter easily.
    """
    docs = []
    for product in products:
        node = product["node"]
        info = extract_product_info(node)
        product_id = info["handle"]
        for size_entry in info["sizes"]:
            docs.append(
                {
                    "timestamp": ts,
                    "product_id": product_id,
                    "size": size_entry["size"],
                    "quantity": size_entry["quantity"],
                }
            )
    return docs


def add_global_snapshot(products):
    """
    Capture a full snapshot of all products into the time-series collection.
    """

    if not connect_to_mongodb():
        raise RuntimeError("MongoDB connection not available")

    if snapshot_collection is None:
        raise RuntimeError("MongoDB snapshot collection not initialized")

    try:
        ts = datetime.now(timezone.utc)
        docs = build_snapshot_docs(products, ts)
        if docs:
            snapshot_collection.insert_many(docs, ordered=False)
            print(f"Inserted snapshot: {len(docs)} rows at {ts.isoformat()}")
        else:
            print("No products found to snapshot")
    except Exception as e:
        print(f"Error inserting global snapshot: {e}")


def get_all_products():

    # Loop through all collections and combine the products, ignoring duplicates
    products = []
    product_ids = set()

    # Use ThreadPoolExecutor to fetch products concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_collection = {
            executor.submit(get_products, collection): collection
            for collection in collections[1:]
        }
        for future in concurrent.futures.as_completed(future_to_collection):
            try:
                collection_products = future.result()
                for product in collection_products:
                    product_id = product["node"]["id"]
                    if product_id not in product_ids:
                        product_ids.add(product_id)
                        products.append(product)
                print(f"Collection {future_to_collection[future]} fetched")
            except Exception as exc:
                print(
                    f"Collection {future_to_collection[future]} generated an exception: {exc}"
                )
    products.sort(key=lambda product: product["node"]["title"])

    return products


def get_products(col):
    # Fetch product data from the API
    url = f"https://taigatakahashi.com/page-data/collection/{col}/page-data.json"
    response = requests.get(url)
    data = response.json()

    # Extract product information
    products = data["result"]["serverData"]["data"]["collection"]["products"]["edges"]
    return products


def extract_product_info(node):
    product_info = {
        "handle": node["handle"],
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
    }

    return product_info


def update_stock_history_for_all():
    """
    Update stock history for all products across all collections.
    """
    if not connect_to_mongodb():
        print("MongoDB connection not available, skipping stock history update")
        return

    products = get_all_products()


if __name__ == "__main__":
    connect_to_mongodb()
    products = get_all_products()
    # add_global_snapshot(products)
    update_stock_history(products)
