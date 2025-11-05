import csv
import os


from django.core.management.base import BaseCommand

from recipes.models import Ingredient
from backend.settings import BASE_DIR

FILE_PATH = BASE_DIR / '/app/data/'
FILENAME = 'ingredients.csv'


class Command(BaseCommand):
    """Команда для импорта данных в базу из CSV-файла."""

    help = 'Импорт данных из CSV-файла в базу данных'

    def handle(self, *args, **options):
        file = os.path.join(FILE_PATH, FILENAME)
        try:
            with open(file, 'r', encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file)
                for row in reader:
                    name, unit = row
                    Ingredient.objects.create(
                        name=name, measurement_unit=unit
                    )
                self.stdout.write(
                    self.style.SUCCESS('Данные из файла загружены в БД.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Произошла ошибка при обработке файла {e}.'
                )
            )
