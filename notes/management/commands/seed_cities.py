from django.core.management.base import BaseCommand
from notes.models import Category, Note


CITIES = [
    {"city": "Kyiv", "region": "Kyiv Region", "river": "Dnipro", "founded": "482"},
    {"city": "Lviv", "region": "Lviv Region", "river": "Poltava", "founded": "1256"},
    {"city": "Kharkiv", "region": "Kharkiv Region", "river": "Kharkiv", "founded": "1654"},
    {"city": "Odesa", "region": "Odesa Region", "river": "Dniester", "founded": "1794"},
    {"city": "Dnipro", "region": "Dnipropetrovsk Region", "river": "Dnipro", "founded": "1776"},
    {"city": "Cherkasy", "region": "Cherkasy Region", "river": "Dnipro", "founded": "1286"},
    {"city": "Zaporizhzhia", "region": "Zaporizhzhia Region", "river": "Dnipro", "founded": "1770"},
    {"city": "Lutsk", "region": "Volyn Region", "river": "Styr", "founded": "1085"},
    {"city": "Uzhhorod", "region": "Zakarpattia Region", "river": "Uzh", "founded": "893"},
    {"city": "Chernivtsi", "region": "Chernivtsi Region", "river": "Prut", "founded": "1408"},
    {"city": "Vinnytsia", "region": "Vinnytsia Region", "river": "Southern Buh", "founded": "1363"},
    {"city": "Poltava", "region": "Poltava Region", "river": "Vorskla", "founded": "1174"},
]


class Command(BaseCommand):
    help = "Наповнює базу тими самими 12 містами, що раніше були захардкоджені у views.py"

    def handle(self, *args, **options):
        for item in CITIES:
            category, _ = Category.objects.get_or_create(title=item["region"])

            Note.objects.get_or_create(
                title=item["city"],
                defaults={
                    "text": f"Річка: {item['river']}. Засновано у {item['founded']} році.",
                    "category": category,
                },
            )

        self.stdout.write(self.style.SUCCESS(f"Додано {len(CITIES)} нотаток про міста!"))
