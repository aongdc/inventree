from telegram import InlineKeyboardMarkup, ParseMode

from utils import log_print, convert_dt
from envs import DATABASE_PATH
import readSQL
import keyboards

def show_transactions(update, context):
    query = update.callback_query
    log_print(update, context)
    user_id = query.from_user.id

    name, transactions = readSQL.Database(DATABASE_PATH).user_transactions(user_id, num_to_show=5)
    out_text = f"*Transaction History for {name.capitalize()} (Latest 5)*"
    if len(transactions) == 0:
        out_text += "\n_~Wah, so empty, buy some stuff leh~_"
    else:
        for i, transaction in enumerate(transactions):
            dt, item, quantity, amount = transaction
            out_text += f"\n\n*{i + 1}. {convert_dt(dt)}*\n" \
                        f"{quantity}x {item}\n" \
                        f"Total: ${float(amount):.2f}"
    query.edit_message_text(text=out_text, reply_markup=None, parse_mode=ParseMode.MARKDOWN)

    kb = keyboards.Keyboard(keyboards.user_query, add_quit_user_query_opt=True)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    context.bot.send_message(chat_id=user_id, text=f"Anything else you wan check?", reply_markup=reply_markup)


def show_summary(update, context):
    query = update.callback_query
    log_print(update, context)
    user_id = query.from_user.id
    user_name = query.from_user.first_name

    name, latest_repayment, repayment_amt, latest_open, open_amt = readSQL.Database(DATABASE_PATH).user_summary(user_id)
    if latest_repayment is None:
        latest_repayment_text = "\n_You have never paid your debts..._"
    else:
        latest_repayment_text = f"\n\nLatest repayment was on {convert_dt(latest_repayment)} for *${float(repayment_amt):.2f}*"

    if latest_open is None:
        latest_open_text = "\n_You have never purchased anything... what a feat..._"
    else:
        latest_open_text = f"\nAfter your last purchase ({convert_dt(latest_open)}), you owe a total of *${float(open_amt):.2f}*."

    out_text = f"*Payment Summary for {user_name}*" + latest_repayment_text + latest_open_text
    query.edit_message_text(text=out_text, reply_markup=None, parse_mode=ParseMode.MARKDOWN)

    kb = keyboards.Keyboard(keyboards.user_query, add_quit_user_query_opt=True)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    context.bot.send_message(chat_id=user_id, text=f"Anything else you wan check?", reply_markup=reply_markup)


def show_trivia(update, context):
    query = update.callback_query
    log_print(update, context)
    user_id = query.from_user.id
    user_name = query.from_user.first_name

    trivia = readSQL.Database(DATABASE_PATH).user_trivia(user_id)
    query.edit_message_text(
        text=f"{user_name}, throughout your entire life with me, you have spent *${float(trivia):.2f}*!!!",
        reply_markup=None, parse_mode=ParseMode.MARKDOWN)

    kb = keyboards.Keyboard(keyboards.user_query, add_quit_user_query_opt=True)
    reply_markup = InlineKeyboardMarkup(kb.setup())
    context.bot.send_message(chat_id=user_id, text=f"Anything else you wan check?", reply_markup=reply_markup)