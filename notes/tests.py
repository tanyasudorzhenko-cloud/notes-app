"""
Тести для функціоналу нотаток.

- NoteModelTests, NoteFormTests   - unit-тести: логіка збереження/
  редагування напряму (без HTTP).

- NoteViewsIntegrationTests       - інтеграційні тести (Extra): через
  Django test client, з залогіненим користувачем (view тепер вимагають
  автентифікації) + перевірка, що чужі нотатки недоступні.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .forms import NoteForm
from .models import Category, Note

User = get_user_model()


# ---------------------------------------------------------------------------
# Unit-тести: модель
# ---------------------------------------------------------------------------

class NoteModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Робота")
        self.user = User.objects.create_user(username="tester", password="pass12345")

    def test_note_is_created_with_correct_fields(self):
        note = Note.objects.create(
            title="Здати звіт",
            text="Підготувати квартальний звіт.",
            category=self.category,
            user=self.user,
        )
        self.assertEqual(note.title, "Здати звіт")
        self.assertEqual(note.category, self.category)
        self.assertEqual(note.user, self.user)
        self.assertIsNone(note.reminder)

    def test_note_str_returns_title(self):
        note = Note.objects.create(title="Купити молоко", text="...", category=self.category, user=self.user)
        self.assertEqual(str(note), "Купити молоко")

    def test_note_can_be_updated(self):
        note = Note.objects.create(title="Старий заголовок", text="старий текст", category=self.category, user=self.user)

        note.title = "Новий заголовок"
        note.save()

        updated = Note.objects.get(pk=note.pk)
        self.assertEqual(updated.title, "Новий заголовок")


# ---------------------------------------------------------------------------
# Unit-тести: форма
# ---------------------------------------------------------------------------

class NoteFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Особисте")
        self.user = User.objects.create_user(username="tester", password="pass12345")

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

        note = form.save(commit=False)
        note.user = self.user
        note.save()

        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(note.title, "Тест форми")

    def test_form_updates_existing_note(self):
        note = Note.objects.create(title="Було", text="старий текст", category=self.category, user=self.user)

        form = NoteForm(data=self._valid_data(title="Стало"), instance=note)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        updated = Note.objects.get(pk=note.pk)
        self.assertEqual(updated.title, "Стало")
        self.assertEqual(Note.objects.count(), 1)

    def test_form_invalid_without_title(self):
        form = NoteForm(data=self._valid_data(title=""))
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


# ---------------------------------------------------------------------------
# Інтеграційні тести (Extra): через test client, з автентифікацією
# ---------------------------------------------------------------------------

class NoteViewsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(title="Робота")

        self.user = User.objects.create_user(username="alice", password="pass12345")
        self.other_user = User.objects.create_user(username="bob", password="pass12345")

        self.my_note = Note.objects.create(
            title="Моя нотатка", text="...", category=self.category, user=self.user
        )
        self.foreign_note = Note.objects.create(
            title="Чужа нотатка", text="...", category=self.category, user=self.other_user
        )

    def test_notes_list_requires_login(self):
        response = self.client.get(reverse("notes_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_notes_list_shows_only_own_notes(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("notes_list"))

        self.assertContains(response, "Моя нотатка")
        self.assertNotContains(response, "Чужа нотатка")

    def test_note_create_assigns_current_user(self):
        self.client.login(username="alice", password="pass12345")
        self.client.post(reverse("note_create"), {
            "title": "Нова нотатка",
            "text": "Текст",
            "reminder": "",
            "category": self.category.pk,
        })

        note = Note.objects.get(title="Нова нотатка")
        self.assertEqual(note.user, self.user)

    def test_cannot_view_foreign_note_detail(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("note_detail", args=[self.foreign_note.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_edit_foreign_note(self):
        self.client.login(username="alice", password="pass12345")
        self.client.post(reverse("note_detail", args=[self.foreign_note.pk]), {
            "title": "Зламано!",
            "text": "...",
            "reminder": "",
            "category": self.category.pk,
        })

        self.foreign_note.refresh_from_db()
        self.assertEqual(self.foreign_note.title, "Чужа нотатка")  # не змінилось

    def test_cannot_delete_foreign_note(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.post(reverse("note_delete", args=[self.foreign_note.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Note.objects.filter(pk=self.foreign_note.pk).exists())

    def test_own_note_delete_works(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.post(reverse("note_delete", args=[self.my_note.pk]))

        self.assertRedirects(response, reverse("notes_list"))
        self.assertFalse(Note.objects.filter(pk=self.my_note.pk).exists())

    def test_logout_redirects_to_notes_list(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("notes_list"))
