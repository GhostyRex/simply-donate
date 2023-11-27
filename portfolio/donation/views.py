from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse

# Import json.
import json

# Form import
from .forms import MoneyDonationForm, UserRegistrationForm, ContactUsForm, GiftDonationForm

# Messages import
from django.contrib import messages

# Model imports.
from .models import *

# Pagination imports.
from django.core.paginator import Paginator

# Math function imports.
from math import ceil

# Import choice from random.
from random import choice

# Stripe Payment imports.
import stripe

# Import settings.
from django.conf import settings

# PayPal imports.
from paypal.standard.forms import PayPalPaymentsForm

# Import Django decorators.
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


# Store the stripe key.
# TODO: FIX-IT; WHEN GOING TO PRODUCTIONS, STORE THE KEYS SOMEWHERE SECRET LIKE SETTINGS.PY. FIND A BETTER WAY TO HIDE
#  THIS.
stripe.api_key = settings.STRIPE_SECRET_KEY
publishableKey = settings.STRIPE_PUBLIC_KEY
webhook_secret = settings.STRIPE_WEBHOOK_SECRET


# Handle 404 pages.
def error_404_view(request, exception):
    # data = {"name": "ThePythonDjango.com"}
    # return render(request,'myapp/error_404.html', data)
    # print('404 done')
    return redirect('index')


# Function to check if a field is empty or has a value.
def empty_checker(field):
    # if the field is an empty string or the field is made of spaces, we return false.
    if not field or field.isspace():
        return False

    # If there is a value, we return True.
    return True


# This function takes in an amount of dollars and convert to cents.
def to_cents(amount):
    return int(amount * 100)


# Function sets the stripe billing status for a bill with a particular payment intent. default is true.
def setStripeBillingStatus(payment_intent, status=True):
    # TODO: FIX-IT; WHAT IF THERE IS NO BILL WITH SUCH A PAYMENT INTENT, WE DO NO UPDATE THE.
    bill = StripeBilling.objects.filter(intent_id=payment_intent).last()

    if bill:
        # Update the delivery status to true.
        bill.status = status

        # Save the updated status.
        bill.save()

        return bill

    return None


@csrf_exempt
def webhook(request):
    print('webhook time')

    endpoint_secret = webhook_secret

    payload = request.body

    # print(payload)

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), endpoint_secret
        )

    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)

    # print(event)

    # Handle the event
    if event.type == 'payment_intent.canceled' or event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object['id']  # contains a stripe.PaymentIntent

        # If failed, we set the billing status to True. This way, any new creations will be good.
        # Then define and call a method to handle the successful payment intent.
        # handle_payment_intent_succeeded(payment_intent)

        # Things important.
        # 1. amount_received
        # 2. client_secret (payment_intent)
        # 3. id (intent_id)
        # 4. payment_method "pm_1NPTQuEnc4dJKADff7OimQF2"
        # 5. payment_method_types ['card']

        # If failed, set the bill status to True.
        setStripeBillingStatus(payment_intent=payment_intent)
        print('good')

    # If the charge fails, we
    elif event.type == 'charge.failed':
        charge = event.data.object

        print(charge)

        # We get the intent id.
        payment_intent = charge['payment_intent']

        # If failed, set the bill status to True.
        setStripeBillingStatus(payment_intent=payment_intent)

        print('failed')

    elif event.type == 'charge.succeeded':
        # Things important.
        # 1. "paid": true,
        # 2. "payment_intent": "pi_3NPTj5Enc4dJKADf1ogK0gtA",
        # "amount": 10000000,
        #       "amount_captured": 10000000,
        #       "amount_refunded": 0,
        # Charge now decides if everything went well on the card. This is the important one.
        charge = event.data.object

        # We get the intent id.
        payment_intent = charge['payment_intent']

        # Now, we look if the charge is paid or not.
        if charge['paid']:
            # Get the amount paid.
            # amountPaid = to_cents(amount=charge['amount_captured'])

            print(payment_intent)
            # With the payment intent, we get the strip billing and the billing type.

            bill = setStripeBillingStatus(payment_intent=payment_intent)

            if bill:
                print('we are here')

                # TODO: FIX-IT; IF WE GET THE BILL NOW, WE DO THE NECESSARY UPDATES IN THE DB. LIKE SET THE MONEY
                #  DONATION TO TRUE.
                moneyDonation = bill.donation

                if moneyDonation:
                    moneyDonation.status = True

                    moneyDonation.save()

            else:
                print('Then there is an error of the type.')

        else:
            # If failed, set the bill status to True.
            setStripeBillingStatus(payment_intent=payment_intent)

        print(charge)

        # Failures to handle.
        # charge.failed
        # payment_intent.payment_failed

    else:
        print('Unhandled event type {}'.format(event.type))

    return HttpResponse(status=200)


@login_required
def payment_complete(request):
    # TODO: UPDATE; IF WE GET A SUCCESS FROM THE RETRIVAL, THEN WE UPDATE THE BILLING STATUS OF THAT INTENT TO TRUE.
    #  ELSE, WE REDIRECT USER BACK TO PAYMENT WITH A PAYMENT FAILURE MESSAGE.
    payment_intent = stripe.PaymentIntent.retrieve(id=request.GET['payment_intent'])

    # We need to get the state of the payment intent. If not success, and paid, then everything should just not add.
    print(payment_intent['status'])

    # From the payment intent we can get the Amount added.
    if payment_intent['status'] == 'succeeded':
        # Get the added balance from the topup.
        Billing = StripeBilling.objects.filter(intent_id=request.GET['payment_intent'], status=True).last()

        # If we get the bill, we get the amount.
        if Billing:
            context = {
                'donationAlert': Billing.amount
            }

            return render(request, 'donation/general/index.html', context=context)

    # If the intent did not succeed, we just redirect to account.
    return redirect('index')


@login_required
def create_payment_intent(request):
    # Create the payment intent here.
    if request.method == 'POST':
        # Look up the bill in db (registration, penalty, contribution) and pass in the amount.
        # Get the last entering. The bill must have a status.
        bill = StripeBilling.objects.filter(user=request.user, status=False).last()

        # If there is a no bill, we redirect back to-accounts else, we send the bills intent.
        if not bill:
            print('No Bill Found.')

            # There must be a bill for a payment to go through.
            return redirect('index')

        return JsonResponse({'clientSecret': bill.intent})

    return render(request, 'donation/account/card_payment.html')


@login_required
def card_payment(request):
    # Create the payment intent here.
    context = {
        'paymentSecret': publishableKey
    }

    return render(request, 'donation/account/card_payment.html', context=context)


@login_required
def paypal_successful(request):
    print('looking through paypal success')
    # TODO: FIX-IT; We get the payerID and use for some kind of reference.
    print(request.GET.get('PayerID'))

    # Get all the infor to display on the account general dashboard.
    context = {
        'paypal_success_escrow': True,
    }

    return render(request, 'donation/general/index.html', context=context)


@login_required
def paypal_cancelled(request):
    print(request.GET.get('PayerID'))

    context = {
        'paypal_cancelled_escrow': True,
    }

    # return render(request, "donation/cancelled.html")
    return render(request, 'donation/general/index.html', context=context)


# Create your views here.
def index(request):
    print(request.user)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('index')

        form = MoneyDonationForm(request.POST)

        if form.is_valid():
            # Do the transactions by checking if the request.user.is_authenticated. If yes, we use their details and,
            # store data in db if not, they are anonymous and, we just do the transaction.
            # print(form)
            amount = form.cleaned_data.get('amount')
            payment_method = form.cleaned_data.get('payment_method')

            print(amount)
            print(payment_method)

            # TODO: FIX-IT; AS AN AUTHENTICATED USER or ANONYMOUS USER, THE SYSTEM PICKS ANY CAUSES AT RANDOM AND
            #  YOUR DONATIONS GO TO THAT CAUSE.
            causes = Cause.objects.filter(complete=False)

            # Get the chosenCause from the list of causes.
            chosenCause = choice([x for x in causes])

            print(chosenCause)

            if chosenCause:
                # Get the payment method
                payment_method = form.cleaned_data.get('payment_method')

                # Get the payment amount.
                payment_amount = form.cleaned_data.get('amount')

                # IF THE PAYMENT METHOD IS NOT PAYPAL, THEN WE USE STRIPE ELSE, WE USE PAYPAL.
                if payment_method.method != 'paypal':
                    # TODO: FIX-IT; CHECK ALL THE STRIPE BILLS. IF THERE EXIST ONE WHICH IS THE LATEST HAVING AN
                    #  INCOMPLETE STATUS, WE UPDATE THE INTENT TO MATCH THE DETAILS.
                    bill = StripeBilling.objects.filter(user=request.user, status=False).last()

                    # If there is none of such a bill, we create a new bill.
                    if not bill:
                        # first create an intent.
                        payment_intent = stripe.PaymentIntent.create(
                            amount=to_cents(amount=payment_amount),
                            currency='usd',
                            payment_method_types=[payment_method.method],
                        )

                        donation = MoneyDonation.objects.create(
                            user=request.user, amount=payment_amount, cause=chosenCause
                        )

                        stripe_billing = StripeBilling.objects.create(
                            user=request.user, intent=payment_intent['client_secret'],
                            intent_id=payment_intent['id'],
                            method=payment_method, amount=payment_amount, donation=donation
                        )

                        # Save the both.
                        stripe_billing.save()
                        donation.save()

                    # TODO: FIX-IT; THIS IS WHERE WE CALL ON THE UPDATE TO UPDATE THE INTENT TO SOMETHING ELSE. THE AMOUNT,
                    #  METHOD ETC.
                    else:
                        try:
                            # Next we update the intent.
                            updated_payment_intent = stripe.PaymentIntent.modify(
                                sid=bill.intent_id,
                                amount=to_cents(amount=payment_amount),
                                currency='usd',
                                payment_method_types=[payment_method.method],
                            )

                            # Update a billing and their billing type.
                            bill.intent_id = updated_payment_intent.id

                            bill.intent = updated_payment_intent.client_secret

                            bill.amount = payment_amount

                            bill.method = payment_method

                            bill.created = now()

                            donation = bill.donation

                            donation.amount = payment_amount

                            # Save the updated bill.
                            donation.save()
                            bill.save()

                            # Update the billing types for that bill.
                            # Build the StripeBillingType for each data in the target data list.
                            # TODO: FIX-IT; WE CHECK IF THE BILLING TYPE ALREADY EXIST. IF SO, WE CONTINUE ELSE,
                            #  WE CREATE A NEW TYPE.

                        except stripe.error.InvalidRequestError:
                            # Reset the bill status so that a new bill can be created for a new intent.
                            bill.status = True

                            bill.save()

                            # TODO: FIX-IT; CREATE A NEW INTENT AND A NEW BILLING.
                            # first create an intent.
                            payment_intent = stripe.PaymentIntent.create(
                                amount=to_cents(amount=payment_amount),
                                currency='usd',
                                payment_method_types=[payment_method.method],
                            )

                            # Create a billing.
                            # TODO: FIX-IT; FOR THE BILLING, WE NEED TO KNOW THE STATUS. SURELY THROUGH WEBHOOKS WHEN WE RECEIVE A
                            #  `COMPLETE HAVING AN INTENT, WE UP DATE ALL THE BILLING DATABASES.
                            stripe_billing = StripeBilling.objects.create(
                                user=request.user, intent=payment_intent['client_secret'],
                                intent_id=payment_intent['id'],
                                method=payment_method, amount=payment_amount, donation=donation
                            )

                            # Save the bill.
                            stripe_billing.save()

                    return redirect('card_payment')

                else:
                    print('PayPal Method')

                    # TODO: FIX-IT; FIRST CHECK THE LATEST PAYPAL BILLING. IF NOT DELIVERED, WE UPDATE IT. IF DELIVERED,
                    #  THEN WE CREATE A NEW ONE.
                    paypalBilling = PaypalBilling.objects.filter(user=request.user, status=False).last()

                    # Update the data.
                    if paypalBilling:
                        paypalBilling.amount = payment_amount

                        paypalBilling.save()

                    # Else, create a paypal-billing.
                    else:
                        donation = MoneyDonation.objects.create(
                            user=request.user, amount=payment_amount, cause=chosenCause
                        )

                        paypalBilling = PaypalBilling.objects.create(
                            user=request.user, amount=payment_amount, donation=donation
                        )

                        # Save both.
                        donation.save()
                        paypalBilling.save()

                    # What you want the button to do.
                    paypal_dict = {
                        # Sandbox: business-email: sb-fndmn26163121@business.example.com
                        # Business pass: AiJz@E3f
                        # Soap Business pass: BL9XVB2PM7K7N3BJ

                        # Personal-email: sb-47dguz26245520@personal.example.com
                        # Personal pass: 4V,>bqDr

                        # TODO: UPDATE; PAY_ID IS GIVEN TOO. WE CAN EXTRACT THAT FROM THE GET REQUEST AND STORE
                        #  IN PAYPAL BILLING DB.
                        # http://localhost:9000/account/payments/paypal/successful/?PayerID=PE3VF55DL38V8
                        # 'payment_method': 'paypal'
                        "business": "sb-fndmn26163121@business.example.com",
                        # "personal": "godloveyufenyuy@gmail.com",
                        "amount": payment_amount,
                        "payment_method_selected": "PAYPAL",
                        "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                        "item_name": ["donation-" + str(paypalBilling.id)],  # Item name should be a list.
                        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
                        "return": request.build_absolute_uri(reverse('paypal_successful')),
                        "cancel_return": request.build_absolute_uri(reverse('paypal_cancelled')),
                    }

                    # Create the instance.
                    form = PayPalPaymentsForm(initial=paypal_dict)

                    context = {
                        "form": form
                    }

                    return render(request, "donation/account/paypal_payment.html", context=context)

            # TODO: FIX-IT; IF ANONYMOUS, THEN WE SEND A SUCCESS MESSAGE AND RENDER INSTEAD OF REDIRECTING. PROBABLY
            #  RENDER REVERSE.
            return redirect('index')

    else:
        form = MoneyDonationForm()

    context = {
        'form': form,
    }

    return render(request, template_name='donation/general/index.html', context=context)


def register_user(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(request, "Registration Successful!")

            # return HttpResponseRedirect(reverse('login'))
            return redirect('login')

    else:
        form = UserRegistrationForm()

    context = {
        'form': form,
    }

    return render(request, template_name='register.html', context=context)


# This view renders the page of causes for anyone to choose from and donate.
def cause(request, pk=None, d_type=None):
    print(pk)
    print(d_type)
    print(request.method)
    if request.method == 'GET':
        if d_type:
            causeObject = Cause.objects.filter(pk=pk)

            if not request.user.is_authenticated:
                return redirect(request.build_absolute_uri('/')[:-1] + '#anonymous')

            # If we found a cause with the id, then we get the cause's images.
            if causeObject:
                # TODO: FIX-IT; WE NEED TO LIMIT THE DONATION TYPE TO; KIND OR GIFTS.
                if d_type == 'kind':
                    # Get the money donation form.
                    form = MoneyDonationForm()

                    # TODO: FIX-IT; RENDER THE KIND PAGE.

                    context = {
                        'cause': causeObject[0],
                        'form': form
                    }

                    return render(request, template_name='donation/general/money_donation.html', context=context)

                elif d_type == 'gift':
                    # Get the gift donation form.
                    form = GiftDonationForm()

                    form.fields['image'].label = 'Gift Image'

                    # TODO: FIX-IT; GIFTS CAN ONLY BE PAID BY REGISTERED USERS.
                    if request.user.is_authenticated:
                        # TODO: FIX-IT; RENDER THE GIFTS PAGE.
                        context = {
                            'cause': causeObject[0],
                            'form': form
                        }

                        return render(request, template_name='donation/general/gift_donation.html', context=context)

            print('Donation type is :', d_type)
        # If a particular course is asked for, we get that cause.
        elif pk:
            causeObject = Cause.objects.filter(pk=pk)

            # If we found a cause with the id, then we get the cause's images.
            if causeObject:
                causeImages = CauseImage.objects.filter(cause=causeObject[0])

                # Counter for the image position in images dictionary.
                imageCounter = 0

                # Let images be an empty dictionary.
                images = {}

                # Display the first 4 latest.
                for causeImage in causeImages[::-1]:
                    images[imageCounter] = '/media/' + str(causeImage.image)

                    imageCounter += 1

                    """# We limit to only 4 displays.
                    if imageCounter > 4:
                        break"""

                # Put the first image and link the rest to it.
                # TODO: FIX-IT; THE NUMBER OF IMAGES HAS A PROBLEM. ENSURE THEY ARE 3 AT LEAST.
                """images = {
                    str(causeImages[0].id): {
                        '0': '/media/' + str(causeImages[0].image),
                        '1': '/media/' + str(causeImages[1].image),
                        '2': '/media/' + str(causeImages[2].image),
                    }
                }"""

                print(images)

                # input('images printer')

                context = {
                    'cause': causeObject[0],
                    'images': images
                }

                # Render cause.html for a particular cause.
                return render(request, template_name='donation/general/cause.html', context=context)

        else:
            # Get all the Causes and filter them by order. Make sure the latest causes come first.
            causeObject = Cause.objects.filter().order_by('id')

            # We need to build a data dictionary having the cause and it's pictures linked. We need just the first picture
            # of each cause.
            dataDictionary = {}

            # For each cause, we get the first image and put it together with the cause.
            for eachCause in causeObject:
                causeImage = CauseImage.objects.filter(cause=eachCause)

                if causeImage:
                    firstImage = causeImage[0]

                    # Build the data dict now.
                    dataDictionary[str(eachCause.id)] = {
                        'cause': eachCause,
                        'img': firstImage
                    }

            # If there was data collected into the dataDictionary, we paginate and pass the data to the cause template.
            if dataDictionary:
                print(dataDictionary)

                # We paginate through the causeObject and use the id to access the datadictionary.
                # Create paginator for the gotten members.
                # 2. We need to split the images into grids of 3. i.e. each row having 3 columns.
                obj_length = len(causeObject)

                # Round up if there are extra gallery that don't make up the 3 column sequence
                num_rows = ceil(obj_length / 3)

                temp_list = []

                obj_list = []

                reversed_obj = list(reversed(causeObject))

                # Get the images in list of 3.
                for i in range(obj_length):
                    temp_list.append(reversed_obj[i])

                    if (i + 1) % 3 == 0 and i + 1 > 2:
                        obj_list.append(temp_list)

                        temp_list = []

                # If there is still some last images that did not round up to 3, then we add them.
                if temp_list:
                    obj_list.append(temp_list)
                    
                # Here, we use 3 since the videos come in sets of 3's.
                paginator = Paginator(obj_list, 10)  # Show 50 contacts per page.

                page_number = request.GET.get("page")

                page_obj = paginator.get_page(page_number)
                # End paginator.

                # Build the context.
                context = {
                    'page_obj': page_obj,
                    'rows': range(num_rows),
                    'dataDictionary': dataDictionary,
                }

                # Render causes.html for all causes.
                return render(request, template_name='donation/general/causes.html', context=context)

    elif request.method == 'POST':
        print('posting')
        print(pk)
        print(d_type)
        if d_type == 'kind':
            form = MoneyDonationForm(request.POST)

        else:
            form = GiftDonationForm(request.POST)

            form.fields['image'].label = 'Gift Image'

        # TODO: FIX-IT; Do the payment here. Stripe or PayPal.
        if form.is_valid():

            if d_type == 'kind':
                # TODO: FIX-IT; IF THE USER IS AUTHENTICATED, THEN USER = REQUEST.USER IF NOT, WE SET USER TO THE
                #  ANONYMOUS USER AND USE THE ID 0. FIND A BETTER WAY TO HANDLE THIS.
                print(request.POST)
                print(pk)
                print('yup')

                # Get the payment method
                payment_method = form.cleaned_data.get('payment_method')

                # Get the payment amount.
                payment_amount = form.cleaned_data.get('amount')

                # Max amount should be 950K.
                if payment_amount > 950000:
                    form.add_error('amount', 'Amount should not be greater than $950,000.00')

                elif payment_amount < 1:
                    form.add_error('amount', 'Amount should not be less than $1.00')

                # IF THE PAYMENT METHOD IS NOT PAYPAL, THEN WE USE STRIPE ELSE, WE USE PAYPAL.
                elif payment_method.method != 'paypal':
                    # TODO: FIX-IT; CHECK ALL THE STRIPE BILLS. IF THERE EXIST ONE WHICH IS THE LATEST HAVING AN
                    #  INCOMPLETE STATUS, WE UPDATE THE INTENT TO MATCH THE DETAILS.
                    bill = StripeBilling.objects.filter(user=request.user, status=False).last()

                    # If there is none of such a bill, we create a new bill.
                    if not bill:
                        # first create an intent.
                        payment_intent = stripe.PaymentIntent.create(
                            amount=to_cents(amount=payment_amount),
                            currency='usd',
                            payment_method_types=[payment_method.method],
                        )

                        # Create a billing.
                        # TODO: FIX-IT; FOR THE BILLING, WE NEED TO KNOW THE STATUS. SURELY THROUGH WEBHOOKS WHEN WE RECEIVE A
                        #  `COMPLETE HAVING AN INTENT, WE UP DATE ALL THE BILLING DATABASES.

                        # TODO: FIX-IT; CREATE THE DONATION FOR THAT BILLING.
                        causeObject = Cause.objects.filter(pk=pk).last()

                        # If we found a cause with the id, then we get the cause's images.
                        if causeObject:
                            donation = MoneyDonation.objects.create(
                                user=request.user, amount=payment_amount, cause=causeObject
                            )

                            stripe_billing = StripeBilling.objects.create(
                                user=request.user, intent=payment_intent['client_secret'], intent_id=payment_intent['id'],
                                method=payment_method, amount=payment_amount, donation=donation
                            )

                            # Save the both.
                            stripe_billing.save()
                            donation.save()

                        # If we cannot get the cause we are donating for, then we redirect to index.
                        else:
                            return redirect('index')

                    # TODO: FIX-IT; THIS IS WHERE WE CALL ON THE UPDATE TO UPDATE THE INTENT TO SOMETHING ELSE. THE AMOUNT,
                    #  METHOD ETC.
                    else:
                        try:
                            # Next we update the intent.
                            updated_payment_intent = stripe.PaymentIntent.modify(
                                sid=bill.intent_id,
                                amount=to_cents(amount=payment_amount),
                                currency='usd',
                                payment_method_types=[payment_method.method],
                            )

                            # Update a billing and their billing type.
                            bill.intent_id = updated_payment_intent.id

                            bill.intent = updated_payment_intent.client_secret

                            bill.amount = payment_amount

                            bill.method = payment_method

                            bill.created = now()

                            donation = bill.donation

                            donation.amount = payment_amount

                            # Save the updated bill.
                            donation.save()
                            bill.save()

                            # Update the billing types for that bill.
                            # Build the StripeBillingType for each data in the target data list.
                            # TODO: FIX-IT; WE CHECK IF THE BILLING TYPE ALREADY EXIST. IF SO, WE CONTINUE ELSE,
                            #  WE CREATE A NEW TYPE.

                        except stripe.error.InvalidRequestError:
                            # Reset the bill status so that a new bill can be created for a new intent.
                            bill.status = True

                            bill.save()

                            # TODO: FIX-IT; CREATE A NEW INTENT AND A NEW BILLING.
                            # first create an intent.
                            payment_intent = stripe.PaymentIntent.create(
                                amount=to_cents(amount=payment_amount),
                                currency='usd',
                                payment_method_types=[payment_method.method],
                            )

                            # Create a billing.
                            # TODO: FIX-IT; FOR THE BILLING, WE NEED TO KNOW THE STATUS. SURELY THROUGH WEBHOOKS WHEN WE RECEIVE A
                            #  `COMPLETE HAVING AN INTENT, WE UP DATE ALL THE BILLING DATABASES.
                            stripe_billing = StripeBilling.objects.create(
                                user=request.user, intent=payment_intent['client_secret'], intent_id=payment_intent['id'],
                                method=payment_method, amount=payment_amount, donation=donation
                            )

                            # Save the bill.
                            stripe_billing.save()

                    return redirect('card_payment')

                else:
                    print('PayPal Method')

                    # TODO: FIX-IT; FIRST CHECK THE LATEST PAYPAL BILLING. IF NOT DELIVERED, WE UPDATE IT. IF DELIVERED,
                    #  THEN WE CREATE A NEW ONE.
                    paypalBilling = PaypalBilling.objects.filter(user=request.user, status=False).last()

                    # Update the data.
                    if paypalBilling:
                        paypalBilling.amount = payment_amount

                        paypalBilling.save()

                    # Else, create a paypal-billing.
                    else:
                        # TODO: FIX-IT; CREATE THE DONATION FOR THAT BILLING.
                        causeObject = Cause.objects.filter(pk=pk).last()

                        # If we found a cause with the id, then we get the cause's images.
                        if causeObject:
                            donation = MoneyDonation.objects.create(
                                user=request.user, amount=payment_amount, cause=causeObject
                            )

                            paypalBilling = PaypalBilling.objects.create(
                                user=request.user, amount=payment_amount, donation=donation
                            )

                            # Save both.
                            donation.save()
                            paypalBilling.save()

                        # If we cannot get the cause we are donating for, then we redirect to index.
                        else:
                            return redirect('index')

                    # What you want the button to do.
                    paypal_dict = {
                        # Sandbox: business-email: sb-fndmn26163121@business.example.com
                        # Business pass: AiJz@E3f
                        # Soap Business pass: BL9XVB2PM7K7N3BJ

                        # Personal-email: sb-47dguz26245520@personal.example.com
                        # Personal pass: 4V,>bqDr

                        # TODO: UPDATE; PAY_ID IS GIVEN TOO. WE CAN EXTRACT THAT FROM THE GET REQUEST AND STORE
                        #  IN PAYPAL BILLING DB.
                        # http://localhost:9000/account/payments/paypal/successful/?PayerID=PE3VF55DL38V8
                        # 'payment_method': 'paypal'
                        "business": "sb-fndmn26163121@business.example.com",
                        # "personal": "godloveyufenyuy@gmail.com",
                        "amount": payment_amount,
                        "payment_method_selected": "PAYPAL",
                        "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                        "item_name": ["donation-" + str(paypalBilling.id)],  # Item name should be a list.
                        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
                        "return": request.build_absolute_uri(reverse('paypal_successful')),
                        "cancel_return": request.build_absolute_uri(reverse('paypal_cancelled')),
                    }

                    # Create the instance.
                    form = PayPalPaymentsForm(initial=paypal_dict)

                    context = {
                        "form": form
                    }

                    return render(request, "donation/account/paypal_payment.html", context=context)

            elif d_type == 'gift':
                print('We post for gift donations!')

                # TODO: FIX-IT; SEND EMAIL WITH THE RELEVANT DETAILS, WE INPUT THE RELEVANT DETAILS IN THE DB.

        # Get the cause.
        causeObject = Cause.objects.filter(pk=pk)

        # If we found a cause with the id, then we get the cause's images.
        if causeObject:
            context = {
                'cause': causeObject[0],
                'form': form
            }

            if d_type == 'kind':
                return render(request, template_name='donation/general/money_donation.html', context=context)

            else:
                return render(request, template_name='donation/general/gift_donation.html', context=context)

    # If no causes to render, redirect home.
    # Rather than redirect to index, we render causes but with an info alert saying no causes yet available.
    return redirect('index')


def contact_us(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)

        if form.is_valid():
            # First we put protection against the text size.
            name = form.cleaned_data.get('name')
            email = form.cleaned_data.get('email')
            subject = form.cleaned_data.get('subject')
            message = form.cleaned_data.get('message')

            if len(message) > 1000:
                form.add_error('message', 'Size is too long. Message should be no more than 1000 characters!')

            else:
                # We send the email.
                # TODO: FIX-IT; ADD THE EMAIL SERVERs AND THE REST.
                pass

    else:
        form = ContactUsForm()

    context = {
        'form': form,
    }

    return render(request, template_name='donation/general/contact_us.html', context=context)


def about_us(request):
    return render(request, template_name='donation/general/about_us.html')


@login_required
def account(request):
    context = {
        'balance': 1000,
    }

    return render(request, "donation/account/account.html", context=context)


def flip_box(request):
    context = {
        'flip': 'flip',
    }

    return render(request, "donation/general/flip_box.html", context=context)


def portfolio(request):
    context = {

    }

    return render(request, "donation/general/portfolio.html", context=context)
