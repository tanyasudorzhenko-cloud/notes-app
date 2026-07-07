from django.urls import path
from . import views

urlpatterns = [
    path('', views.notes_list, name='notes_list'),
    path('hello/', views.hello_notes, name='hello_notes'),
]