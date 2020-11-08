import inspect
import random
import sqlite3


class TellerMachine:
    def __init__(self):
        self.card_number = ''
        self.account_number = ''
        self.pin = ''
        self.balance = 0

    def generator(self, gen_type):
        random.seed()
        if gen_type == 'card_number':
            for i in range(9):
                self.account_number += str(random.randint(0, 9))
            self.card_number = '400000' + self.account_number
            self.card_number += str(self.checksum(self.card_number))
            return self.card_number
        elif gen_type == 'pin':
            for i in range(4):
                self.pin += str(random.randrange(9))
            return self.pin

    def checksum(self, card_number):
        temp_list = []
        for i in card_number:
            temp_list.append(int(i))
        for i in range(len(temp_list)):
            if i % 2 == 0:
                temp_list[i] *= 2
                if temp_list[i] > 9:
                    temp_list[i] -= 9
        remainder = sum(temp_list) % 10
        return 10 - remainder if remainder != 0 else 0

        """
        # OLD VARIANT
        temp_number = ''
        temp_sum = 0
        temp_index = 1
        for i in self.card_number:
            if temp_index % 2 != 0:
                temp = int(i) * 2
                if temp > 9:
                    temp -= 9
                temp_number += str(temp)
            else:
                temp_number += i
            temp_index += 1
        for i in temp_number:
            temp_sum += int(i)
        remainder = temp_sum % 10
        if remainder != 0:
            return str(10 - remainder)
        else:
            return 0
        """

    @staticmethod
    def db_init():
        conn = sqlite3.connect('card.s3db')
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS card (
                           id INTEGER,
                           number TEXT,
                           pin TEXT,
                           balance INTEGER DEFAULT 0
                       );''')
        conn.commit()
        conn.close()
        return True

    def db_update(self, resource, card_number, balance):
        conn = sqlite3.connect('card.s3db')
        cur = conn.cursor()
        if resource == 'new_account':
            cur.execute('INSERT INTO card (number, pin) VALUES (?, ?)',
                        (card_number, self.pin))
        elif resource == 'change_balance':
            cur.execute('UPDATE card SET balance = (?) WHERE number = (?)',
                        (balance, card_number))
        elif resource == 'close_account':
            cur.execute('DELETE FROM card WHERE number = (?)',
                        [card_number])
        conn.commit()
        conn.close()
        return True

    def db_select(self, resource, recipient):
        conn = sqlite3.connect('card.s3db')
        conn.row_factory = lambda cursor, row: row[0]
        cur = conn.cursor()
        if resource == 'pin':
            cur.execute('SELECT pin from card WHERE number = (?)', (self.card_number,))
        elif resource == 'balance':
            cur.execute('SELECT balance from card WHERE number = (?)', (self.card_number,))
        elif resource == 'card_exists':
            cur.execute('SELECT number from card WHERE number = (?)', (recipient,))
        elif resource == 'recipient_balance':
            cur.execute('SELECT balance from card WHERE number = (?)', (recipient,))
        select = cur.fetchone()
        conn.close()
        return select

    def main_menu(self):
        self.db_init()
        self.card_number = ''
        self.account_number = ''
        self.pin = ''
        self.balance = 0
        reply = input("1. Create an account\n2. Log into account\n0. Exit\n")
        if reply == "1":
            self.generator('card_number')
            self.generator('pin')
            ready_info = """
                         Your card has been created
                         Your card number:
                         {card_number}
                         Your card PIN:
                         {pin}""" \
                .format(card_number=self.card_number, pin=self.pin)
            print(inspect.cleandoc(ready_info))
            self.db_update('new_account', self.card_number, 0)
        elif reply == "2":
            self.card_number = input("Enter your card number:\n")
            self.pin = input("Enter your PIN:\n")
            if len(self.card_number) == 16 and len(self.pin) == 4:
                if self.db_select('pin', '') == self.pin:
                    print("You have successfully logged in!")
                    self.logged_in()
                else:
                    print("Wrong card number or PIN!")
            else:
                print("Wrong card number or PIN!")
        elif reply == "0":
            exit(0)

    def logged_in(self):
        while True:
            account_menu = input("1. Balance\n2. Add income\n3. Do transfer\n"
                                 "4. Close account\n5. Log out\n0. Exit\n")
            if account_menu == "1":
                self.balance = self.db_select('balance', '')
                print("Balance: {}".format(self.balance))
                continue
            elif account_menu == "2":
                self.balance += int(input("Enter income:\n"))
                self.db_update('change_balance', self.card_number, self.balance)
                print("Income was added!")
                continue
            elif account_menu == "3":
                recipient = input("Transfer\nEnter card number:\n")
                if recipient == self.account_number:
                    print("You can't transfer money to the same account!")
                elif str(self.checksum(recipient[:-1])) != recipient[-1]:
                    print("Probably you made a mistake in the card number. Please try again!")
                    continue
                elif not self.db_select('card_exists', recipient):
                    print("Such a card does not exist.")
                    continue
                transfer_sum = int(input("Enter how much money you want to transfer:\n"))
                if transfer_sum > self.balance:
                    print("Not enough money!")
                else:
                    self.balance -= transfer_sum
                    self.db_update('change_balance', self.card_number, self.balance)
                    transfer_sum += self.db_select('recipient_balance', recipient)
                    self.db_update('change_balance', recipient, transfer_sum)
                    print("Success!")
                continue
            elif account_menu == "4":
                self.db_update('close_account', self.card_number, 0)
                self.main_menu()
                print("The account has been closed!")
                continue
            elif account_menu == "5":
                self.main_menu()
                print("You have successfully logged out!")
            elif account_menu == "0":
                exit(0)


machine = TellerMachine()
while True:
    machine.main_menu()
