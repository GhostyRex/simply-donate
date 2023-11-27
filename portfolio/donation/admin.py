from django.contrib import admin
from .models import *


# Register your models here.

@admin.register(MoneyDonation)
class MoneyDonationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "status", "created",)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "method",)


@admin.register(GiftDonation)
class GiftDonationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "image", "status", "created",)


@admin.register(Cause)
class CauseAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "description",)


@admin.register(CauseImage)
class CauseImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'cause',)


@admin.register(StripeBilling)
class StripeBillingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'donation', 'intent', 'intent_id', 'method', 'amount', 'status', 'created',)


@admin.register(PaypalBilling)
class PaypalBillingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'donation', 'amount', 'status', 'created',)
