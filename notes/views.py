from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NoteForm
from .models import Category, Note


async def hello_notes(request):
    return HttpResponse("Hello from Notes app.")


@login_required
async def notes_list(request):
    user = await request.auser()  # асинхронне отримання поточного користувача

    notes_qs = Note.objects.select_related("category").filter(user=user)

    selected_category = request.GET.get("category", "")
    if selected_category:
        notes_qs = notes_qs.filter(category_id=selected_category)

    search_query = request.GET.get("q", "")
    if search_query:
        notes_qs = notes_qs.filter(title__icontains=search_query)

    reminder_date = request.GET.get("reminder_date", "")
    if reminder_date:
        notes_qs = notes_qs.filter(reminder__date=reminder_date)

    notes = [note async for note in notes_qs]
    categories = [category async for category in Category.objects.all()]

    context = {
        "notes": notes,
        "categories": categories,
        "selected_category": selected_category,
        "search_query": search_query,
        "reminder_date": reminder_date,
    }
    return await sync_to_async(render)(request, "notes/notes_list.html", context)


@login_required
async def note_create(request):
    user = await request.auser()

    if request.method == "POST":
        form = NoteForm(request.POST)
        is_valid = await sync_to_async(form.is_valid)()
        if is_valid:
            note = form.save(commit=False)
            note.user = user
            await note.asave()
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm()

    return await sync_to_async(render)(request, "notes/note_form.html", {"form": form})


@login_required
async def note_detail(request, pk):
    user = await request.auser()

    note = await sync_to_async(get_object_or_404)(
        Note.objects.select_related("category"), pk=pk, user=user
    )

    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        is_valid = await sync_to_async(form.is_valid)()
        if is_valid:
            await sync_to_async(form.save)()
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm(instance=note)

    return await sync_to_async(render)(request, "notes/note_detail.html", {"note": note, "form": form})


@login_required
async def note_delete(request, pk):
    user = await request.auser()

    note = await sync_to_async(get_object_or_404)(
        Note.objects.select_related("category"), pk=pk, user=user
    )

    if request.method == "POST":
        await note.adelete()
        return redirect("notes_list")

    return await sync_to_async(render)(request, "notes/note_confirm_delete.html", {"note": note})
