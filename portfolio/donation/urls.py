from django.urls import path, include
from .import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Navigation.
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('register/', views.register_user, name='register'),

    # The path to all causes.
    path('cause/', views.cause, name='cause'),
    path('cause/<int:pk>/', views.cause, name='cause'),
    path('cause/<int:pk>/<slug:d_type>/', views.cause, name='cause'),

    # Payment Routes.
    path('payments/checkout/', views.card_payment, name='card_payment'),
    path('payments/checkout/create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('payments/checkout/complete/', views.payment_complete, name='payment_complete'),
    path('payments/checkout/webhook/', views.webhook, name='webhook'),

    # PayPal Routes.
    path('payments/paypal/cancelled/', views.paypal_cancelled, name='paypal_cancelled'),
    path('payments/paypal/successful/', views.paypal_successful, name='paypal_successful'),
    # path('account/payments/paypal-payment/', views.affuadusa_paypal_payment, name='affuadusa_paypal_payment'),
    path('paypal/', include("paypal.standard.ipn.urls")),

    # Contact Us.
    path('contact-us/', views.contact_us, name='contact_us'),
    path('about-us/', views.about_us, name='about_us'),

    # Account paths.
    path('account/', views.account, name='account'),
]
