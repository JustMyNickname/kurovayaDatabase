# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext, filedialog
from typing import List, Optional
import re
from datetime import datetime
import csv
import pandas as pd
import peewee
from werkzeug.security import generate_password_hash, check_password_hash

from models import (
    Organization_Data, Personal_Data, Client, Employee, Deposit, Loan,
    Card, Bank_Account, Transaction, Users, db
)

class AddEditDialog(simpledialog.Dialog):
    def __init__(self, parent, title, fields: List[str], initial_data: Optional[dict] = None, user_status: str = 'admin'):
        self.fields = fields
        self.initial_data = initial_data
        self.user_status = user_status
        super().__init__(parent, title)

    def body(self, master):
        self.entries = {}
        for idx, field in enumerate(self.fields):
            label_text = field.replace('_', ' ').capitalize() + ":"
            if field == 'password':
                label_text = "Пароль:"
            tk.Label(master, text=label_text).grid(row=idx, column=0, padx=5, pady=5, sticky='e')
            if field == 'password':
                entry = tk.Entry(master, show="*")
            else:
                entry = tk.Entry(master)
            entry.grid(row=idx, column=1, padx=5, pady=5, sticky='w')
            if self.initial_data and field in self.initial_data and self.initial_data[field] is not None:
                if field == 'password':
                    # Do not pre-fill password fields
                    entry.insert(0, "")
                else:
                    entry.insert(0, str(self.initial_data[field]))
            self.entries[field] = entry

        if 'password' in self.fields:
            self.hash_copy_button = tk.Button(master, text="Хешировать Пароль", command=self.hash_password)
            self.hash_copy_button.grid(row=len(self.fields), column=1, padx=5, pady=5, sticky='w')

        # Disable 'client_type' field if user is an employee
        if self.user_status == 'employee' and 'client_type' in self.fields:
            self.entries['client_type'].config(state='disabled')

        return list(self.entries.values())[0]

    def hash_password(self):
        plain_password = self.entries['password'].get().strip()
        if not plain_password:
            messagebox.showerror("Ошибка ввода", "Поле пароля не может быть пустым.")
            return
        hashed_password = generate_password_hash(plain_password)
        self.entries['password'].delete(0, tk.END)
        self.entries['password'].insert(0, hashed_password)
        messagebox.showinfo("Успех", "Пароль захэширован.")

    def validate(self):
        data = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if value == '':
                data[field] = None
                continue

            if field == 'status' and self.user_status == 'employee' and (value == 'admin' or value == 'employee'):
                messagebox.showerror("Ошибка ввода", "Недостаточный уровень доступа")
                return False
            try:
                if field in ['date_of_registration', 'opening_date', 'closing_date', 'date', 'date_of_employment',
                             'validity_period']:
                    try:
                        datetime.strptime(value, '%Y-%m-%d')
                    except ValueError:
                        messagebox.showerror("Ошибка ввода", "Неверный формат даты. Используйте YYYY-MM-DD.")
                        return False
                if field.endswith('_id'):
                    if not value.isdigit():
                        raise ValueError(f"Поле {field} должно содержать только цифры.")
                if field == 'card_number':
                    if not re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{4}', value):
                        raise ValueError("Номер карты должен быть в формате xxxx-xxxx-xxxx-xxxx.")
                if field in ['security_code', 'card_amount', 'interest_rate', 'deposit_amount', 'inn', 'kpp',
                             'loan_amount']:
                    if not re.fullmatch(r'\d+(\.\d+)?', value):
                        raise ValueError(f"Поле {field} должно содержать только цифры.")
                if field == 'telephone_number':
                    if not re.fullmatch(r'\+7-\d{3}-\d{3}-\d{2}-\d{2}', value):
                        raise ValueError("Номер телефона должен быть в формате +7-XXX-XXX-XX-XX.")
                if field == 'passport_serial':
                    if not re.fullmatch(r'\d{4}', value):
                        raise ValueError("Серия паспорта должна содержать 4 цифры.")
                if field == 'passport_number':
                    if not re.fullmatch(r'\d{6}', value):
                        raise ValueError("Номер паспорта должен содержать 6 цифр.")
            except ValueError as ve:
                messagebox.showerror("Ошибка ввода", str(ve))
                return False
            data[field] = value

        self.result = data
        return True

class LoginDialog(simpledialog.Dialog):
    def __init__(self, parent):
        self.login = None
        self.password = None
        self.user = None
        self.client_id = None
        super().__init__(parent, title="Вход в систему")

    def body(self, master):
        tk.Label(master, text="Логин:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.login_entry = tk.Entry(master)
        self.login_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(master, text="Пароль:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        return self.login_entry

    def validate(self):
        self.login = self.login_entry.get().strip()
        self.password = self.password_entry.get().strip()

        if not self.login or not self.password:
            messagebox.showerror("Ошибка ввода", "Поля логина и пароля не могут быть пустыми.")
            return False

        try:
            user = Users.get(Users.login == self.login)
            if check_password_hash(user.password, self.password):
                self.user = user
                if user.status == 'client':
                    client = Client.get(Client.id == user.id)
                    self.client_id = client.id
                    self.result = {'user': user, 'client_id': self.client_id}
                else:
                    self.result = {'user': user}
                return True
            else:
                messagebox.showerror("Ошибка входа", "Неверный логин или пароль.")
                return False
        except Users.DoesNotExist:
            messagebox.showerror("Ошибка входа", "Неверный логин или пароль.")
            return False
        except Client.DoesNotExist:
            messagebox.showerror("Ошибка", "Запись клиента не найдена.")
            return False

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Банковское Приложение")
        self.geometry("1200x700")
        db.connect()

        user_info = self.show_login()

        if not user_info:
            self.destroy()
            return

        self.user = user_info['user']
        self.client_id = user_info.get('client_id')

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=1, fill='both')

        self.tables_tab = ttk.Frame(self.notebook)
        self.custom_query_tab = ttk.Frame(self.notebook)

        self.available_tables = []

        if self.user.status == 'admin':
            self.available_tables = [
                'Users', 'Organization_Data', 'Personal_Data', 'Client', 'Employee',
                'Deposit', 'Loan', 'Card', 'Bank_Account', 'Transaction'
            ]
            self.notebook.add(self.tables_tab, text='Таблицы')
            self.notebook.add(self.custom_query_tab, text='Ввести SQL Запрос')
        elif self.user.status == 'employee':
            self.available_tables = [
                'Users', 'Organization_Data', 'Personal_Data', 'Client',
                'Deposit', 'Loan', 'Card', 'Bank_Account', 'Transaction'
            ]
            self.notebook.add(self.tables_tab, text='Таблицы')
        elif self.user.status == 'client':
            self.available_tables = [
                'Personal_Data', 'Organization_Data', 'Client', 'Deposit', 'Loan',
                'Card', 'Bank_Account', 'Transaction'
            ]
            self.notebook.add(self.tables_tab, text='Мои Данные')

        self.create_tables_tab()
        if self.user.status == 'admin':
            self.create_custom_query_tab()

        self.create_menu()

    def show_login(self):
        dialog = LoginDialog(self)
        return dialog.result

    def create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        user_menu = tk.Menu(menu_bar, tearoff=0)
        user_menu.add_command(label="Выход", command=self.logout)
        menu_bar.add_cascade(label=f"Добро пожаловать, {self.user.login}", menu=user_menu)

    def logout(self):
        self.destroy()
        db.close()

    def create_tables_tab(self):
        if not self.available_tables:
            messagebox.showwarning("Предупреждение", "Нет доступных таблиц для отображения.")
            return

        self.table_selected = tk.StringVar()
        self.table_combo = ttk.Combobox(
            self.tables_tab, values=self.available_tables, state='readonly',
            textvariable=self.table_selected
        )
        self.table_combo.bind("<<ComboboxSelected>>", self.load_table)
        self.table_combo.pack(pady=10)

        button_frame = tk.Frame(self.tables_tab)
        button_frame.pack(pady=5)


        self.add_button = tk.Button(button_frame, text="Добавить", command=self.add_record, state='disabled')
        self.add_button.pack(side='left', padx=5)

        self.edit_button = tk.Button(button_frame, text="Изменить", command=self.edit_record, state='disabled')
        self.edit_button.pack(side='left', padx=5)

        self.delete_button = tk.Button(button_frame, text="Удалить", command=self.delete_record, state='disabled')
        self.delete_button.pack(side='left', padx=5)

        self.export_csv_button = tk.Button(button_frame, text="Экспорт CSV", command=self.export_csv, state='disabled')
        self.export_csv_button.pack(side='left', padx=5)

        self.export_xlsx_button = tk.Button(button_frame, text="Экспорт XLSX", command=self.export_xlsx, state='disabled')
        self.export_xlsx_button.pack(side='left', padx=5)

        self.tree = ttk.Treeview(self.tables_tab, columns=[], show='headings')
        self.tree.pack(expand=1, fill='both', pady=10)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def sort_treeview(self, col, reverse):
        try:
            l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
            try:
                l.sort(key=lambda t: float(t[0]), reverse=reverse)
            except ValueError:
                l.sort(reverse=reverse)
            for index, (val, k) in enumerate(l):
                self.tree.move(k, '', index)
            self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))
        except Exception as e:
            messagebox.showerror("Ошибка сортировки", str(e))

    def delete_record(self):
        if self.user.status == 'client':
            messagebox.showerror("Ошибка прав доступа", "Клиент не может удалять записи.")
            return

        table = self.table_selected.get()
        model = self.get_model(table)
        if not model:
            messagebox.showerror("Ошибка", f"Модель для таблицы {table} не найдена.")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления.")
            return

        values = self.tree.item(selected[0], 'values')
        columns = [field.name for field in model._meta.sorted_fields]
        record_dict = dict(zip(columns, values))
        record_id = record_dict.get('id')
        if not record_id:
            messagebox.showerror("Ошибка", "Не удалось определить ID записи.")
            return

        confirm = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить запись?")
        if confirm:
            try:
                record = model.get(model.id == record_id)
                record.delete_instance()
                messagebox.showinfo("Успех", "Запись успешно удалена.")
                self.load_table()
            except model.DoesNotExist:
                messagebox.showerror("Ошибка", "Запись не найдена в базе данных.")
            except Exception as e:
                messagebox.showerror("Ошибка при удалении записи", str(e))


    def load_table(self, event=None):
        table = self.table_selected.get()
        model = self.get_model(table)
        if not model:
            messagebox.showerror("Ошибка", f"Модель для таблицы {table} не найдена.")
            return

        records = []
        if self.user.status == 'admin':
            records = list(model.select())
        elif self.user.status == 'employee':
            if table == 'Users':
                records = list(model.select().where(Users.status == 'client'))  # Only clients for employees
            else:
                records = list(model.select())
        elif self.user.status == 'client':
            if not self.client_id:
                messagebox.showerror("Ошибка", "Идентификатор клиента не найден.")
                return
            try:
                if table == 'Personal_Data':
                    client = Client.get(Client.id == self.client_id)
                    if client.personal_data:
                        records = [client.personal_data]
                elif table == 'Organization_Data':
                    client = Client.get(Client.id == self.client_id)
                    if client.organization_data:
                        records = [client.organization_data]
                elif table == 'Client':
                    client = Client.get(Client.id == self.client_id)
                    records = [client]
                elif table == 'Bank_Account':
                    records = list(Bank_Account.select().where(Bank_Account.client == self.client_id))
                elif table == 'Deposit':
                    records = list(Deposit.select().join(
                        Bank_Account, on=(Deposit.id == Bank_Account.deposit)
                    ).where(Bank_Account.client == self.client_id))
                elif table == 'Loan':
                    records = list(Loan.select().join(
                        Bank_Account, on=(Loan.id == Bank_Account.loan)
                    ).where(Bank_Account.client == self.client_id))
                elif table == 'Card':
                    records = list(Card.select().join(
                        Bank_Account, on=(Card.id == Bank_Account.card)
                    ).where(Bank_Account.client == self.client_id))
                elif table == 'Transaction':
                    records_from = list(Transaction.select().join(
                        Bank_Account, on=(Transaction.bank_account_from == Bank_Account.id)
                    ).where(Bank_Account.client == self.client_id))
                    records_to = list(Transaction.select().join(
                        Bank_Account, on=(Transaction.bank_account_to == Bank_Account.id)
                    ).where(Bank_Account.client == self.client_id))
                    records = records_from + records_to
                else:
                    records = []
            except Client.DoesNotExist:
                records = []
            except Exception as e:
                messagebox.showerror("Ошибка", f"Произошла ошибка при загрузке данных: {e}")
                return

        self.tree.delete(*self.tree.get_children())
        columns = [field.name for field in model._meta.sorted_fields]
        self.tree['columns'] = columns

        for col in columns:
            self.tree.heading(col, text=col.replace('_', ' ').capitalize(),
                              command=lambda _col=col: self.sort_treeview(_col, False))
            self.tree.column(col, width=150, anchor='center')

        for record in records:
            row = [getattr(record, col) for col in columns]
            self.tree.insert('', 'end', values=row)

        # Настройка прав доступа к кнопкам
        if self.user.status == 'admin':
            self.add_button.config(state='normal')
            self.edit_button.config(state='disabled')
            self.delete_button.config(state='disabled')
            self.export_csv_button.config(state='normal')
            self.export_xlsx_button.config(state='normal')
        elif self.user.status == 'employee':
            if table != 'Transaction':
                self.add_button.config(state='normal')
                self.edit_button.config(state='normal')
                self.delete_button.config(state='normal')
            else:
                self.add_button.config(state='disabled')
                self.edit_button.config(state='disabled')
                self.delete_button.config(state='disabled')
            self.export_csv_button.config(state='disabled')
            self.export_xlsx_button.config(state='disabled')
        elif self.user.status == 'client':
            self.add_button.config(state='disabled')
            self.edit_button.config(state='disabled')
            self.delete_button.config(state='disabled')
            self.export_csv_button.config(state='disabled')
            self.export_xlsx_button.config(state='disabled')

    def get_model(self, table_name):
        models = {
            'Users': Users,
            'Organization_Data': Organization_Data,
            'Personal_Data': Personal_Data,
            'Client': Client,
            'Employee': Employee,
            'Deposit': Deposit,
            'Loan': Loan,
            'Card': Card,
            'Bank_Account': Bank_Account,
            'Transaction': Transaction
        }
        return models.get(table_name, None)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            self.edit_button.config(state='disabled')
            self.delete_button.config(state='disabled')
            return

        table = self.table_selected.get()
        if self.user.status == 'client':
            self.edit_button.config(state='disabled')
            self.delete_button.config(state='disabled')
            return

        if self.user.status == 'admin' or (self.user.status == 'employee' and table != 'Transaction'):
            self.edit_button.config(state='normal')
            self.delete_button.config(state='normal')
        else:
            self.edit_button.config(state='disabled')
            self.delete_button.config(state='disabled')

    def add_record(self):
        table = self.table_selected.get()
        model = self.get_model(table)
        if not model:
            messagebox.showerror("Ошибка", f"Модель для таблицы {table} не найдена.")
            return

        if self.user.status == 'client':
            messagebox.showerror("Ошибка прав доступа", "Клиент не может добавлять записи.")
            return

        fields = [field.name for field in model._meta.sorted_fields if field.name != 'id']
        dialog = AddEditDialog(self, f"Добавить в {table}", fields, user_status=self.user.status)
        if dialog.result is not None:
            data = {k: v for k, v in dialog.result.items()}

            if self.user.status == 'employee' and 'status' in data and 'login' in data:
                data['status'] = 'client'

            if 'password' in data and data['password']:
                pass
            else:
                data.pop('password', None)

            try:
                obj = model.create(**data)
                messagebox.showinfo("Успех", "Запись успешно добавлена.")
                self.load_table()
            except Exception as e:
                messagebox.showerror("Ошибка при вставке записи", str(e))

    def edit_record(self):
        if self.user.status == 'client':
            messagebox.showerror("Ошибка прав доступа", "Клиент не может изменять записи.")
            return

        table = self.table_selected.get()
        model = self.get_model(table)
        if not model:
            messagebox.showerror("Ошибка", f"Модель для таблицы {table} не найдена.")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для изменения.")
            return
        values = self.tree.item(selected[0], 'values')
        columns = [field.name for field in model._meta.sorted_fields]
        record_dict = dict(zip(columns, values))
        record_id = record_dict.get('id')
        if not record_id:
            messagebox.showerror("Ошибка", "Не удалось определить ID записи.")
            return

        try:
            record = model.get(model.id == record_id)
        except model.DoesNotExist:
            messagebox.showerror("Ошибка", "Запись не найдена в базе данных.")
            return

        fields = [field.name for field in model._meta.sorted_fields if field.name != 'id']
        initial_data = {field: getattr(record, field) for field in fields}
        dialog = AddEditDialog(self, f"Изменить в {table}", fields, initial_data=initial_data, user_status=self.user.status)
        if dialog.result is not None:
            data = {k: v for k, v in dialog.result.items()}

            if self.user.status == 'employee' and 'status' in data and 'login' in data:
                data['status'] = 'client'

            if 'password' in data and data['password']:
                pass
            elif 'password' in data:
                data.pop('password')

            try:
                for key, value in data.items():
                    setattr(record, key, value)
                record.save()
                messagebox.showinfo("Успех", "Запись успешно обновлена.")
                self.load_table()
            except Exception as e:
                messagebox.showerror("Ошибка при обновлении записи", str(e))

    def export_csv(self):
        table = self.table_selected.get()
        model = self.get_model(table)
        if not model:
            messagebox.showerror("Ошибка", f"Модель для таблицы {table} не найдена.")
            return

        try:
            if self.user.status == 'client':
                records = list(model.select().where(Bank_Account.client == self.client_id))
            else:
                records = list(model.select())
        except Client.DoesNotExist:
            records = []

        columns = [field.name for field in model._meta.sorted_fields]

        file_path = filedialog.asksaveasfilename(defaultextension='.csv',
                                                 filetypes=[("CSV files", '*.csv')])
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([col.replace('_', ' ').capitalize() for col in columns])
                for record in records:
                    row = [getattr(record, col) for col in columns]
                    writer.writerow(row)
            messagebox.showinfo("Успех", f"Таблица '{table}' успешно экспортирована в CSV.")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))

    def export_xlsx(self):
        table = self.table_selected.get()
        model = self.get_model(table)
        if not model:
            messagebox.showerror("Ошибка", f"Модель для таблицы {table} не найдена.")
            return

        try:
            if self.user.status == 'client':
                records = list(model.select().where(Bank_Account.client == self.client_id))
            else:
                records = list(model.select())
        except Client.DoesNotExist:
            records = []

        columns = [field.name for field in model._meta.sorted_fields]
        data = [[getattr(record, col) for col in columns] for record in records]

        file_path = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                                 filetypes=[("Excel files", '*.xlsx')])
        if not file_path:
            return

        try:
            df = pd.DataFrame(data, columns=[col.replace('_', ' ').capitalize() for col in columns])
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Успех", f"Таблица '{table}' успешно экспортирована в XLSX.")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))

    def create_custom_query_tab(self):
        input_frame = tk.Frame(self.custom_query_tab)
        input_frame.pack(pady=10, padx=10, fill='x')

        tk.Label(input_frame, text="Введите SQL запрос:").pack(anchor='w')
        self.custom_query_text = scrolledtext.ScrolledText(input_frame, height=10)
        self.custom_query_text.pack(fill='x', pady=5)

        execute_button = tk.Button(input_frame, text="Выполнить запрос", command=self.execute_custom_query)
        execute_button.pack(pady=5)

        self.custom_query_tree = ttk.Treeview(self.custom_query_tab, columns=[], show='headings')
        self.custom_query_tree.pack(expand=1, fill='both', pady=10)

    def manual_syntax_check(self, query: str) -> bool:
        query = query.strip().lower()

        if not query.startswith(("select", "insert", "update", "delete")):
            messagebox.showerror("Ошибка синтаксиса", "Запрос должен начинаться с SELECT, INSERT, UPDATE или DELETE.")
            return False

        if "from" not in query and not query.startswith("insert"):
            messagebox.showerror("Ошибка синтаксиса", "Запрос должен содержать ключевое слово FROM или соответствующее для INSERT/UPDATE/DELETE.")
            return False

        return True

    def execute_custom_query(self):
        query = self.custom_query_text.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Предупреждение", "Поле запроса не может быть пустым.")
            return

        if not self.manual_syntax_check(query):
            return

        try:
            results = db.execute_sql(query)
            if results.description is None:
                db.commit()
                messagebox.showinfo("Успех", "Запрос выполнен успешно.")
                return
            columns = [desc[0] for desc in results.description]
            data = results.fetchall()
        except peewee.OperationalError as e:
            messagebox.showerror("Синтаксическая ошибка", str(e))
            return
        except Exception as e:
            messagebox.showerror("Ошибка выполнения запроса", str(e))
            return

        self.custom_query_tree.delete(*self.custom_query_tree.get_children())
        self.custom_query_tree['columns'] = columns
        for col in columns:
            self.custom_query_tree.heading(col, text=col.replace('_', ' ').capitalize(),
                                           command=lambda _col=col: self.sort_treeview_custom(_col, False))
            self.custom_query_tree.column(col, width=150, anchor='center')
        for row in data:
            self.custom_query_tree.insert('', 'end', values=row)

    def sort_treeview_custom(self, col, reverse):
        try:
            l = [(self.custom_query_tree.set(k, col), k) for k in self.custom_query_tree.get_children('')]
            try:
                l.sort(key=lambda t: float(t[0]), reverse=reverse)
            except ValueError:
                l.sort(reverse=reverse)
            for index, (val, k) in enumerate(l):
                self.custom_query_tree.move(k, '', index)
            self.custom_query_tree.heading(col, command=lambda: self.sort_treeview_custom(col, not reverse))
        except Exception as e:
            messagebox.showerror("Ошибка сортировки", str(e))
