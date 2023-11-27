from django.db import models
from django.contrib.auth.models import User

# Time import.
from django.utils.timezone import now


PAYMENT_METHOD_CHOICES = (
    ('card', 'Card'),
    ('cashapp', 'CashApp'),
    ('paypal', 'PayPal'),
)

DONATION_CHOICES = (
    ('kind', 'Kind'),
    ('gift', 'Gift'),
    ('both', 'Both'),
)

# Type comes from a list of ['contribution', 'penalty','registration' 'cpr(all of the previous 3)', 'topup']
BILLING_TYPE_CHOICES = (
    ('stripe', 'STRIPE'),
    ('paypal', 'PAYPAL'),
    # ('escrow', 'ESCROW'),
)


# Stores the phone number of the user upon registration.
class Phone(models.Model):
    phone = models.CharField("Phone Number", max_length=20)

    user = models.ForeignKey(User, on_delete=models.CASCADE)


# Methods of payment. Could be added by the admin.
class PaymentMethod(models.Model):
    # The payment method.
    method = models.CharField("Payment Methods", max_length=15, choices=PAYMENT_METHOD_CHOICES, default='card')

    # Foreign key that extends from the User model.
    # Here, the user is the one who added the members to the family.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.method}"


# Model to contain all the causes.
class Cause(models.Model):
    # The user who creates a cause.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # TODO: FIX-IT; WE NEED TO SET THE IMAGE DIRECTORY TO STORE THE DONATED GIFT'S IMAGE.
    # image = models.ImageField(upload_to='causes')
    # Title of the cause
    title = models.CharField("Title", max_length=50)

    # TODO: FIX-IT; ENSURE THE USER KNOWS THE MAX LENGTH OF THE DESCRIPTION. DISPLAY IT AS THEY ALWAYS DO AT THE
    #  BOTTOM AND COUNT IT WITH JAVASCRIPT AS YOU COUNT THE PASSWORD LENGTH.
    #  The text box should also stop accepting text after the limit has been reached.
    description = models.CharField("Description", max_length=500)

    # User states the donation choices the cause will accept.
    donation_type = models.CharField("Donation Type", max_length=15, choices=DONATION_CHOICES, default='kind')

    # False means the donation is still active.
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}"


# Donation class to store all the donation amounts done by a user.
class MoneyDonation(models.Model):
    # The user who donates.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # The cause that the image is linked to.
    cause = models.ForeignKey(Cause, on_delete=models.CASCADE)

    # When the user pays through a payment gateway, the amount is inputted. Accept only dollars.
    amount = models.DecimalField("Amount ($)", max_digits=64, decimal_places=2, default=0, blank=True, null=True)

    status = models.BooleanField('Arrival', default=False)

    # The date the donation was made
    created = models.DateTimeField('Date', default=now)

    def __str__(self):
        return f"{self.cause}"


# TODO: FIX-IT; GIFT DONATION NEEDS MORE DATA. LIKE SENDING FROM WHERE, BY WHO, PHONE NUMBER, EMAIL ETC.
#  SHIPPING DETAILS.
# Donation class to store the gift donation pledges given by the user.
class GiftDonation(models.Model):
    # The user who donates.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # The cause that the image is linked to.
    cause = models.ForeignKey(Cause, on_delete=models.CASCADE)

    # The image of the gift donated.
    # TODO: FIX-IT; WE NEED TO SET THE IMAGE DIRECTORY TO STORE THE DONATED GIFT'S IMAGE.
    image = models.ImageField(upload_to='gifts')

    # States if the gift donation has arrived or not. This can be manipulated by the admin user.
    status = models.BooleanField('Arrival', default=False)

    # The date the donation pledge was made.
    created = models.DateTimeField('Date', default=now)

    # TODO: FIX-IT; SHOULD THERE BE AN ARRIVAL DATE. DEFAULT TO PROBABLY NONE OR EMPTY.
    # arrival = models.DateTimeField('Date', default=now)

    def __str__(self):
        return f"{self.user.username}"


# model linked to cause with one cause having more than one image.
class CauseImage(models.Model):
    # The image associated to the cause.
    image = models.ImageField(upload_to='causes')

    # The cause that the image is linked to.
    cause = models.ForeignKey(Cause, on_delete=models.CASCADE)

    # TODO: FIX-IT; We need to overwrite the original save to save the image in a particular size, keeping
    #  100% of the quality.


class StripeBilling(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Get the money donation.
    donation = models.ForeignKey(MoneyDonation, on_delete=models.CASCADE)

    # The payment intent stripe uses to track data.
    intent = models.CharField("Payment Intent Secret", max_length=100)

    # The id is used to retrieve the intents.
    intent_id = models.CharField("Payment Intent ID", max_length=100)

    # The payment method used.
    method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)

    # The amount transacted.
    amount = models.DecimalField("Amount", max_digits=64, decimal_places=2, default=0, blank=True, null=True)

    # The status of the Billing. The says if it was delivered to stripe or not. Kind of like the delivery report for
    # the bill.
    status = models.BooleanField('Delivery', default=False)

    # The date the bill was made/updated.
    created = models.DateTimeField('Date', default=now)

    def __str__(self):
        return f"{self.intent}"


class PaypalBilling(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Get the money donation.
    donation = models.ForeignKey(MoneyDonation, on_delete=models.CASCADE)

    # The amount transacted.
    amount = models.DecimalField("Amount", max_digits=64, decimal_places=2, default=0, blank=True, null=True)

    # The status of the Billing. The says if it was delivered to stripe or not. Kind of like the delivery report for
    # the bill.
    status = models.BooleanField('Delivery', default=False)

    # The date the bill was made/updated.
    created = models.DateTimeField('Date', default=now)
