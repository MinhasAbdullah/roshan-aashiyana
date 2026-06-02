from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('listings/', views.listings, name='listings'),
    path('check-cnic/', views.check_cnic, name='check_cnic'),
    path('property/<int:id>/<slug:slug>/', views.property_detail, name='property_detail'),
    path('about/', views.about, name='about'),
    path('register/',views.SignUp, name='SignUp'),
    path('login/', views.SignIn, name='SignIn'),
    path('logout/', views.logout_user, name='logout'),
    path('add_favourite/<int:id>/<slug:slug>/', views.add_favourite, name='add_favourite'),
    path('favourites/', views.favourites, name='favourites'),
    path('dealer_register/', views.dealer_register, name='dealer_register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_property/', views.add_property, name='add_property'),
    path('my_listings', views.my_listings, name='my_listings'),
    path('edit/<int:id>/<slug:slug>/', views.edit_property, name='edit_property'),
    path('delete/<int:id>/<slug:slug>/', views.delete_property, name='delete_property'),
    path('dealer_inquiries/', views.dealer_inquiries, name='dealer_inquiries'),
    path('dealer_reviews/', views.dealer_reviews, name='dealer_reviews'),
    path('verify-email/<uidb64>/<token>/',views.verify_email,name='verify_email'),
    path("autocomplete/", views.autocomplete, name="autocomplete"),
    path('dealers/', views.dealers, name='dealers'),
    path('dealer_profile/<int:id>/', views.dealer_profile, name='dealer_profile'),
]

