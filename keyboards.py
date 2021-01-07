from telegram import InlineKeyboardButton, KeyboardButton

QUIT_BUY_PROMPT = "Nvm, actulli I dun wan buy liao"
BACK_TO_INVENTORY_PROMPT = "Sian, I fat finger press wrong thing"
QUIT_USER_QUERY_PROMPT = "Nvm, dun wan see stats liao"
BACK_TO_MAIN_PAGE = "<< Back to Main Page"
BACK_TO_ADMIN_PAGE = "< Back to Admin Page"

start = "Wanna buy dis itemz!", "Money flow where oredi?", "I am ruler the admin.", "Buh-bye!"
nothing_to_buy = "Aiyoh, go back home page lor...", "Harh... liddat no choice lor, bye!"
cfm_buy = "Yarlarh, double cfm plus chop",
post_sale = "I still wan buy thing", "Go back homepage pls", "Nothing liao, zao first, thx"
user_query = "So far I spend on what harh?", "How much money I owe leh?", "Trivia"
admin_options = "(View/Edit User Records)", "Update Inventory"
admin_inventory_update = "Edit Existing", "Add Items"
admin_inventory_empty = BACK_TO_ADMIN_PAGE, BACK_TO_MAIN_PAGE
admin_edit_item = "(Edit Item Name)", "Delete Item", "< Back to Inventory List"
admin_cfm_delete = "Confirm Delete", "< Back to Inventory List"
admin_cfm_add = "Confirm Inventory Update", "Edit", "< Cancel"

end = "/Start Attdbot",


class Keyboard:
    def __init__(self,
                 options,
                 inline=True,
                 callback_to_row_header=False,
                 callback_info=None,
                 add_quit_buy_opt=False,
                 add_back_to_inventory_opt=False,
                 add_quit_user_query_opt=False,
                 add_generic_back_home_opt=False,
                 add_back_to_admin_opt=False,
                 add_back=False):
        self.options = options
        self.inline = inline
        self.callback_to_row_header = callback_to_row_header
        self.callback_info = callback_info
        self.add_quit_buy_opt = add_quit_buy_opt
        self.add_back_to_inventory_opt = add_back_to_inventory_opt
        self.add_quit_user_query_opt = add_quit_user_query_opt
        self.add_generic_back_home_opt = add_generic_back_home_opt
        self.add_back_to_admin_opt = add_back_to_admin_opt
        self.add_back = add_back
        self.keyboard = []
        self.fn = InlineKeyboardButton if self.inline else KeyboardButton

    def setup(self):
        i = 0
        while i < len(self.options):
            callback_data = f"{self.callback_info}~" if self.callback_info else ""

            if type(self.options[i]) is list:
                _keyboard = []

                if self.callback_to_row_header:
                    header, *_ = self.options[i]
                    callback_data += f'{header}~'

                for elem in self.options[i]:
                    _callback_data = f'{callback_data}{elem}'
                    _keyboard.append(self.fn(f"{elem}", callback_data=_callback_data))
                self.keyboard.append(_keyboard)

            else:
                callback_data += f'{self.options[i]}'
                self.keyboard.append([self.fn(f"{self.options[i]}", callback_data=f'{callback_data}')])

            i += 1

        if self.add_back_to_inventory_opt:
            self.keyboard.append([self.fn(BACK_TO_INVENTORY_PROMPT, callback_data=BACK_TO_INVENTORY_PROMPT)])
        if self.add_quit_buy_opt:
            self.keyboard.append([self.fn(QUIT_BUY_PROMPT, callback_data=QUIT_BUY_PROMPT)])
        if self.add_quit_user_query_opt:
            self.keyboard.append([self.fn(QUIT_USER_QUERY_PROMPT, callback_data=QUIT_USER_QUERY_PROMPT)])
        if self.add_back_to_admin_opt:
            self.keyboard.append([self.fn(BACK_TO_ADMIN_PAGE, callback_data=BACK_TO_ADMIN_PAGE)])
        if self.add_generic_back_home_opt:
            self.keyboard.append([self.fn(BACK_TO_MAIN_PAGE, callback_data=BACK_TO_MAIN_PAGE)])

        return self.keyboard


"""
TODO:
2. admin edit inventory
> add using list table
> edit by clicking
>> edit item name or delete item
>> edit cost
>> edit qty
> view user info
>> click user more details
>>> last purchase info, repayment, owe
>>> cancel last purchase
>>> repay
3. fix user names page
> allow multiaccts per user
4. auth?
"""