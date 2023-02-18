import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Дополнительная команда для manage.py для переименования проекта"""
    help = 'Переименовать проект Django'

    # Необходимо изменить после переименования
    current_project_name = 'django_encommerce'

    def add_arguments(self, parser):
        """Необходимые аргументы для работы команды"""
        parser.add_argument(
            'new_project_name', type=str, help='Введите новое название проекта'
        )
    
    def handle(self, *args, **kwargs):
        new_project_name = kwargs['new_project_name']

        files_to_rename = [
            f'{self.current_project_name}/settings/base.py',
            f'{self.current_project_name}/wsgi.py',
            'manage.py'
        ]

        folder_to_rename = self.current_project_name

        for f in files_to_rename:
            with open(f, 'r') as file:
                filedata = file.read()

            filedata = filedata.replace(self.current_project_name, new_project_name)

            with open(f, 'w') as file:
                file.write(filedata)

        os.rename(folder_to_rename, new_project_name)

        self.stdout.write(self.style.SUCCESS('Имя проекта было изменено на %s' % new_project_name))

