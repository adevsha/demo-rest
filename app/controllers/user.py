from app.data import store
from app.models.user import UserCreate, UserUpdate


def list_users() -> list[dict]:
    return list(store.users.values())


def get_user(user_id: int) -> dict | None:
    return store.users.get(user_id)


def create_user(data: UserCreate) -> dict:
    user = {"id": store.next_user_id, **data.model_dump()}
    store.users[store.next_user_id] = user
    store.next_user_id += 1
    return user


def update_user(user_id: int, data: UserUpdate) -> dict | None:
    if user_id not in store.users:
        return None
    updates = data.model_dump(exclude_unset=True)
    store.users[user_id].update(updates)
    return store.users[user_id]


def delete_user(user_id: int) -> bool:
    return store.users.pop(user_id, None) is not None
