import readSQL
from envs import DATABASE_PATH

def register_user(update, context):
    """If user_id has not been registered, write to database.
    Then, continue to _start."""
    query = update.callback_query
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    user_name = query.from_user.username
    name = query.data.lower()
    db = readSQL.Database(DATABASE_PATH)
    db.add_user(name, user_id, first_name, user_name)


def update_user(update, context):
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    user_name = update.message.from_user.username
    db = readSQL.Database(DATABASE_PATH)
    db.update_user(user_id, first_name, user_name)