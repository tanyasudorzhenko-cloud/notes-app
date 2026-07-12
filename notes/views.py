from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .models import Note, Category
from .forms import NoteForm


def hello_notes(request):
    return HttpResponse("Hello from Notes app.")


def notes_list(request):
    notes = Note.objects.select_related("category").all()

    selected_category = request.GET.get("category", "")
    if selected_category:
        notes = notes.filter(category_id=selected_category)

    search_query = request.GET.get("q", "")
    if search_query:
        notes = notes.filter(title__icontains=search_query)

    reminder_date = request.GET.get("reminder_date", "")
    if reminder_date:
        notes = notes.filter(reminder__date=reminder_date)

    context = {
        "notes": notes,
        "categories": Category.objects.all(),
        "selected_category": selected_category,
        "search_query": search_query,
        "reminder_date": reminder_date,
    }
    return render(request, "notes/notes_list.html", context)


def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save()
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm()

    return render(request, "notes/note_form.html", {"form": form})


def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm(instance=note)

    return render(request, "notes/note_detail.html", {"note": note, "form": form})


def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if request.method == "POST":
        note.delete()
        return redirect("notes_list")

    return render(request, "notes/note_confirm_delete.html", {"note": note})
