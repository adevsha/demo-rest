class EmailAlreadyRegisteredError(Exception):
    pass


class InsufficientStockError(Exception):
    def __init__(self, product_id: int):
        self.product_id = product_id
        super().__init__(f"Insufficient stock for product {product_id}")


class ProductNotFoundError(Exception):
    def __init__(self, product_id: int):
        self.product_id = product_id
        super().__init__(f"Product {product_id} not found")
