from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.notes_list, name='notes_list'),
    path('hello/', views.hello_notes, name='hello_notes'),
    path('create/', views.note_create, name='note_create'),
    path('<int:pk>/', views.note_detail, name='note_detail'),
    path('<int:pk>/delete/', views.note_delete, name='note_delete'),

    path(
        'login/',
        auth_views.LoginView.as_view(template_name='notes/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
