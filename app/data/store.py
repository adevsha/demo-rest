users: dict[int, dict] = {
    1: {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "age": 30},
    2: {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "age": 25},
    3: {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "age": 35},
    4: {"id": 4, "name": "Diana Prince", "email": "diana@example.com", "age": 28},
    5: {"id": 5, "name": "Eve Wilson", "email": "eve@example.com", "age": 32},
    6: {"id": 6, "name": "Frank Miller", "email": "frank@example.com", "age": 45},
    7: {"id": 7, "name": "Grace Lee", "email": "grace@example.com", "age": 27},
    8: {"id": 8, "name": "Henry Davis", "email": "henry@example.com", "age": 38},
    9: {"id": 9, "name": "Ivy Chen", "email": "ivy@example.com", "age": 22},
    10: {"id": 10, "name": "Jack Taylor", "email": "jack@example.com", "age": 55},
}

products: dict[int, dict] = {
    1: {"id": 1, "name": "Laptop", "description": "A powerful laptop", "price": 999.99, "in_stock": True},
    2: {"id": 2, "name": "Wireless Mouse", "description": "Ergonomic wireless mouse", "price": 29.99, "in_stock": True},
    3: {"id": 3, "name": "Mechanical Keyboard", "description": "RGB mechanical keyboard", "price": 149.99, "in_stock": True},
    4: {"id": 4, "name": "Monitor", "description": "27-inch 4K monitor", "price": 399.99, "in_stock": False},
    5: {"id": 5, "name": "USB-C Hub", "description": "7-in-1 USB-C hub", "price": 49.99, "in_stock": True},
    6: {"id": 6, "name": "Webcam", "description": "1080p HD webcam", "price": 79.99, "in_stock": True},
    7: {"id": 7, "name": "Headphones", "description": "Noise-cancelling headphones", "price": 199.99, "in_stock": False},
    8: {"id": 8, "name": "Desk Lamp", "description": "LED desk lamp with dimmer", "price": 34.99, "in_stock": True},
    9: {"id": 9, "name": "Mouse Pad", "description": "Large extended mouse pad", "price": 14.99, "in_stock": True},
    10: {"id": 10, "name": "External SSD", "description": "1TB portable SSD", "price": 119.99, "in_stock": True},
}

next_user_id = 11
next_product_id = 11
