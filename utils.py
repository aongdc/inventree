import datetime
import logging
from envs import DATE_FORMAT, TIME_FORMAT

def log_print(update, context):
    query = update.message if update.message else update.callback_query
    user_id = update.message.from_user.id if update.message else query.from_user.id
    name = update.message.from_user.first_name if update.message else query.from_user.first_name
    logging.getLogger('__main__').info(f"{name} ({user_id}): {query.text if update.message else query.data}")


def _remove_inline(update, context):
    """Removes inline reply markup of previous message."""
    query = update.callback_query
    query.edit_message_reply_markup(reply_markup=None)


def convert_dt(dt):
    if type(dt) is str:
        return datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').strftime(f'{DATE_FORMAT} {TIME_FORMAT}')
    else:
        return dt.strftime(f'{DATE_FORMAT} {TIME_FORMAT}')


def localize_dt(dt):
    return dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=datetime.timezone(datetime.timedelta(hours=8)))