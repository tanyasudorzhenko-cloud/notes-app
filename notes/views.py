from django.http import HttpResponse
from django.shortcuts import render

def hello_notes(request):
    return HttpResponse("Hello from Notes app.")

def notes_list(request):
    notes = [
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
    return render(request, "notes/notes_list.html", {"notes": notes})
