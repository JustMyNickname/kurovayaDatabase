import peewee

db = peewee.PostgresqlDatabase(
    'bank',
    user = 'postgres',
    password = 123,
    host = '127.0.0.1',
    port = '5432'
)
