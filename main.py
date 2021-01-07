from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup, ParseMode
import logging
import datetime
import os

from envs import TELEGRAM_BOT_TOKEN, DATABASE_PATH, DATE_FORMAT, TIME_FORMAT, PORT, STATE_ADD_ITEMS, WEBAPP
import keyboards
import readSQL
from users import users
import registration
import purchasing
import user_query
import admin
from utils import *

updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler("info.log"),
                        logging.StreamHandler()]
                    )
logger = logging.getLogger(__name__)

user_map = users()
user_lst = users(as_dict=False)


def initial(update, context):
    """All /start commands call this function.
    If user_id is known, continue to start;
    else, find out who it is."""
    user = update.message.from_user
    user_id = update.message.from_user.id
    logger.info(f"User {user.first_name} ({user_id}) started the conversation.")

    db = readSQL.Database(DATABASE_PATH)
    user_id_lst = db.get_user_id_lst()

    if user_id not in user_id_lst:
        _user_lst = [x.upper() for x in user_lst]
        users_kb = []
        names_per_row = 2
        for i in range(len(_user_lst) // names_per_row + (len(_user_lst) % names_per_row > 0)):
            users_kb.append([_user_lst[x] for x in range(i * names_per_row, min(len(_user_lst), names_per_row + i * names_per_row))])
        kb = keyboards.Keyboard(users_kb)
        reply_markup = InlineKeyboardMarkup(kb.setup())
        context.bot.send_message(chat_id=user_id,
                                 text="Hello, welcome to the world of Inventree!\n"
                                      "To finish setting things up, which of the following is your name?",
                                 reply_markup=reply_markup)

    else:
        registration.update_user(update, context)
        return start(update, context)


def register_user(update, context):
    registration.register_user(update, context)
    return _start(update, context)


def start(update, context):
    query = update.callback_query
    kb = keyboards.Keyboard(keyboards.start)
    reply_markup = InlineKeyboardMarkup(kb.setup())

    if update.message:
        user = update.message.from_user
        update.message.reply_text(f"Hello {user.first_name}, how I can help you today?", reply_markup=reply_markup)
    else:
        log_print(update, context)
        query.edit_message_text(text="Simi you still need me help you do?", reply_markup=reply_markup)


def _start(update, context):
    """Modified start function for new users,
    as message should be edited and not replied to with new message."""
    query = update.callback_query
    log_print(update, context)

    kb = keyboards.Keyboard(keyboards.start)
    reply_markup = InlineKeyboardMarkup(kb.setup())

    user = query.from_user
    query.edit_message_text(f"Hello {user.first_name}, how I can help you today?", reply_markup=reply_markup)


def user_queries(update, context):
    query = update.callback_query
    log_print(update, context)

    kb = keyboards.Keyboard(keyboards.user_query, add_quit_user_query_opt=True)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(text="Wah, what thing you wan check?", reply_markup=reply_markup)


def admin_options(update, context):
    query = update.callback_query
    user = query.from_user.first_name
    log_print(update, context)

    kb = keyboards.Keyboard(keyboards.admin_options, add_generic_back_home_opt=True)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    query.edit_message_text(text=f"Good day to you, {user}. What's up?", reply_markup=reply_markup)


def end_sess(update, context):
    query = update.callback_query
    log_print(update, context)
    query.edit_message_text(text="My pleasure to have helped you today, kam xia!", reply_markup=None)
    return ConversationHandler.END


def help(update, context):
    log_print(update, context)
    update.message.reply_text("Use /start to test this bot.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update}\ncaused error {context.error}')


def main():
    # Setup database
    try:
        readSQL.Database(DATABASE_PATH, setup=True)
    except:
        logger.fatal("DATABASE CONNECTION FAILED")

    # Initialise > Home Page
    dispatcher.add_handler(CommandHandler('start', initial))

    # Registration > Home Page
    dispatcher.add_handler(CallbackQueryHandler(register_user, pattern="|".join([x.upper() for x in user_lst])))

    # (Home Page) > Inventory
    dispatcher.add_handler(CallbackQueryHandler(purchasing.show_inventory, pattern=keyboards.start[0]))
    dispatcher.add_handler(CallbackQueryHandler(purchasing.show_inventory, pattern=keyboards.BACK_TO_INVENTORY_PROMPT))
    # Inventory > Quantity
    dispatcher.add_handler(CallbackQueryHandler(purchasing.select_qty, pattern='(^(~item)~[^~]*~[^~]*$)'))
    # Quantity > Check Purchase
    dispatcher.add_handler(CallbackQueryHandler(purchasing.buy_item, pattern='(^(~item)~[^~]*~[^~]*~[^~]*$)'))
    # Check Purchase > Confirm Purchase
    dispatcher.add_handler(CallbackQueryHandler(purchasing.confirm_buy, pattern='(^(~item)~[^~]*~[^~]*~[^~]*~[^~]*~Ya.*$)'))
    # Confirm Purchase > Inventory (Reselect)
    dispatcher.add_handler(CallbackQueryHandler(purchasing.show_inventory, pattern='(^(~item)~[^~]*~[^~]*~[^~]*~[^~]*~Sian.*$)'))
    # Confirm Purchase > Inventory (Purchase More)
    dispatcher.add_handler(CallbackQueryHandler(purchasing.show_inventory, pattern=keyboards.post_sale[0]))

    # Home Page > User Query Page
    dispatcher.add_handler(CallbackQueryHandler(user_queries, pattern=keyboards.start[1]))
    # User Query Page > Transactions
    dispatcher.add_handler(CallbackQueryHandler(user_query.show_transactions, pattern=keyboards.user_query[0]))
    # User Query Page > Debt
    dispatcher.add_handler(CallbackQueryHandler(user_query.show_summary, pattern=keyboards.user_query[1]))
    # User Query Page > Trivia
    dispatcher.add_handler(CallbackQueryHandler(user_query.show_trivia, pattern=keyboards.user_query[2]))

    # Home Page > Admin Page
    dispatcher.add_handler(CallbackQueryHandler(admin_options, pattern=keyboards.start[2]))
    dispatcher.add_handler(CallbackQueryHandler(admin_options, pattern=f".+{keyboards.BACK_TO_ADMIN_PAGE}$"))
    # Admin Page > Users Options
    dispatcher.add_handler(CallbackQueryHandler(admin.update_users, pattern=keyboards.admin_options[0]))
    # (Admin Page) > Inventory Options
    dispatcher.add_handler(CallbackQueryHandler(admin.update_inventory, pattern=keyboards.admin_options[1]))
    dispatcher.add_handler(CallbackQueryHandler(admin.update_inventory, pattern=f"^\[admin\]~item~< Back to Update Inventory Page$"))
    # Inventory Options > Show Inventory
    dispatcher.add_handler(CallbackQueryHandler(admin.show_inventory, pattern=keyboards.admin_inventory_update[0]))
    dispatcher.add_handler(CallbackQueryHandler(admin.show_inventory, pattern=f".*{keyboards.admin_edit_item[2]}$"))
    # Show Inventory > Edit Item Name or Delete
    dispatcher.add_handler(CallbackQueryHandler(admin.item_edit_or_delete, pattern="^\[admin\]~item~[^<~]*~[^<~]*$"))
    # Edit Item Name or Delete > Edit Item Name
    # Edit Item Name or Delete > Item Delete
    dispatcher.add_handler(CallbackQueryHandler(admin.delete_item, pattern=f"^\[admin\]~item~[^<~]*~[^<~]*~{keyboards.admin_edit_item[1]}$"))
    # Item Delete > Confirm Item Delete
    dispatcher.add_handler(CallbackQueryHandler(admin.delete_item_confirm, pattern=f"^\[admin\]~item~[^<~]*~[^<~]*~[^~]*~{keyboards.admin_cfm_delete[0]}$"))
    # Show Inventory > Edit Item Cost
    # Show Inventory > Edit Item Quantity
    # Inventory Options (or Confirm Inventory - Edit) > Add to Inventory
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin.add_items, pattern=keyboards.admin_inventory_update[1]),
                      CallbackQueryHandler(admin.add_items, pattern=f"^\[admin\]~cfm_add~{keyboards.admin_cfm_add[1]}$")], states={
            STATE_ADD_ITEMS: [MessageHandler(filters=Filters.text, callback=admin._add_items)]},
        fallbacks=[CommandHandler('cancel', ConversationHandler.END)]))
    dispatcher.add_handler(CallbackQueryHandler(admin.add_items, pattern=keyboards.admin_inventory_update[1]))
    dispatcher.add_handler(CallbackQueryHandler(admin.add_items, pattern=f"^\[admin\]~cfm_add~{keyboards.admin_cfm_add[1]}$"))
    # Add to Inventory > Confirm Inventory
    dispatcher.add_handler(CallbackQueryHandler(admin.add_item_confirm, pattern=f"^\[admin\]~cfm_add~{keyboards.admin_cfm_add[0]}$"))
    # Confirm Inventory > Inventory Options (Add to Inventory - Cancel)
    dispatcher.add_handler(CallbackQueryHandler(admin.update_inventory, pattern=f"^\[admin\]~cfm_add~{keyboards.admin_cfm_add[2]}$"))
    # Go Back To Home Page
    dispatcher.add_handler(CallbackQueryHandler(start, pattern=keyboards.post_sale[1]))
    dispatcher.add_handler(CallbackQueryHandler(start, pattern=keyboards.QUIT_BUY_PROMPT))
    dispatcher.add_handler(CallbackQueryHandler(start, pattern=keyboards.QUIT_USER_QUERY_PROMPT))
    dispatcher.add_handler(CallbackQueryHandler(start, pattern=keyboards.nothing_to_buy[0]))
    dispatcher.add_handler(CallbackQueryHandler(start, pattern=f"^.*{keyboards.BACK_TO_MAIN_PAGE}$"))

    # End Session
    dispatcher.add_handler(CallbackQueryHandler(end_sess, pattern=keyboards.start[3]))
    dispatcher.add_handler(CallbackQueryHandler(end_sess, pattern=keyboards.post_sale[2]))
    dispatcher.add_handler(CallbackQueryHandler(end_sess, pattern=keyboards.nothing_to_buy[1]))

    # Help Page
    dispatcher.add_handler(CommandHandler('help', help))

    # Error Handler
    dispatcher.add_error_handler(error)

    # Start the Bot
    # updater.start_polling()
    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TELEGRAM_BOT_TOKEN)
    updater.bot.set_webhook(WEBAPP + TELEGRAM_BOT_TOKEN)

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
