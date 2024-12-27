from peewee import *
from database import db


class BaseModel(Model):
    class Meta:
        database = db

class Users(BaseModel):
    id = AutoField()
    login = CharField(max_length=255, unique=True)
    password = CharField(max_length=255)
    status = CharField(max_length=50)

class Organization_Data(BaseModel):
    id = AutoField()
    organization_name = CharField(max_length=255)
    owner_name = CharField(max_length=255)
    email = CharField(max_length=255, unique=True)
    inn = CharField(max_length=20)
    kpp = CharField(max_length=20)


class Personal_Data(BaseModel):
    id = AutoField()
    fcs = CharField(max_length=255)
    address = CharField(max_length=255)
    telephone_number = CharField(max_length=20)
    email = CharField(max_length=255, unique=True)
    passport_serial = CharField(max_length=20)
    passport_number = CharField(max_length=20)


class Client(BaseModel):
    id = AutoField()
    client_type = CharField(max_length=50)
    status = CharField(max_length=50)
    date_of_registration = DateField()
    personal_data = ForeignKeyField(
        Personal_Data, backref='clients', null=True, on_delete='RESTRICT'
    )
    organization_data = ForeignKeyField(
        Organization_Data, backref='clients', null=True, on_delete='RESTRICT'
    )


class Employee(BaseModel):
    id = AutoField()
    fcs = CharField(max_length=255)
    telephone_number = CharField(max_length=20)
    email = CharField(max_length=255, unique=True)
    date_of_employment = DateField()
    position = CharField(max_length=100)
    status = CharField(max_length=50)
    rating = DecimalField(max_digits=6, decimal_places=2, null=True)


class Deposit(BaseModel):
    id = AutoField()
    interest_rate = IntegerField()
    deposit_amount = IntegerField()
    opening_date = DateField()
    closing_date = DateField()
    employee = ForeignKeyField(
        Employee, backref='deposits', null=True, on_delete='SET NULL'
    )


class Loan(BaseModel):
    id = AutoField()
    interest_rate = DecimalField(max_digits=5, decimal_places=2)
    loan_amount = DecimalField(max_digits=12, decimal_places=2)
    loan_term = CharField(max_length=50)
    repayment_period = CharField(max_length=50)
    opening_date = DateField()
    closing_date = DateField()
    status = CharField(max_length=50)
    employee = ForeignKeyField(
        Employee, backref='loans', null=True, on_delete='SET NULL'
    )


class Card(BaseModel):
    id = AutoField()
    card_number = CharField(max_length=20, unique=True)
    security_code = CharField(max_length=10)
    card_amount = DecimalField(max_digits=12, decimal_places=2)
    opening_date = DateField()
    validity_period = DateField()
    status = CharField(max_length=50)
    employee = ForeignKeyField(
        Employee, backref='cards', null=True, on_delete='SET NULL'
    )


class Bank_Account(BaseModel):
    id = AutoField()
    bank_account_type = CharField(max_length=50)
    opening_date = DateField()
    card = ForeignKeyField(
        Card, backref='bank_accounts', null=True, on_delete='SET NULL'
    )
    loan = ForeignKeyField(
        Loan, backref='bank_accounts', null=True, on_delete='SET NULL'
    )
    deposit = ForeignKeyField(
        Deposit, backref='bank_accounts', null=True, on_delete='SET NULL'
    )
    client = ForeignKeyField(
        Client, backref='bank_accounts', null=True, on_delete='SET NULL'
    )


class Transaction(BaseModel):
    id = AutoField()
    date = DateField()
    time = TimeField()
    amount_money = DecimalField(max_digits=12, decimal_places=2)
    bank_account_from = ForeignKeyField(
        Bank_Account, backref='Transaction', null=True, on_delete='SET NULL', column_name='bank_account_from'
    )
    bank_account_to = ForeignKeyField(
        Bank_Account, backref='Transaction', null=True, on_delete='SET NULL', column_name='bank_account_to'
    )

