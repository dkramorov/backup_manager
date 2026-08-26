Описание
-----------
Менеджер для создания резервных копий баз

Установка пакетом
-----------
Для локальной разработки::
    pip install -e packages/backup_manager
Для обычной установки через requirements.txt::
    excel_manager @ git+https://github.com/dkramorov/backup_manager.git


Импорт
-----------
Проверка::
    from managers.backup_manager import BackupManager


Удаление
-----------
Удалить пакет::
    pip uninstall backup_manager

Для создания пакета
https://docs.python.org/3.10/distutils/introduction.html#distutils-simple-example
https://docs.python.org/3.10/distutils/sourcedist.html
::
    python setup.py sdist




