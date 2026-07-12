from django.http import HttpResponse
from django.shortcuts import render

from .models import Note


def hello_notes(request):
    return HttpResponse("Hello from Notes app.")


def notes_list(request):
    notes = Note.objects.select_related("category").all()
    return render(request, "notes/notes_list.html", {"notes": notes})
