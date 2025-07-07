from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    #View allo user per accedere all'assistenza (sotto il profilo)
    path("assistenza/", views.user_chat, name="user_chat"),

    #View dello staff per accedere alle chat di assistenza (tramite menù per loro)
    path("staff/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/chat/", views.staff_chat_with_user, name="staff_chat"),
]
