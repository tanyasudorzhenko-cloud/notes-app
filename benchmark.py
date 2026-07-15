"""
Бенчмарк швидкості views.

Використання:
    1. Запусти сервер окремо:  python manage.py runserver
    2. Онови USERNAME/PASSWORD нижче під себе
    3. pip install httpx --break-system-packages   (якщо ще нема)
    4. python benchmark.py

Скрипт логіниться під твоїм користувачем, створює одну тестову нотатку
(щоб було що відкривати в note_detail), а тоді послідовно (одне за одним,
не паралельно) викликає кожен ендпоінт по REPEATS разів і рахує час.
"""

import re
import time

import httpx

BASE_URL = "http://127.0.0.1:8000/notes"
USERNAME = "root"          # заміни на свого користувача
PASSWORD = "root01"      # заміни на свій пароль
REPEATS = 20                # скільки разів викликати кожен ендпоінт


def _error_snippet(html: str) -> str:
    """Шукає текст помилки валідації форми в HTML, а не просто перші символи сторінки."""
    match = re.search(r'(?:text-danger|errorlist)[^>]*>\s*([^<]{1,200})', html)
    if match:
        return match.group(1).strip()
    return html[:300].replace("\n", " ")


def login(client: httpx.Client) -> None:
    login_page = client.get(f"{BASE_URL}/login/")
    csrf_token = login_page.cookies.get("csrftoken")

    response = client.post(
        f"{BASE_URL}/login/",
        data={
            "username": USERNAME,
            "password": PASSWORD,
            "csrfmiddlewaretoken": csrf_token,
        },
        headers={"Referer": f"{BASE_URL}/login/"},
    )
    if response.status_code != 302:
        raise RuntimeError(
            f"Не вдалось залогінитись (код {response.status_code}).\n"
            f"Перевір USERNAME/PASSWORD у скрипті.\n"
            f"Текст помилки: {_error_snippet(response.text)}"
        )


def create_test_note(client: httpx.Client) -> int:
    """Створює тестову нотатку і повертає її pk, щоб було що відкривати в note_detail."""
    form_page = client.get(f"{BASE_URL}/create/")
    csrf_token = form_page.cookies.get("csrftoken")

    # автоматично беремо перший доступний id категорії прямо зі сторінки форми,
    # щоб не вгадувати його вручну
    category_options = re.findall(r'<option value="(\d+)"', form_page.text)
    if not category_options:
        raise RuntimeError(
            "У базі немає жодної категорії. Спочатку створи хоча б одну "
            "через /admin/notes/category/add/, і повтори."
        )
    category_id = category_options[0]

    response = client.post(
        f"{BASE_URL}/create/",
        data={
            "title": "Бенчмарк-нотатка",
            "text": "Створено автоматично для вимірювання швидкості.",
            "reminder": "",
            "category": category_id,
            "csrfmiddlewaretoken": csrf_token,
        },
        headers={"Referer": f"{BASE_URL}/create/"},
    )
    if response.status_code != 302:
        raise RuntimeError(
            f"Не вдалось створити тестову нотатку (код {response.status_code}).\n"
            f"Текст помилки: {_error_snippet(response.text)}"
        )

    note_pk = response.headers["Location"].strip("/").split("/")[-1]
    return int(note_pk)


def measure(client: httpx.Client, name: str, method: str, url: str, repeats: int = REPEATS) -> float:
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        client.request(method, url)
        timings.append(time.perf_counter() - start)

    total = sum(timings)
    avg_ms = (total / len(timings)) * 1000
    print(f"{name:<22} | викликів: {repeats:<3} | разом: {total:6.3f}с | середнє: {avg_ms:6.1f}мс")
    return total


def main():
    with httpx.Client(follow_redirects=False) as client:
        print("Логінюсь...")
        login(client)

        print("Створюю тестову нотатку...")
        note_pk = create_test_note(client)

        print(f"\nБенчмарк ({REPEATS} викликів на кожен ендпоінт)\n" + "-" * 66)

        grand_total = 0.0
        grand_total += measure(client, "hello_notes", "GET", f"{BASE_URL}/hello/")
        grand_total += measure(client, "notes_list", "GET", f"{BASE_URL}/")
        grand_total += measure(client, "note_create (GET)", "GET", f"{BASE_URL}/create/")
        grand_total += measure(client, "note_detail (GET)", "GET", f"{BASE_URL}/{note_pk}/")

        print("-" * 66)
        print(f"{'СУМАРНО':<22} | {grand_total:.3f} секунд на всі запити разом")


if __name__ == "__main__":
    main()
