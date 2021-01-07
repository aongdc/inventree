from telegram import InlineKeyboardMarkup, ParseMode
from telegram.ext import MessageHandler, DispatcherHandlerStop
import re

from utils import log_print
from envs import DATABASE_PATH, STATE_ADD_ITEMS
from purchasing import show_inventory as inventory, get_inventory
import keyboards
import readSQL

def update_inventory(updater, context):
    query = updater.callback_query

    kb = keyboards.Keyboard(keyboards.admin_inventory_update, add_back_to_admin_opt=True,
                            add_generic_back_home_opt=True)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(text="Do you wanna update items in the current inventory, or add (a) new item(s)?",
                            reply_markup=reply_markup,
                            parse_mode=ParseMode.MARKDOWN)

def show_inventory(updater, context, as_new_message=False):
    # query = updater.callback_query
    # log_print(updater, context)
    return inventory(updater, context, as_new_message, admin=True, show_all=True)

def item_edit_or_delete(updater, context):
    query = updater.callback_query
    log_print(updater, context)

    item_name = query.data.split("[admin]~item~")[1].split("~")[0]
    kb = keyboards.Keyboard(keyboards.admin_edit_item, callback_info=query.data)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(text=f"What do you wanna do with item: *{item_name}*?",
                            reply_markup=reply_markup,
                            parse_mode=ParseMode.MARKDOWN)

def delete_item(updater, context):
    query = updater.callback_query
    log_print(updater, context)
    item_name = query.data.split("[admin]~item~")[1].split("~")[0]
    kb = keyboards.Keyboard(keyboards.admin_cfm_delete, callback_info=query.data)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(text=f"Confirm delete item: *{item_name}*?",
                            reply_markup=reply_markup,
                            parse_mode=ParseMode.MARKDOWN)

def delete_item_confirm(updater, context):
    query = updater.callback_query
    log_print(updater, context)

    item_name = query.data.split("[admin]~item~")[1].split("~")[0]
    readSQL.Database(DATABASE_PATH).delete_item(item_name)
    query.edit_message_text(text=f"Deleted from inventory: *{item_name}*",
                            reply_markup=None,
                            parse_mode=ParseMode.MARKDOWN)
    return show_inventory(updater, context, as_new_message=True)

def add_items(updater, context):
    query = updater.callback_query
    user_id = query.from_user.id
    log_print(updater, context)

    current_inventory = get_inventory(as_dict=True)
    if current_inventory is None or current_inventory == [None]:
        inventory_text = "The inventory is currently empty."
    else:
        inventory_text = "*Current Inventory*"
        for item, details in current_inventory.items():
            inventory_text += f"\n{details['quantity']}x {item} @ ${details['cost']:.2f}"
    query.edit_message_text(text=inventory_text,
                            reply_markup=None,
                            parse_mode=ParseMode.MARKDOWN)
    context.bot.send_message(chat_id=user_id,
                             text="Send me a message with the details of the item(s) you wanna add in the following format:"
                                  "\n<quantity>x <item> @ <cost per unit>"
                                  "\neg. 5x apple @ $0.50")
    return STATE_ADD_ITEMS

def _add_items(updater, context):
    user_id = updater.message.from_user.id
    to_add = updater.message.text
    add_text = "*Confirm to add/update the following items?*"

    try:
        lines = to_add.split("\n")
        for line in lines:
            to_add = re.match('(^\d+) ?x?[\t ]+(.+)[\t ]+@?[\t ]*\$?((?:0*\.)?\d+|\d+\.\d*)\s*$', line)
            if not to_add:
                raise Exception("Invalid format!")

            qty, item, cost = to_add.groups()
            qty = int(qty)
            item = item.lower().strip('@').strip()
            cost = round(float(cost), 2)

            context.user_data['items_to_add'].append([{'qty': qty, 'item': item, 'cost': cost}])
            add_text += f'\n{qty}x {item.capitalize()} @ ${cost:.2f} ea'

        kb = keyboards.Keyboard(keyboards.admin_cfm_add, callback_info="[admin]~cfm_add")
        reply_markup = InlineKeyboardMarkup(kb.setup())
        context.bot.send_message(chat_id=user_id,
                                 text=add_text,
                                 reply_markup=reply_markup,
                                 parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        print(e)
        return

    return

def add_item_confirm(updater, context):
    query = updater.callback_query
    to_add = context.user_data['items_to_add']
    current_items = [x.lower() for x in get_inventory(as_dict=True).keys()]
    added = "*Added into inventory:*"

    for item_details in to_add:
        qty, item, cost = item_details['qty'], item_details['item'], item_details['cost']
        if item in current_items:
            readSQL.Database(DATABASE_PATH).update_inventory(item, qty, cost)
        else:
            readSQL.Database(DATABASE_PATH).add_item(item, cost, qty)

        added += f'\n{qty}x {item.capitalize()} @ ${cost:.2f} ea'

    query.edit_message_text(text=added,
                            reply_markup=None,
                            parse_mode=ParseMode.MARKDOWN)

    return show_inventory(updater, context, as_new_message=True)

def update_users(updater, context):
    pass