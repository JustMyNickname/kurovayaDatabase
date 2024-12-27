from peewee import *
from playhouse.migrate import PostgresqlMigrator, migrate
from models import db, Loan

migrator = PostgresqlMigrator(db)

with db.connection_context():
    migrate(
        migrator.drop_column('loan', 'trust')
    )

print("Migration: Removed 'trust' column from 'Loan' table.")
