from peewee import *
from playhouse.migrate import PostgresqlMigrator, migrate
from models import db, Loan

migrator = PostgresqlMigrator(db)

with db.connection_context():
    migrate(
        migrator.add_column('loan', 'trust', BooleanField(default=False))
    )

print("Migration: Added 'trust' column to 'Loan' table.")
