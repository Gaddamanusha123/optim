from django.urls import path
from . import views

urlpatterns = [
    path("signup", views.signup),
    path("login", views.login),
    path("add-train", views.add_train),
    path("search", views.search_trains),
    path("availability/<int:train_id>", views.check_availability),

    path("pay", views.pay),
    path("book", views.book_ticket),
    path("booking/<int:id>", views.booking_details),
    path("booking/<int:id>/cancel", views.cancel_booking),
]
