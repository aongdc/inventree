import psycopg2
from envs import DATE_FORMAT, TIME_FORMAT, DATABASE_PATH
import datetime


class Database:
    def __init__(self, db_path, setup=False):
        self.db_path = db_path
        if setup:
            self.setup()

    def create_connection(self):
        """
        create a database connection to the SQLite database specified by the db_file
        :param db_file: database file
        :return: Connection object or None
        """
        self.conn = None
        try:
            self.conn = psycopg2.connect(self.db_path, sslmode='require')
            # self.conn = psycopg2.connect(host='localhost', database='inventree', user='postgres', password='aodc123456mts')
        except Exception as e:
            print(e)
        return self.conn

    def setup(self):
        self.cur = self.create_connection().cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS users ("
                         "user_id INTEGER NOT NULL, "
                         "name TEXT NOT NULL, "
                         "first_name TEXT, "
                         "user_name TEXT, "
                         "CONSTRAINT user_id PRIMARY KEY (user_id))")
        self.cur.execute("CREATE TABLE IF NOT EXISTS log ("
                         "datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL, "
                         "user_id INTEGER NOT NULL, "
                         "name TEXT, "
                         "item TEXT NOT NULL, "
                         "quantity INTEGER NOT NULL, "
                         "amount NUMERIC NOT NULL, "
                         "CONSTRAINT user_id FOREIGN KEY (user_id) "
                         "REFERENCES users (user_id) MATCH SIMPLE "
                         "ON UPDATE NO ACTION "
                         "ON DELETE NO ACTION "
                         "NOT VALID)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS payment ("
                         "datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL, "
                         "user_id INTEGER NOT NULL, "
                         "amount NUMERIC NOT NULL, "
                         "type TEXT NOT NULL, "
                         "CONSTRAINT user_id FOREIGN KEY (user_id) "
                         "REFERENCES users (user_id) MATCH SIMPLE "
                         "ON UPDATE NO ACTION "
                         "ON DELETE NO ACTION "
                         "NOT VALID)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS inventory ("
                         "item TEXT NOT NULL, "
                         "cost NUMERIC NOT NULL, "
                         "quantity INTEGER NOT NULL, "
                         "PRIMARY KEY (item))")
        # self.cur.execute("DELETE FROM inventory")
        # self.cur.execute("INSERT INTO inventory (item, cost, quantity) VALUES ('apple', 4, 13)")
        # self.cur.execute("INSERT INTO inventory (item, cost, quantity) VALUES ('orange', 7, 21)")
        # self.cur.execute("INSERT INTO inventory (item, cost, quantity) VALUES ('banana', 10, 8)")
        # self.cur.execute("INSERT INTO inventory (item, cost, quantity) VALUES ('peach', 15, 3)")
        self.conn.commit()

    def get_users_table(self):
        self.cur = self.create_connection().cursor()
        self.cur.execute("SELECT * FROM users")
        return self.cur

    def get_payment_table(self):
        self.cur = self.create_connection().cursor()
        self.cur.execute("SELECT * FROM payment")
        return self.cur

    def get_user_id_lst(self):
        self.user_id_lst = [x[0] for x in self.get_users_table().fetchall()]
        return self.user_id_lst

    def get_user_id_map(self):
        self.user_id_map = dict()
        tuple_map = [x[0:2] for x in self.get_users_table().fetchall()]
        for id, name in tuple_map:
            self.user_id_map[id] = name
        return self.user_id_map

    def get_inventory_table(self):
        self.cur = self.create_connection().cursor()
        self.cur.execute("SELECT * FROM inventory ORDER BY item ASC")
        return self.cur

    def get_log_table(self):
        self.cur = self.create_connection().cursor()
        self.cur.execute("SELECT * FROM log")
        return self.cur

    def add_user(self, name, user_id, first_name, user_name):
        self.conn = self.create_connection()
        self.cur = self.conn.cursor().execute(f"INSERT INTO users (name, user_id, first_name, user_name)"
                                              f"VALUES ('{name}', '{user_id}', '{first_name}', '{user_name}')")
        self.conn.commit()
        return self.cur

    def update_user(self, user_id, first_name, user_name):
        self.conn = self.create_connection()
        self.cur = self.conn.cursor().execute(f"UPDATE users "
                                              f"SET first_name = '{first_name}',"
                                              f"user_name = '{user_name}' "
                                              f"WHERE user_id = {user_id}")
        self.conn.commit()
        return self.cur

    def fetch_inventory(self):
        inventory = self.get_inventory_table().fetchall()
        if len(inventory) == 0:
            return None
        columns = list(map(lambda x: x[0], self.cur.description))
        inventory_dict = dict()
        for listing in inventory:
            inventory_dict[listing[0]] = {columns[1]: listing[1], columns[2]: listing[2]}
        return inventory_dict, columns

    def update_inventory(self, item, qty, cost=None):
        self.cur = self.get_inventory_table()
        self.cur.execute(f"UPDATE inventory "
                         f"SET quantity = ((SELECT quantity FROM inventory WHERE item = '{item.lower()}') - {qty}) "
                         f"WHERE item = '{item.lower()}'")
        if cost:
            self.cur.execute(f"UPDATE inventory "
                             f"SET cost = {cost} "
                             f"WHERE item = '{item.lower()}'")
        self.conn.commit()

    def update_log(self, dt, user_id, item, qty, amount):
        self.cur = self.get_log_table()
        name = self.get_user_id_map()[user_id]
        self.cur.execute(f"INSERT INTO log (datetime, user_id, name, item, quantity, amount) "
                         f"VALUES ('{self.convert_dt(dt)}', {user_id}, '{name}', '{item.lower()}', {qty}, {amount})")
        self.conn.commit()

    def update_payment(self, dt, user_id, amount, payment_type):
        self.cur = self.get_payment_table()
        self.cur.execute("SELECT user_id FROM payment WHERE type = 'open'")
        is_new_user = user_id not in [x for y in self.cur.fetchall() for x in y]

        if payment_type == 'repayment' or is_new_user:
            self.cur.execute(f"INSERT INTO payment (datetime, user_id, amount, type) "
                             f"VALUES ('{self.convert_dt(dt)}', {user_id}, {amount}, '{payment_type}')")

        if not is_new_user:
            operation = '+' if payment_type == 'open' else '-'
            self.cur.execute(f"UPDATE payment "
                             f"SET amount = "
                             f"((SELECT amount FROM payment WHERE type = 'open' AND user_id = {user_id}) {operation} {amount}),"
                             f"datetime = '{self.convert_dt(dt)}' "
                             f"WHERE type = 'open' AND user_id = {user_id}")

        self.conn.commit()

    def user_summary(self, user_id):
        self.cur = self.get_payment_table()
        name = self.get_user_id_map()[user_id]
        self.cur.execute(f"SELECT datetime, amount FROM payment "
                         f"WHERE type = 'repayment' AND user_id = {user_id} "
                         f"ORDER BY datetime DESC LIMIT 1")
        latest_repayment = self.cur.fetchone()
        if latest_repayment is not None:
            latest_repayment_date, repayment_amt = latest_repayment
        else:
            latest_repayment_date, repayment_amt = None, 0

        self.cur.execute(f"SELECT datetime, amount FROM payment "
                        f"WHERE type = 'open' AND user_id = {user_id} "
                        f"ORDER BY datetime DESC LIMIT 1")
        latest_open = self.cur.fetchone()
        if latest_open is not None:
            latest_open_date, open_amt = latest_open
        else:
            latest_open_date, open_amt = None, 0

        return name, latest_repayment_date, repayment_amt, latest_open_date, open_amt

    def user_transactions(self, user_id, num_to_show=5):
        self.cur = self.get_log_table()
        name = self.get_user_id_map()[user_id]
        self.cur.execute(f"SELECT datetime, item, quantity, amount FROM log "
                         f"WHERE user_id = {user_id} "
                         f"ORDER BY datetime DESC LIMIT {num_to_show}")
        transactions = self.cur.fetchall()
        return name, transactions

    def user_trivia(self, user_id):
        self.cur = self.get_log_table()
        self.cur.execute(f"SELECT amount FROM log "
                         f"WHERE user_id = {user_id} ")
        amounts = self.cur.fetchall()
        trivia = sum([x for y in amounts for x in y])
        return trivia

    def delete_item(self, item):
        self.cur = self.get_inventory_table()
        self.cur.execute(f"DELETE FROM inventory WHERE item='{item.lower()}'")
        self.conn.commit()

    def add_item(self, item, cost, qty):
        self.cur = self.get_inventory_table()
        self.cur.execute(f"INSERT INTO inventory (item, cost, quantity) VALUES ('{item}', {cost}, {qty})")
        self.conn.commit()

    def convert_dt(self, dt):
        return datetime.datetime.strptime(dt, f'{DATE_FORMAT} {TIME_FORMAT}').strftime('%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    Database(DATABASE_PATH, setup=True)