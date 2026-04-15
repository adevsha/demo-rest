from app.data import store
from app.models.product import ProductCreate, ProductUpdate


def list_products() -> list[dict]:
    return list(store.products.values())


def get_product(product_id: int) -> dict | None:
    return store.products.get(product_id)


def create_product(data: ProductCreate) -> dict:
    product = {"id": store.next_product_id, **data.model_dump()}
    store.products[store.next_product_id] = product
    store.next_product_id += 1
    return product


def update_product(product_id: int, data: ProductUpdate) -> dict | None:
    if product_id not in store.products:
        return None
    updates = data.model_dump(exclude_unset=True)
    store.products[product_id].update(updates)
    return store.products[product_id]


def delete_product(product_id: int) -> bool:
    return store.products.pop(product_id, None) is not None
