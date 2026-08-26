import datetime
import os
import time

from managers.simple_logger import logger
from managers.system_manager import search_binary, system_cmd


class PostgresqlBackupManager:
    """Менеджер по резервному копированию postgresql базы
    """
    def __init__(self,
                 db_name: str = None,
                 db_host: str = 'localhost',
                 db_port: int = 5432,
                 db_username: str = None,
                 db_passwd: str = None,
                 pg_dump_v: str = None):
        """Инициализация
           :param db_name: имя бд
           :param db_host: адрес сервера бд
           :param db_port: порт сервера бд
           :param db_username: имя пользователя бд
           :param pg_dump_v: версия pg_dump, которая нужна, например, 15.15 или 18.4
        """
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.db_username = db_username
        self.db_passwd = db_passwd

        self.gzip_path = search_binary('gzip')
        if not self.gzip_path:
            raise Exception('gzip not found')
        self.pg_dump_path = search_binary('pg_dump')
        if not self.pg_dump_path or pg_dump_v:
            self.pg_dump_path = self.get_pg_dump(v=pg_dump_v)
        if not self.pg_dump_path:
            raise Exception('pg_dump not found')

    def get_pg_dump(self,
                    v: str = '15.15',
                    workdir: str = '/tmp',
                    with_install: bool = False,
                    force: bool = False):
        """Получение pg_dump
           wget https://ftp.postgresql.org/pub/source/v15.15/postgresql-15.15.tar.gz
           :param v: требуемая версия postgresql
           :param workdir: рабочая директория
        """
        archive = 'postgresql-%s.tar.gz' % v
        workdir = '%s/%s' % (workdir.rstrip('/'), v)
        os.system('mkdir -p %s' % workdir)
        cd_tmp = 'cd %s' % workdir
        folder = archive.split('.tar.gz')[0]
        pg_dump_path = '%s/%s/src/bin/pg_dump/pg_dump' % (workdir, folder)
        if not os.path.exists(pg_dump_path):
            archive_full_path = os.path.join(workdir, archive)
            if force or not os.path.exists(archive_full_path):
                link = 'https://ftp.postgresql.org/pub/source/v%s/%s' % (v, archive)
                os.system('%s && wget %s' % (cd_tmp, link))
                if not os.path.exists(os.path.join(workdir, archive)):
                    raise Exception('Archive not found on server %s' % link)
                os.system('%s && tar -xzf %s' % (cd_tmp, archive))
            if not with_install:
                os.system('%s && cd %s && ./configure && make -C src/bin' % (cd_tmp, folder))
        if with_install:
            os.system('%s && cd %s && ./configure && make -C src/bin install' % (cd_tmp, folder))
        os.system('%s --version' % pg_dump_path)
        if os.path.exists(pg_dump_path):
            self.pg_dump_path = pg_dump_path
            return pg_dump_path

    def create_backup(self,
                      media_folder: str = '/tmp'):
        """Выполнить резервное копирование базы данных
           :param media_folder: папка, куда будем сохранять дамп
        """
        if not self.db_name:
            raise Exception('База данных не указана')
        if not os.path.exists(media_folder):
            os.mkdir(media_folder)
        if not os.path.exists(media_folder):
            raise Exception('Папка %s не существует' % media_folder)

        started = time.time()

        backup_path = os.path.join(media_folder, '%s_%s.sql' % (
            self.db_name,
            datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'),
        ))

        #cmd = '%s -c -h %s -p %s -U %s %s > %s' % (
        #    pg_dump_path,
        #    self.db_host,
        #    self.db_port,
        #    self.db_username,
        #    self.db_name,
        #    backup_path,
        #)

        compressed_path = '%s.tgz' % backup_path
        cmd = '%s -v -c -h %s -p %s -U %s %s|%s > %s' % (
            self.pg_dump_path,
            self.db_host,
            self.db_port,
            self.db_username,
            self.db_name,
            self.gzip_path,
            compressed_path,
        )

        if self.db_passwd:
            cmd = 'export PGPASSWORD="%s" && %s' % (self.db_passwd, cmd)

        logger.info('[BACKUP]: %s' % cmd)
        try:
            backup_result = system_cmd([cmd])
        except Exception as e:
            backup_result = str(e)

        backup_size = 0
        if not os.path.exists(compressed_path):
            logger.info('[ERROR]: %s' % backup_result)
        else:
            backup_size = os.path.getsize(compressed_path)
        backup_took = int(time.time() - started)
        logger.info('backup took: %s, size: %s' % (backup_took, backup_size))

    def create_direct_s3_backup(self,
                                aws_endpoint_url: str,
                                aws_access_key_id: str,
                                aws_secret_access_key_id: str,
                                bucket: str = 'tmp', location: str = 'tmp'):
        """Выполнить резервное копирование базы данных напрямую в S3
           без использования локальной папки через awscli
           :param aws_endpoint_url: адрес до хранилища (например, https://storage.yandexcloud.net)
           :param aws_access_key_id: ключ s3
           :param aws_secret_access_key_id: серкретный ключ s3
           :param bucket: бакет
           :param location: папка в бакете
        """
        started = time.time()
        aws_path = search_binary('aws')
        if not aws_path:
            raise Exception('aws (awscli) not found')
        if not self.db_name:
            raise Exception('База данных не указана')
        backup_path = '%s_%s.sql' % (
            self.db_name,
            datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'),
        )
        compressed_path = '%s.tgz' % backup_path

        cmd = '%s -h %s -p %s -U %s -Z 9 -v %s | %s --no-verify-ssl s3 cp - s3://%s/%s/%s' % (
            self.pg_dump_path,
            self.db_host,
            self.db_port,
            self.db_username,
            self.db_name,
            aws_path,
            bucket,
            location,
            compressed_path,
        )

        if self.db_passwd:
            cmd = 'export PGPASSWORD="%s" && %s' % (self.db_passwd, cmd)
        cmd = 'export AWS_ENDPOINT_URL="%s" && %s' % (aws_endpoint_url, cmd)
        cmd = 'export AWS_ACCESS_KEY_ID="%s" && %s' % (aws_access_key_id, cmd)
        cmd = 'export AWS_SECRET_ACCESS_KEY="%s" && %s' % (aws_secret_access_key_id, cmd)

        logger.info('[BACKUP]: %s' % cmd)
        try:
            backup_result = system_cmd([cmd])
        except Exception as e:
            backup_result = str(e)

        backup_took = int(time.time() - started)
        #logger.info('backup took: %s, size: %s' % (backup_took, backup_size))
        print(backup_result)



class BackupManager:
    """Менеджер по работе с бекапами
    """
    def __init__(self, *args, **kwargs):
        """Инициализация
        """
        self.pg_manager = PostgresqlBackupManager(*args, **kwargs)
