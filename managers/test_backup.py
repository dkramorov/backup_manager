import argparse
import os
import sys
from managers.simple_logger import logger
from managers.backup_manager import BackupManager


parser = argparse.ArgumentParser()
parser.add_argument('--host', help='Set s3 host')
parser.add_argument('--access_key', help='Set s3 access_key')
parser.add_argument('--secret_key', help='Set s3 secret_key')
parser.add_argument('--bucket', help='Set s3 bucket')
# TODO: бд параметры
args = parser.parse_args()


if __name__ == '__main__':
    logger.info("""Если возникают ошибки со сборкой, необходимо указать путь к icu4c
    export ICU_CFLAGS="-I/opt/homebrew/opt/icu4c/include"
    export ICU_LIBS="-L/opt/homebrew/opt/icu4c/lib -licui18n -licuuc -licudata"
    При ошибках с libpq (Library not loaded: /usr/local/pgsql/lib/libpq.5.dylib)
    find /opt -name libpq.5.dylib
    sudo mkdir -p /usr/local/pgsql/lib
    sudo ln -s /opt/homebrew/Cellar/postgresql@18/18.4/lib/postgresql/libpq.5.dylib /usr/local/pgsql/lib/libpq.5.dylib
    """)
    logger.info('USAGE: --host="https://storage.yandexcloud.net" --access_key="your-access-key" --secret_key="your-secret-key" --bucket="test-records-std"')
    bm = BackupManager(
        db_name='empty_project',
        db_host='localhost',
        db_port=5432,
        db_username='postgres',
        db_passwd=None,
        pg_dump_v='18.4',
    )
    #pg_dump_path = bm.pg_manager.get_pg_dump(v='18.4')
    #logger.info('pg_dump path %s' % pg_dump_path)

    #bm.pg_manager.create_backup()
    bm.pg_manager.create_direct_s3_backup(
        aws_endpoint_url=args.host or 'https://storage.yandexcloud.net',
        aws_access_key_id=args.access_key,
        aws_secret_access_key_id=args.secret_key,
        bucket=args.bucket or 'test-records-std',
    )