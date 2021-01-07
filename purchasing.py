from telegram import InlineKeyboardMarkup, ParseMode
import datetime

from utils import log_print, localize_dt
import readSQL
from envs import DATABASE_PATH, DATE_FORMAT, TIME_FORMAT
import keyboards


def get_inventory(as_dict=False, as_item_list=False, show_all=False):
    inventory = readSQL.Database(DATABASE_PATH).fetch_inventory()
    if inventory is None:
        return dict() if as_dict else [None]
    inventory_dict, columns = inventory
    if as_dict:
        return {k.capitalize(): v for k, v in inventory_dict.items()}
    inventory_list = []
    if as_item_list:
        for item in inventory_dict.keys():
            inventory_list.append(item.capitalize())
    else:
        inventory_list = [[column.upper() for column in columns]]
        for i, (item, details) in enumerate(inventory_dict.items()):
            item, cost, qty = item.capitalize(), f"${float(details[columns[1]]):.2f}", details[columns[2]]
            if qty <= 0 and not show_all:
                continue
            inventory_list.append([item, cost, qty])
    return inventory_list


def show_inventory(update, context, as_new_message=False, admin=False, show_all=False):
    query = update.message if update.message else update.callback_query
    log_print(update, context)
    user_id = update.message.from_user.id if update.message else query.from_user.id
    inventory_list = get_inventory(show_all=show_all)
    if inventory_list == [None]:
        kb = keyboards.Keyboard(keyboards.nothing_to_buy if not admin else keyboards.admin_inventory_empty)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        reply_text = "_Wah suay eh... Nothing left to buy liao..._" if not admin else "The inventory is currently empty."
        query.edit_message_text(text=reply_text,
                                reply_markup=reply_markup,
                                parse_mode=ParseMode.MARKDOWN)
    else:
        if admin:
            inventory_list += ["< Back to Update Inventory Page", "<< Back to Main Page"]
            kb = keyboards.Keyboard(inventory_list, callback_to_row_header=True, callback_info="[admin]~item")
        else:
            kb = keyboards.Keyboard(inventory_list, add_quit_buy_opt=True, callback_to_row_header=True, callback_info="~item")
        reply_markup = InlineKeyboardMarkup(kb.setup())
        reply_text = "You wan simi?" if not admin else "Tap on the item, cost, or quantity, respectively to edit them."

        if as_new_message:
            context.bot.send_message(chat_id=user_id, text=f"Here is the updated inventory. Tap on the item, cost, or quantity, respectively to edit them.",
                                     reply_markup=reply_markup)
        else:
            query.edit_message_text(text=reply_text, reply_markup=reply_markup)


def select_qty(update, context):
    query = update.callback_query
    log_print(update, context)

    item = query.data.split("~item~", 1)[1].split("~")[0]
    inventory_dict = get_inventory(as_dict=True)
    try:
        max_qty = min(inventory_dict[item]['quantity'], 10)
    except:
        return

    opts_per_row = 2
    kb_setup = []
    for i in range(max_qty // opts_per_row + (max_qty % opts_per_row > 0)):
        kb_setup.append([x for x in range(1 + i * opts_per_row, min(max_qty, opts_per_row + i * opts_per_row) + 1)])
    kb = keyboards.Keyboard(kb_setup, callback_info=query.data, add_quit_buy_opt=True, add_back_to_inventory_opt=True)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(text=f"{item} x how many?", reply_markup=reply_markup)


def buy_item(update, context):
    query = update.callback_query
    log_print(update, context)

    item, qty = query.data.split("~item~", 1)[1].split("~")[0], query.data.split("~item~", 1)[1].split("~")[-1]
    qty = int(qty)

    inventory_dict = get_inventory(as_dict=True)
    cost, stock = inventory_dict[item]['cost'], inventory_dict[item]['quantity']

    if qty > stock:
        if stock <= 0:
            inventory_list = get_inventory()
            kb = keyboards.Keyboard(inventory_list, add_quit_buy_opt=True)
            reply_markup = InlineKeyboardMarkup(kb.setup())
            query.edit_message_text(text=f"Sorri leh, don't have {qty}x {item} liao... "
                                         f"Bobian you have to choose other thing~~",
                                    reply_markup=reply_markup)
        else:
            max_qty = max(stock, 10)
            opts_per_row = 2
            kb_setup = []
            for i in range(max_qty // opts_per_row + (max_qty % opts_per_row > 0)):
                kb_setup.append(
                    [x for x in range(1 + i * opts_per_row, min(max_qty, opts_per_row + i * opts_per_row) + 1)])
            kb = keyboards.Keyboard(kb_setup, callback_info=item, add_quit_buy_opt=True, add_back_to_inventory_opt=True)
            reply_markup = InlineKeyboardMarkup(kb.setup())
            query.edit_message_text(text=f"Wah sad, only have {stock}x {item} left sia... "
                                         f"Can only choose lower quantity, bobian arh~~",
                                    reply_markup=reply_markup)
    else:
        total_payable = qty * cost
        kb = keyboards.Keyboard(keyboards.cfm_buy, callback_info=f'{query.data}~{total_payable}',
                                add_back_to_inventory_opt=True, add_quit_buy_opt=True)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        query.edit_message_text(text=f"Ok, confirm plus chop {qty}x {item} ah? "
                                     f"Total need pay ${total_payable:.2f} hor!",
                                reply_markup=reply_markup)


def confirm_buy(update, context):
    query = update.callback_query
    log_print(update, context)
    user_id = query.from_user.id

    item, _, qty, payable, _ = query.data.split('~item~', 1)[1].split("~")
    qty = int(qty)
    payable = float(payable.strip('$'))
    dt = localize_dt(datetime.datetime.now()).strftime(f'{DATE_FORMAT} {TIME_FORMAT}')
    update_database(dt, user_id, item, qty, payable, 'open')

    query.edit_message_text(text=f"*Transaction Details*\n"
                                 f"*{dt}*\n\n"
                                 f"{qty}x {item} @ ${payable/qty:.2f} each\n"
                                 f"Total: ${payable:.2f}\n",
                            reply_markup=None,
                            parse_mode=ParseMode.MARKDOWN)

    kb = keyboards.Keyboard(keyboards.post_sale)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    context.bot.send_message(chat_id=user_id, text=f"Still got anything you need bo?", reply_markup=reply_markup)


def update_database(dt, uid, item, qty, amount, payment_type):
    readSQL.Database(DATABASE_PATH).update_inventory(item, qty)
    readSQL.Database(DATABASE_PATH).update_log(dt, uid, item, qty, amount)
    readSQL.Database(DATABASE_PATH).update_payment(dt, uid, amount, payment_type)