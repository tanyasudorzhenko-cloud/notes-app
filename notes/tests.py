from django.test import TestCase

"""
Тести для функціоналу нотаток.

- NoteModelTests, NoteFormTests   - unit-тести: перевіряють логіку
  збереження/редагування напряму (без HTTP), швидкі й ізольовані.

- NoteViewsIntegrationTests       - інтеграційні тести (Extra): через
  Django test client реально "заходять" на сторінки (create/detail/
  delete/list з фільтрами) і перевіряють повний ланцюжок запит -> view
  -> база даних -> відповідь.
"""

from django.test import TestCase, Client
from django.urls import reverse

from .models import Category, Note
from .forms import NoteForm


# ---------------------------------------------------------------------------
# Unit-тести: модель
# ---------------------------------------------------------------------------

class NoteModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Робота")

    def test_note_is_created_with_correct_fields(self):
        note = Note.objects.create(
            title="Здати звіт",
            text="Підготувати квартальний звіт.",
            category=self.category,
        )
        self.assertEqual(note.title, "Здати звіт")
        self.assertEqual(note.text, "Підготувати квартальний звіт.")
        self.assertEqual(note.category, self.category)
        self.assertIsNone(note.reminder)

    def test_note_str_returns_title(self):
        note = Note.objects.create(title="Купити молоко", text="...", category=self.category)
        self.assertEqual(str(note), "Купити молоко")

    def test_note_can_be_updated(self):
        note = Note.objects.create(title="Старий заголовок", text="старий текст", category=self.category)

        note.title = "Новий заголовок"
        note.text = "новий текст"
        note.save()

        updated = Note.objects.get(pk=note.pk)
        self.assertEqual(updated.title, "Новий заголовок")
        self.assertEqual(updated.text, "новий текст")


# ---------------------------------------------------------------------------
# Unit-тести: форма (саме тут "живе" логіка збереження/редагування)
# ---------------------------------------------------------------------------

class NoteFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Особисте")

    def _valid_data(self, **overrides):
        data = {
            "title": "Нотатка",
            "text": "Текст нотатки",
            "reminder": "",
            "category": self.category.pk,
        }
        data.update(overrides)
        return data

    def test_valid_form_creates_note(self):
        form = NoteForm(data=self._valid_data(title="Тест форми"))
        self.assertTrue(form.is_valid(), form.errors)

        note = form.save()
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(note.title, "Тест форми")

    def test_form_updates_existing_note(self):
        note = Note.objects.create(title="Було", text="старий текст", category=self.category)

        form = NoteForm(
            data=self._valid_data(title="Стало", text="новий текст"),
            instance=note,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        updated = Note.objects.get(pk=note.pk)
        self.assertEqual(updated.title, "Стало")
        self.assertEqual(updated.text, "новий текст")
        # переконуємось, що це той самий запис, а не новий
        self.assertEqual(Note.objects.count(), 1)

    def test_form_invalid_without_title(self):
        form = NoteForm(data=self._valid_data(title=""))
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_form_invalid_without_category(self):
        form = NoteForm(data=self._valid_data(category=""))
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)

    def test_reminder_is_optional(self):
        form = NoteForm(data=self._valid_data(reminder=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_reminder_is_parsed_from_datetime_local_format(self):
        form = NoteForm(data=self._valid_data(reminder="2026-08-20T14:30"))
        self.assertTrue(form.is_valid(), form.errors)
        note = form.save()
        self.assertEqual(note.reminder.strftime("%Y-%m-%dT%H:%M"), "2026-08-20T14:30")


# ---------------------------------------------------------------------------
# Інтеграційні тести (Extra): через test client, реальні HTTP-запити
# ---------------------------------------------------------------------------

class NoteViewsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category_work = Category.objects.create(title="Робота")
        self.category_home = Category.objects.create(title="Особисте")

    def test_notes_list_returns_200(self):
        response = self.client.get(reverse("notes_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notes/notes_list.html")

    def test_note_create_get_shows_form(self):
        response = self.client.get(reverse("note_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    def test_note_create_post_saves_note_to_database(self):
        response = self.client.post(reverse("note_create"), {
            "title": "Нова нотатка",
            "text": "Текст",
            "reminder": "",
            "category": self.category_work.pk,
        })
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.first()
        self.assertEqual(note.title, "Нова нотатка")
        # після успішного створення - редірект на деталі нотатки
        self.assertRedirects(response, reverse("note_detail", args=[note.pk]))

    def test_note_detail_get_shows_note_data(self):
        note = Note.objects.create(title="Показати мене", text="...", category=self.category_work)
        response = self.client.get(reverse("note_detail", args=[note.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Показати мене")

    def test_note_detail_post_updates_note(self):
        note = Note.objects.create(title="Старе", text="старий текст", category=self.category_work)

        response = self.client.post(reverse("note_detail", args=[note.pk]), {
            "title": "Нове",
            "text": "новий текст",
            "reminder": "",
            "category": self.category_home.pk,
        })

        note.refresh_from_db()
        self.assertEqual(note.title, "Нове")
        self.assertEqual(note.category, self.category_home)
        self.assertRedirects(response, reverse("note_detail", args=[note.pk]))

    def test_note_delete_get_shows_confirmation(self):
        note = Note.objects.create(title="Видалити мене", text="...", category=self.category_work)
        response = self.client.get(reverse("note_delete", args=[note.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Видалити мене")
        # GET нічого не видаляє
        self.assertEqual(Note.objects.count(), 1)

    def test_note_delete_post_removes_note(self):
        note = Note.objects.create(title="Видалити мене", text="...", category=self.category_work)

        response = self.client.post(reverse("note_delete", args=[note.pk]))

        self.assertEqual(Note.objects.count(), 0)
        self.assertRedirects(response, reverse("notes_list"))

    def test_filter_by_category(self):
        Note.objects.create(title="Робоча", text="...", category=self.category_work)
        Note.objects.create(title="Домашня", text="...", category=self.category_home)

        response = self.client.get(reverse("notes_list"), {"category": self.category_work.pk})

        self.assertContains(response, "Робоча")
        self.assertNotContains(response, "Домашня")

    def test_search_by_title(self):
        Note.objects.create(title="Купити молоко", text="...", category=self.category_home)
        Note.objects.create(title="Здати звіт", text="...", category=self.category_work)

        response = self.client.get(reverse("notes_list"), {"q": "молоко"})

        self.assertContains(response, "Купити молоко")
        self.assertNotContains(response, "Здати звіт")# Create your tests here.
