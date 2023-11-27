# from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.views.decorators.csrf import csrf_exempt
from django.dispatch import receiver
from .models import *

# String manipulation import
from ast import literal_eval


@csrf_exempt
@receiver(valid_ipn_received)
def webhook(sender, **kwargs):
    ipn_obj = sender
    # print('this is a hook')
    # print(ipn_obj.payer_id)  # paypalipn
    # print(ST_PP_COMPLETED)  # paypalipn

    # TODO: FIX-IT; IF THE STATUS IS COMPLETED, WE DO THE COMPLETED STUFF.
    # if ipn_obj.payment_status.upper() == 'COMPLETED' or ipn_obj.payment_status == ST_PP_COMPLETED:
    if ipn_obj.payment_status.upper() == 'COMPLETED':
        # print(ipn_obj.item_name)
        # print(type(ipn_obj.item_name))
        # input('hook paused')

        # Convert the item name list from a string-list to a normal list.
        itemNameList = literal_eval(ipn_obj.item_name)

        # print(itemNameList)

        # for each item in the item list, we work on the billing and transaction validation.
        for itemName in itemNameList:
            (item, billingID) = itemName.split('-')

            # Convert the id to an integer.
            billingID = int(billingID)

            # print(billingID)

            # Get the bill.
            bill = PaypalBilling.objects.filter(id=billingID).last()

            # If the bill, then we are ok.
            if bill:
                # Use the item to find out what type of transaction it was for.
                # If t for topup transaction.
                if item == 'donation':
                    # We need now to find the family of the man who got billed.
                    # Since it is top up, the bill's billing_type_id == Family_id.
                    donation = bill.donation

                    bill.status = True
                    donation.status = True

                    # Save the balance in.
                    bill.save()
                    donation.save()

                    print('Donation created')

                else:
                    print('no transaction.')
            else:
                print('no bill bad for us!')

    return
