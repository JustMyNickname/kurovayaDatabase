import os
import subprocess
import datetime

DB_NAME = "bank"
DB_USER = "postgres"
DB_PASSWORD = "123"
DB_HOST = "localhost"
DB_PORT = "5432"

BACKUP_FOLDER = r"E:\!Yandex sync\YandexDisk\BD_backup"


def backup_database():
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(BACKUP_FOLDER, f"{DB_NAME}_backup_{current_time}.sql")

    pg_dump_path = r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"
    pg_dump_command = [
        pg_dump_path,
        f"-U{DB_USER}",
        f"-h{DB_HOST}",
        f"-p{DB_PORT}",
        "-F", "c",
        "-f", backup_file,
        DB_NAME
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    try:
        subprocess.run(pg_dump_command, env=env, check=True)
        print(f"Резервная копия успешно создана: {backup_file}")
    except Exception as ex:
        print(f"Ошибка при создании резервной копии: {ex}")

backup_database()
