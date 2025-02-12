import openpyxl
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, reverse, redirect, get_object_or_404

from consign_app.models import Login,Collection,DeleteConsignment,DriverLocation,Location,UserLogin, AddConsignment,AddConsignmentTemp,Disel, AddTrack,FeedBack,Debitledger,Creditledger, Branch,Driver,Vehicle, Staff,Consignee, Consignor,TripSheetTemp,TripSheetPrem, Account,Expenses
#from django.core.mail import send_mail


import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, Http404

import datetime
import random
import string
import secrets
import pprint

from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
from consign.settings import BASE_DIR
from django.db.models import Q, Max, Min, Subquery
from django.contrib import messages
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.http import require_POST
from django.db.models import Count
from datetime import datetime
from django.core.exceptions import ValidationError
from decimal import Decimal

from django.db.models.functions import Concat
from django.db import connection, IntegrityError




#import datetime
#from .models import AddTrack, AddConsignment


import requests
from io import BytesIO
from django.core.files import File

from django.core.files.base import ContentFile
from django.conf import settings  # Ensure MEDIA_ROOT is configured



# Initialize Razorpay client with your API keys


from django.contrib.auth.models import User

from django.views.generic import TemplateView
class OfflineView(TemplateView):
    template_name = 'offline.html'

# Create your views here.
def index(request):
    return render(request,'index.html')



def feedback(request):
    uid = request.session.get('username')
    if not uid:
        return redirect('login')  # Redirect to login if session does not have username

    # Fetch only the receiver_email column
    userdata = AddConsignment.objects.filter(receiver_email=uid).values_list('receiver_email', flat=True)

    if request.method == "POST":
        feed = request.POST.get('feedback')

        if userdata.exists():
            username = userdata[0]  # Extract the first email from the list

            FeedBack.objects.create(
                username=username,
                feedback=feed
            )
            messages.success(request, 'Feedback sent successfully')
            return redirect('feedback')
        else:
            messages.error(request, 'User not found')
            return render(request, 'feedback.html')

    return render(request, 'feedback.html')

def view_feedback(request):
    userdata=FeedBack.objects.all()
    return render(request,'view_feedback.html',{'userdata':userdata})

def staff_home(request):
    return render(request,'staff_home.html')

def staff_nav(request):
    return render(request,'staff_nav.html')

def index_menu(request):
    return render(request,'index_menu.html')

def admin_home(request):
    return render(request,'admin_home.html')

def user_home(request):
    return render(request,'user_home.html')

def user_home(request):
    return render(request,'user_home.html')

def user_menu(request):
    return render(request,'user_menu.html')

def nav(request):
    return render(request,'nav.html')

def branch_home(request):
    return render(request,'branch_home.html')
def staff_home(request):
    return render(request,'staff_home.html')
def userlogin(request):
    if request.method=="POST":
        username=request.POST.get('t1')
        password=request.POST.get('t2')
        request.session['username']=username
        ucount=Login.objects.filter(username=username).count()
        if ucount>=1:
            udata = Login.objects.get(username=username)
            upass = udata.password
            utype=udata.utype
            if password == upass:
                request.session['utype'] = utype
                if utype == 'user':
                    return render(request,'user_home.html')
                if utype == 'admin':
                    return render(request,'admin_home.html')
                if utype == 'branch':
                    return render(request,'branch_home.html')
                if utype == 'staff':
                    return render(request,'staff_home.html')
                if utype == 'driver':
                    return redirect('location')
            else:
                return render(request,'userlogin.html',{'msg':'Invalid Password'})
        else:
            return render(request,'userlogin.html',{'msg':'Invalid Username'})
    return render(request,'userlogin.html')


from django.db.models import Max
from django.db import transaction
def addConsignment(request):
    if request.method == "POST":
        now = datetime.now().replace(microsecond=0)
        con_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")

        uid = request.session.get('username')
        branch = Staff.objects.get(staffPhone=uid)
        uname = branch.Branch
        branchemail = branch.branchemail
        username = branch.staffname


        # Get the last track_id and increment it
        last_track_id = AddConsignment.objects.aggregate(Max('track_id'))['track_id__max']
        track_id = int(last_track_id) + 1 if last_track_id else 1000
        con_id = str(track_id)

        # Get the last Consignment_id and increment it
        last_con_id = AddConsignment.objects.aggregate(Max('Consignment_id'))['Consignment_id__max']
        Consignment_id = last_con_id + 1 if last_con_id else 1000
        Consignment_id = str(Consignment_id)

        last_cust_id = Consignee.objects.aggregate(Max('cust_id'))['cust_id__max']
        cust_id = last_cust_id + 1 if last_cust_id else 1
        cust_id = str(cust_id)

        last_consignor_id = Consignor.objects.aggregate(Max('cust_id'))['cust_id__max']
        consignor_id = last_consignor_id + 1 if last_consignor_id else 1000
        consignor_id = str(consignor_id)

        # Sender details
        send_name = request.POST.get('a1')
        send_mobile = request.POST.get('a2')
        send_address = request.POST.get('a4')
        sender_GST = request.POST.get('sendergst')

        # Receiver details
        rec_name = request.POST.get('a5')
        rec_mobile = request.POST.get('a6')
        rec_address = request.POST.get('a8')
        rec_GST = request.POST.get('receivergst')

        # Check if the Consignor already exists
        consignor, created = Consignor.objects.get_or_create(
            sender_name=send_name,
            defaults={
                'sender_mobile': send_mobile,
                'sender_address': send_address,
                'sender_GST': sender_GST,
                'branch': uname,
                'cust_id': consignor_id  # Temporarily set cust_id to None
            }
        )

        # If the consignor was created, assign a new cust_id
        if created:
            consignor_id = consignor.cust_id  # Use the newly created cust_id
        else:
            consignor_id = consignor.cust_id  # Retain existing cust_id if not created

        # Save consignor mobile number in UserLogin table
        UserLogin.objects.update_or_create(
            email=send_mobile,  # Use sender_mobile as the unique key
            defaults={
                'username': send_name,  # Set username to sender_name
                # Add any other fields as necessary
            }
        )

        # Check if the Consignee already exists
        consignee, created = Consignee.objects.get_or_create(
            receiver_name=rec_name,
            defaults={
                'receiver_mobile': rec_mobile,
                'receiver_address': rec_address,
                'receiver_GST': rec_GST,
                'branch': uname,
                'cust_id': cust_id  # Temporarily set cust_id to None
            }
        )

        # Save consignee mobile number in UserLogin table
        UserLogin.objects.update_or_create(
            email=rec_mobile,  # Use receiver_mobile as the unique key
            defaults={
                'username': rec_name,  # Set username to receiver_name
                # Add any other fields as necessary
            }
        )

        # If the consignee was created, assign a new cust_id
        if created:
            cust_id = consignee.cust_id  # Use the newly created cust_id
        else:
            cust_id = consignee.cust_id  # Retain existing cust_id if not created

        # Handling copies
        copies = []
        if request.POST.get('consignor_copy'):
            copies.append('Consignor Copy')
        if request.POST.get('consignee_copy'):
            copies.append('Consignee Copy')
        if request.POST.get('lorry_copy'):
            copies.append('Lorry Copy')
        copy_type = ', '.join(copies)  # Combine into a single string

        # Handling product entries
        products = request.POST.getlist('product[]')
        pieces = request.POST.getlist('pieces[]')

        # Other consignment details
        delivery = request.POST.get('delivery_option')
        prod_invoice = request.POST.get('prod_invoice')
        prod_price = request.POST.get('prod_price')
        weight = float(request.POST.get('weight') or 0)
        weightAmt = float(request.POST.get('weightAmt') or 0)
        freight = float(request.POST.get('freight') or 0)
        hamali = float(request.POST.get('hamali') or 0)
        door_charge = float(request.POST.get('door_charge') or 0)
        st_charge = float(request.POST.get('st_charge') or 0)
        cost = float(request.POST.get('cost') or 0)
        bal = float(request.POST.get('balance') or 0)
        pay_status = request.POST.get('payment')
        route_from = request.POST.get('from')
        route_to = request.POST.get('to')
        eway_bill = request.POST.get('ewaybill_no')


        utype = request.session.get('utype')
        branch_value = 'admin' if utype == 'admin' else uname

        # Determine the appropriate name based on pay_status
        if pay_status == 'Consigner_AC':
            account_name = send_name

        elif pay_status == 'Consignee_AC':
            account_name = rec_name
        else:
            account_name = send_name  # Default to sender_name if pay_status is neither

        # Create consignment records
        for product, piece in zip(products, pieces):
            if not product or not piece:
                continue
            AddConsignment.objects.create(
                track_id=con_id,
                Consignment_id=Consignment_id,
                sender_name=send_name,
                sender_mobile=send_mobile,
                sender_address=send_address,
                sender_GST=sender_GST,
                receiver_name=rec_name,
                receiver_mobile=rec_mobile,
                receiver_address=rec_address,
                receiver_GST=rec_GST,
                desc_product=product,
                pieces=piece,
                prod_invoice=prod_invoice,
                prod_price=prod_price,
                weightAmt=weightAmt,
                weight=weight,
                balance=bal,
                freight=freight,
                hamali=hamali,
                door_charge=door_charge,
                st_charge=st_charge,
                route_from=route_from,
                route_to=route_to,
                total_cost=cost,
                date=con_date,
                pay_status=pay_status,
                branch=branch_value,
                name=username,
                time=current_time,
                copy_type=copy_type,
                delivery=delivery,
                eway_bill=eway_bill,
                consignment_status='Pending',
                branchemail=branchemail,
                status='Consignment Added'

            )
            AddConsignmentTemp.objects.create(
                track_id=con_id,
                Consignment_id=Consignment_id,
                sender_name=send_name,
                sender_mobile=send_mobile,
                sender_address=send_address,
                sender_GST=sender_GST,
                receiver_name=rec_name,
                receiver_mobile=rec_mobile,
                receiver_address=rec_address,
                receiver_GST=rec_GST,
                desc_product=product,
                pieces=piece,
                prod_invoice=prod_invoice,
                prod_price=prod_price,
                weightAmt=weightAmt,
                weight=weight,
                balance=bal,
                freight=freight,
                hamali=hamali,
                door_charge=door_charge,
                st_charge=st_charge,
                route_from=route_from,
                route_to=route_to,
                total_cost=cost,
                date=con_date,
                pay_status=pay_status,
                branch=branch_value,
                name=username,
                time=current_time,
                copy_type=copy_type,
                delivery=delivery,
                eway_bill=eway_bill
            )

        if pay_status in ['Consigner_AC', 'Consignee_AC']:
            try:
                # Confirm this block executes
                print(f"Attempting to save to Account with track_id {con_id}, sender_name {account_name}, cost {cost}")

                previous_balance_entry = Account.objects.filter(sender_name=account_name).order_by('-Date').first()
                previous_balance = float(previous_balance_entry.Balance) if previous_balance_entry else 0.0
                updated_balance = previous_balance + cost

                # Proceed to save/update account data
                Account.objects.update_or_create(
                    track_number=con_id,
                    defaults={
                        'sender_name': account_name,
                        'Date': now,
                        'particulars': f'LR: {con_id}',
                        'debit': cost,
                        'credit': 0,
                        'TrType': 'sal',
                        'Balance': updated_balance,
                        'headname': 'Account Receivable',
                        'Branch': uname
                    }
                )
                print(f"Successfully updated balance for {account_name}: {updated_balance}")
            except Exception as e:
                print(f"Error while saving to Account table: {e}")

        #send_jsk_message([send_mobile, rec_mobile],
                         #f"Order is confirmed with Raichur parcel service. LRno - {con_id} Sender - {send_name} Receiver - {rec_name} For more click below.https://raichurparcelservices.com/customerLogin")

        return redirect('printConsignment', track_id=con_id)

    return render(request, 'addConsignment.html')



import requests
from django.conf import settings
import urllib.parse

def send_jsk_message(phone_numbers, message):
    """Send a message using JSK Bunk API."""
    try:
        # Ensure phone_numbers is a list and join them with commas
        if isinstance(phone_numbers, list):
            phone_numbers = ','.join(phone_numbers)

        # Prepare URL-encoded message to handle spaces and special characters
        encoded_message = urllib.parse.quote(message)

        JSK_API_KEY = "4673C8B442502E"
        # Construct the API endpoint with necessary query parameters
        url = "http://103.182.103.247/app/smsapi/index.php"
        params = {
            'key': JSK_API_KEY,
            'campaign': '13937',  # Use the correct campaign ID
            'routeid': '3',  # Define the appropriate route ID
            'type': 'text',
            'contacts': phone_numbers,
            'senderid': 'RAPASE',  # Ensure this sender ID is active and correct
            'msg': encoded_message,
            'template_id': '1707173227210886975',  # Ensure template ID is correct
            'pe_id': '1701173148054888405'  # Ensure PE ID is correct
        }

        # Log the URL for debugging
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        print(f"Sending request to URL: {full_url}")

        # Send the GET request
        response = requests.get(url, params=params)

        # Check the response
        response.raise_for_status()  # Raises an error for unsuccessful requests
        print(f"Message sent to {phone_numbers}: {response.text}")

    except requests.exceptions.RequestException as e:
        # Print detailed error message for debugging
        print(f"Failed to send message to {phone_numbers}. Error: {e}")
        print("Response content:", response.content if response else "No response content")

def printConsignment(request, track_id):
    grouped_userdata = {}
    copy_types = []
    totalqty = 0  # Initialize total quantity

    try:
        consignments = AddConsignment.objects.filter(track_id=track_id)
        uid = request.session.get('username')

        staff = Staff.objects.get(staffPhone=uid)
        user_branch = staff.Branch  # Adjust if the branch info is stored differently
        branchemail = staff.branchemail
        branchdetails = Branch.objects.get(email=branchemail)

        if not consignments.exists():
            return render(request, '404.html')  # Handle case where no consignments are found.

        # Loop over each consignment item to gather details individually
        for consignment in consignments:
            if consignment.track_id not in grouped_userdata:
                # Initialize data structure for each track_id
                grouped_userdata[consignment.track_id] = {
                    field.name: getattr(consignment, field.name) for field in AddConsignment._meta.fields
                }
                grouped_userdata[consignment.track_id]['consignment_list'] = []  # To store individual products

            # Add each consignment's product details as a separate entry
            consignment_details = {
                'pieces': consignment.pieces,
                'desc_product': consignment.desc_product,

            }
            grouped_userdata[consignment.track_id]['consignment_list'].append(consignment_details)
            totalqty += consignment.pieces  # Sum up the pieces for total quantity

            if consignment.copy_type not in copy_types:
                copy_types.append(consignment.copy_type)

    except ObjectDoesNotExist:
        grouped_userdata = {}

    return render(request, 'printConsignment.html', {
        'grouped_userdata': grouped_userdata,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types),  # Include the aggregated copy types
        'totalqty': totalqty  # Pass total quantity to the template

    })



def invoiceConsignment(request, track_id):
    grouped_userdata = {}
    copy_types = []
    totalqty = 0  # Initialize total quantity

    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        # Get common details from the first consignment
        consignment = consignments.first()

        # Fetch the branch name from the consignment
        branch_name = consignment.branch  # Adjust this field based on your model
        branchemail= consignment.branchemail
        # Fetch branch details using the branch name
        branchdetails = get_object_or_404(Branch, companyname=branchemail)

        if not consignments.exists():
            return render(request, '404.html')  # Handle case where no consignments are found.

        # Loop over each consignment item to gather details individually
        for consignment in consignments:
            if consignment.track_id not in grouped_userdata:
                # Initialize data structure for each track_id
                grouped_userdata[consignment.track_id] = {
                    field.name: getattr(consignment, field.name) for field in AddConsignment._meta.fields
                }
                grouped_userdata[consignment.track_id]['consignment_list'] = []  # To store individual products

            # Add each consignment's product details as a separate entry
            consignment_details = {
                'pieces': consignment.pieces,
                'desc_product': consignment.desc_product,

            }
            grouped_userdata[consignment.track_id]['consignment_list'].append(consignment_details)
            totalqty += consignment.pieces  # Sum up the pieces for total quantity

            if consignment.copy_type not in copy_types:
                copy_types.append(consignment.copy_type)

    except ObjectDoesNotExist:
        grouped_userdata = {}

    return render(request, 'invoiceConsignment.html', {
        'grouped_userdata': grouped_userdata,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types),  # Include the aggregated copy types
        'totalqty': totalqty  # Pass total quantity to the template

    })



def view_consignment(request):
    uid = request.session.get('username')
    grouped_userdata = {}

    if uid:
        try:
            from_date_str = request.POST.get('from_date')
            to_date_str = request.POST.get('to_date')

            consigner = request.POST.get('consigner')
            consigee = request.POST.get('consignee')
            track_id = request.POST.get('lrno')

            # Parse dates
            from_date = parse_date(from_date_str) if from_date_str else None
            to_date = parse_date(to_date_str) if to_date_str else None

            # Fetch the staff and associated branch
            staff = Staff.objects.get(staffPhone=uid)
            user_branch = staff.Branch  # Adjust if the branch info is stored differently

            # Start building the query
            consignments = AddConsignment.objects.filter(branch=user_branch)

            if consigner:
                consignments = consignments.filter(sender_name=consigner)
            if consigee:
                consignments = consignments.filter(receiver_name=consigee)
            if track_id:
                consignments = consignments.filter(track_id=track_id)

            if from_date and to_date:
                consignments = consignments.filter(date__range=(from_date, to_date))
            elif from_date:
                consignments = consignments.filter(date__gte=from_date)
            elif to_date:
                consignments = consignments.filter(date__lte=to_date)

            # Group consignments by track_id and concatenate product details
            for consignment in consignments:
                track_id = consignment.track_id
                if track_id not in grouped_userdata:
                    grouped_userdata[track_id] = {
                        'route_from': consignment.route_from,
                        'route_to': consignment.route_to,
                        'sender_name': consignment.sender_name,
                        'sender_mobile': consignment.sender_mobile,
                        'receiver_name': consignment.receiver_name,
                        'receiver_mobile': consignment.receiver_mobile,
                        'total_cost': 0,
                        'pieces': 0,
                        'weight': consignment.weight,
                        'pay_status': consignment.pay_status,
                        'products': []
                    }
                # Aggregate total cost and pieces
                grouped_userdata[track_id]['total_cost'] += consignment.total_cost
                grouped_userdata[track_id]['pieces'] += consignment.pieces

                # Concatenate product details without ID
                product_detail = consignment.desc_product
                grouped_userdata[track_id]['products'].append(product_detail)

        except ObjectDoesNotExist:
            # In case of staff or branch not found, return an empty set
            grouped_userdata = {}

    # Convert the list of product details to a single string
    for track_id, details in grouped_userdata.items():
        details['products'] = ', '.join(details['products'])

    return render(request, 'view_consignment.html', {'grouped_userdata': grouped_userdata})


def user_view_consignment(request):
    uid = request.session['username']
    userdata = AddConsignment.objects.filter(receiver_email=uid).values()
    return render(request,'user_view_consignment.html',{'userdata':userdata})


def consignment_edit(request, pk):
    userdata = AddConsignment.objects.filter(id=pk).first()  # Retrieve a single object or None


    if request.method == "POST":
        track_id = userdata.track_id
        con_date = userdata.date

        send_name = request.POST.get('a1')
        send_mobile = request.POST.get('a2')
        send_email = request.POST.get('a3')
        send_address = request.POST.get('a4')

        rec_name = request.POST.get('a5')
        rec_mobile = request.POST.get('a6')
        rec_email = request.POST.get('a7')
        rec_address = request.POST.get('a8')

        cost = request.POST.get('a9')

        # Update the object
        userdata.track_no = track_id
        userdata.sender_name = send_name
        userdata.sender_mobile = send_mobile
        userdata.sender_email = send_email
        userdata.sender_address = send_address
        userdata.receiver_name = rec_name
        userdata.receiver_mobile = rec_mobile
        userdata.receiver_email = rec_email
        userdata.receiver_address = rec_address
        userdata.total_cost = cost
        userdata.date = con_date
        userdata.save()

        # Redirect to a different URL after successful update
        base_url = reverse('view_consignment')
        return redirect(base_url)

    return render(request, 'consignment_edit.html', {'userdata': userdata})


def consignment_delete(request,pk):
    udata=AddConsignment.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_consignment')
    return redirect(base_url)




def addTrack(request):
    consignments = AddConsignment.objects.all().order_by('-id')  # Fetch all consignments ordered by id descending
    if request.method == "POST":
        now = datetime.datetime.now()
        con_date = now.strftime("%Y-%m-%d")

        track_id = request.POST.get('a1')
        status = request.POST.get('status')  # Retrieve status from the form

        # Retrieve total_cost from AddConsignment table based on some condition
        # For example, you can get it based on track_id or any other criteria

        # If the selected status is "Other", retrieve the custom status from the form
        if status == "Other":
            custom_status = request.POST.get('a2')
        else:
            custom_status = None

        # Create AddTrack object with retrieved total_cost
        AddTrack.objects.create(
            track_id=track_id,
            description=status,
            date=con_date

        )

        return render(request, 'addTrack.html', {'msg': 'Added'})
    return render(request, 'addTrack.html',{'consignments':consignments})


def search_results(request):
    tracker_id = request.GET.get('tracker_id')
    consignments = AddConsignment.objects.all().order_by('-id')  # Fetch all consignment data

    if tracker_id:
        try:
            trackers = AddTrack.objects.filter(track_id=tracker_id)
            if trackers.exists():
                return render(request, 'search_results.html', {'trackers': trackers, 'consignments': consignments})
            else:
                message = f"No tracking information found for ID: {tracker_id}"
                return render(request, 'search_results.html', {'message': message, 'consignments': consignments})
        except Exception as e:
            message = f"Error occurred: {str(e)}"
            return render(request, 'search_results.html', {'message': message, 'consignments': consignments})
    else:
        return render(request, 'search_results.html', {'message': "Please enter a tracker ID.", 'consignments': consignments})



def track_delete(request,pk):
    udata=AddTrack.objects.get(id=pk)
    udata.delete()
    base_url=reverse('search_results')
    return redirect(base_url)


def user_search_results(request):
    tracker_id = request.GET.get('tracker_id')

    if tracker_id:
        try:
            trackers = AddTrack.objects.filter(track_id=tracker_id)
            if trackers.exists():
                return render(request, 'user_search_results.html', {'trackers': trackers})
            else:
                message = f"No tracking information found for ID: {tracker_id}"
                return render(request, 'user_search_results.html', {'message': message})
        except Exception as e:
            message = f"Error occurred: {str(e)}"
            return render(request, 'user_search_results.html', {'message': message})
    else:
        return render(request, 'user_search_results.html', {'message': "Please enter a tracker ID."})

def branch(request):
    if request.method == "POST":
        companyname = request.POST.get('companyname')
        headname = request.POST.get('headname')
        phonenumber = request.POST.get('phonenumber')
        email = request.POST.get('email')
        password = request.POST.get('password')
        gst = request.POST.get('gst')
        address = request.POST.get('address')
        services = request.POST.get('services')
        agency = request.POST.get('agency')

        utype = 'branch'


        if Login.objects.filter(username=email).exists():
            messages.error(request, 'Username (email) already exists.')
            return render(request, 'branch.html')

        # If the email does not exist, create the branch and login records
        Branch.objects.create(
            companyname=companyname,
            phonenumber=phonenumber,
            email=email,
            gst=gst,
            address=address,
            services=services,
            agency=agency,
            headname=headname,
            password=password
        )
        Login.objects.create(utype=utype, username=email, password=password, name=headname)

        messages.success(request, 'Branch created successfully.')

    return render(request, 'branch.html')


def addlocation(request):
    if request.method == "POST":
        location = request.POST.get('location')
        Location.objects.create(
            location=location,
        )
    return render(request,'location.html')

def view_location(request):
    data=Location.objects.all()
    return render(request,'viewLocation.html',{'data':data})

def get_location(request):
    query = request.GET.get('query', '')
    if query:
        sender_names = Location.objects.filter(location__icontains=query).values_list('location', flat=True)
        print('sender_names numbers:', list(sender_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_names), safe=False)
    return JsonResponse([], safe=False)

def location_delete(request,pk):
    udata=Location.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_location')
    return redirect(base_url)

def view_branch(request):
    data=Branch.objects.all()
    return render(request,'view_branch.html',{'data':data})

def location_delete(request,pk):
    udata=Location.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_location')
    return redirect(base_url)

def edit_branch(request, pk):
    data = Branch.objects.filter(id=pk).first()  # Retrieve a single object or None

    original_email = data.email

    if request.method == "POST":
        companyname = request.POST.get('companyname')
        headname = request.POST.get('headname')
        phonenumber = request.POST.get('phonenumber')
        email = request.POST.get('email')
        gst = request.POST.get('gst')
        address = request.POST.get('address')
        services = request.POST.get('services')
        agency = request.POST.get('agency')
        password = request.POST.get('password')

        # Update the object
        data.companyname = companyname
        data.headname = headname
        data.phonenumber = phonenumber
        data.email = email
        data.gst = gst
        data.address = address
        data.services = services
        data.agency = agency
        data.password = password
        data.save()


        # Update the Login record using the original staffPhone
        user = Login.objects.filter(username=original_email).first()  # Fetch the user with the original phone number
        if user:
            user.username = email  # Update username to the new phone number
            user.name = headname  # Update name
            user.password=password
            user.save()
        # Redirect to a different URL after successful update
        base_url = reverse('view_branch')
        return redirect(base_url)

    return render(request, 'edit_branch.html', {'data': data})

def branch_delete(request,pk):
    udata=Branch.objects.get(id=pk)
    user = Login.objects.filter(username=udata.email).first()
    if user:
        user.delete()
    udata.delete()
    base_url=reverse('view_branch')
    return redirect(base_url)

def driver(request):
    if request.method == "POST":
        driver_name = request.POST.get('driver_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        passport = request.POST.get('passport')
        license = request.POST.get('license')
        aadhar = request.POST.get('aadhar')

        passportfile = request.FILES['passport']
        fs = FileSystemStorage()
        filepassport = fs.save(passportfile.name, passportfile)
        upload_file_url = fs.url(filepassport)
        path = os.path.join(BASE_DIR, '/media/' + filepassport)

        licensefile = request.FILES['license']
        fs = FileSystemStorage()
        filelicense= fs.save(licensefile.name, licensefile)
        upload_file_url = fs.url(filelicense)
        path = os.path.join(BASE_DIR, '/media/' + filelicense)

        aadharfile = request.FILES['aadhar']
        fs = FileSystemStorage()
        fileaadhar = fs.save(aadharfile.name, aadharfile)
        upload_file_url = fs.url(fileaadhar)
        path = os.path.join(BASE_DIR, '/media/' + fileaadhar)

        Driver.objects.create(
            driver_name=driver_name,
            phone_number=phone_number,
            address=address,
            passport=passportfile,
            license=licensefile,
            aadhar=aadharfile,
            location_sharing_active='True'
        )
        Login.objects.create(
            username=phone_number,
            password=phone_number,
            utype='driver'
        )
    return render(request, 'driver.html')


def view_driver(request):
    data=Driver.objects.all()
    return render(request,'view_driver.html',{'data':data})


def driver_edit(request, pk):
    data = Driver.objects.filter(id=pk).first()  # Retrieve a single object or None


    if request.method == "POST":
        driver_name = request.POST.get('driver_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')


        # Update the object
        data.driver_name = driver_name
        data.phone_number = phone_number
        data.address = address

        data.save()

        # Redirect to a different URL after successful update
        base_url = reverse('view_driver')
        return redirect(base_url)

    return render(request, 'driver_edit.html', {'data': data})


def driver_delete(request,pk):
    udata=Driver.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_driver')
    return redirect(base_url)


def vehicle(request):
    if request.method == "POST":
        vehicle_number = request.POST.get('vehicle_number')
        rcdate = request.POST.get('rcdate')
        incurencedate = request.POST.get('incurencedate')
        permitdate = request.POST.get('permitdate')
        taxdate = request.POST.get('taxdate')
        emissiondate = request.POST.get('emissiondate')

        rcfile = request.FILES['rc']
        fs = FileSystemStorage()
        filerc = fs.save(rcfile.name, rcfile)
        upload_file_url = fs.url(filerc)
        path = os.path.join(BASE_DIR, '/media/' + filerc)

        incurencefile = request.FILES['incurence']
        fs = FileSystemStorage()
        fileincurence = fs.save(incurencefile.name, incurencefile)
        upload_file_url = fs.url(fileincurence)
        path = os.path.join(BASE_DIR, '/media/' + fileincurence)

        permitfile = request.FILES['permit']
        fs = FileSystemStorage()
        filepermit = fs.save(permitfile.name, permitfile)
        upload_file_url = fs.url(filepermit)
        path = os.path.join(BASE_DIR, '/media/' + filepermit)

        taxfile = request.FILES['tax']
        fs = FileSystemStorage()
        filetax = fs.save(taxfile.name, taxfile)
        upload_file_url = fs.url(filetax)
        path = os.path.join(BASE_DIR, '/media/' + filetax)

        emissionfile = request.FILES['emission']
        fs = FileSystemStorage()
        fileemission = fs.save(emissionfile.name, emissionfile)
        upload_file_url = fs.url(fileemission)
        path = os.path.join(BASE_DIR, '/media/' + fileemission)

        if Vehicle.objects.filter(vehicle_number=vehicle_number).exists():
            messages.error(request, 'vehicle number already exists.')
            return render(request, 'vehicle.html')

        Vehicle.objects.create(
            vehicle_number=vehicle_number,
            rccard=rcfile,
            rccardate=rcdate,
            incurencedate=incurencedate,
            incurence=incurencefile,
            permit=permitfile,
            permitdate=permitdate,
            tax=taxfile,
            taxdate=taxdate,
            emission=emissionfile,
            emissiondate=emissiondate
        )
        messages.success(request, 'Vehicle created successfully.')
    return render(request, 'vehicle.html')

from django.utils.timezone import now

def view_vehicle(request):
    today = now().date()  # Get the current date
    data = Vehicle.objects.all()

    # Add a 'days_left' attribute for each field to use in the template
    for vehicle in data:
        vehicle.rc_days_left = (vehicle.rccardate - today).days if vehicle.rccardate else None
        vehicle.insurance_days_left = (vehicle.incurencedate - today).days if vehicle.incurencedate else None
        vehicle.permit_days_left = (vehicle.permitdate - today).days if vehicle.permitdate else None
        vehicle.tax_days_left = (vehicle.taxdate - today).days if vehicle.taxdate else None
        vehicle.emission_days_left = (vehicle.emissiondate - today).days if vehicle.emissiondate else None

    return render(request, 'view_vehicle.html', {'data': data})

def vehicle_edit(request, pk):
    data = Vehicle.objects.filter(id=pk).first()  # Retrieve a single object or None


    if request.method == "POST":
        vehicle_number = request.POST.get('vehicle_number')
        rcdate = request.POST.get('rcdate')
        incurencedate = request.POST.get('incurencedate')
        permitdate = request.POST.get('permitdate')
        taxdate = request.POST.get('taxdate')
        emissiondate = request.POST.get('emissiondate')

        data.vehicle_number = vehicle_number
        data.rccardate = rcdate
        data.incurencedate = incurencedate
        data.permitdate = permitdate
        data.taxdate = taxdate
        data.emissiondate = emissiondate

        data.save()

        # Redirect to a different URL after successful update
        base_url = reverse('view_vehicle')
        return redirect(base_url)

    return render(request, 'vehicle_edit.html', {'data': data})


def vehicle_delete(request,pk):
    udata=Vehicle.objects.get(id=pk)
    udata.delete()
    base_url=reverse('view_vehicle')
    return redirect(base_url)

def get_account_name(request):
    query = request.GET.get('query', '')
    if query:
        sender_names = Account.objects.filter(sender_name__icontains=query).values_list('sender_name', flat=True).distinct()
        print('sender_names numbers:', list(sender_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_names), safe=False)
    return JsonResponse([], safe=False)

def get_consignor_name(request):
    query = request.GET.get('query', '')
    if query:
        sender_names = Consignor.objects.filter(sender_name__icontains=query).values_list('sender_name', flat=True)
        print('sender_names numbers:', list(sender_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(sender_names), safe=False)
    return JsonResponse([], safe=False)

def get_sender_details(request):
    name = request.GET.get('name', '')
    if name:
        consignor = Consignor.objects.filter(sender_name=name).first()
        if consignor:
            data = {
                'sender_mobile': consignor.sender_mobile,
                'sender_email': consignor.sender_email,
                'sender_GST': consignor.sender_GST,
                'sender_address': consignor.sender_address,
                'sender_company': consignor.sender_company,
                'cust_id': consignor.cust_id,
            }
        else:
            data = {}
    else:
        data = {}

    return JsonResponse(data)

def get_consignee_name(request):
    query = request.GET.get('query', '')
    if query:
        receiver_names = Consignee.objects.filter(receiver_name__icontains=query).values_list('receiver_name', flat=True)
        print('sender_names numbers:', list(receiver_names))  # Debugging: check the data in the terminal
        return JsonResponse(list(receiver_names), safe=False)
    return JsonResponse([], safe=False)

def get_rec_details(request):
    name = request.GET.get('name', '')
    if name:
        consignee = Consignee.objects.filter(receiver_name=name).first()
        if consignee:
            data = {
                'receiver_mobile': consignee.receiver_mobile,
                'receiver_GST': consignee.receiver_GST,
                'receiver_email': consignee.receiver_email,
                'receiver_address': consignee.receiver_address,
                'receiver_company': consignee.receiver_company,
                'cust_id': consignee.cust_id,
            }
        else:
            data = {}
    else:
        data = {}

    return JsonResponse(data)



def branchConsignment(request):
    if request.method == "POST":
        now = datetime.now().replace(microsecond=0)

        con_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")

        uid = request.session.get('username')
        branch = Branch.objects.get(email=uid)
        branchemail = branch.email
        uname = branch.companyname
        username = branch.headname


        # Get the last track_id and increment it
        last_track_id = AddConsignment.objects.aggregate(Max('track_id'))['track_id__max']
        track_id = int(last_track_id) + 1 if last_track_id else 1000
        con_id = str(track_id)

        # Get the last Consignment_id and increment it
        last_con_id = AddConsignment.objects.aggregate(Max('Consignment_id'))['Consignment_id__max']
        Consignment_id = last_con_id + 1 if last_con_id else 1000
        Consignment_id = str(Consignment_id)

        last_cust_id = Consignee.objects.aggregate(Max('cust_id'))['cust_id__max']
        cust_id = last_cust_id + 1 if last_cust_id else 1
        cust_id = str(cust_id)

        last_consignor_id = Consignor.objects.aggregate(Max('cust_id'))['cust_id__max']
        consignor_id = last_consignor_id + 1 if last_consignor_id else 1000
        consignor_id = str(consignor_id)

        # Sender details
        send_name = request.POST.get('a1')
        send_mobile = request.POST.get('a2')
        send_address = request.POST.get('a4')
        sender_GST = request.POST.get('sendergst')

        # Receiver details
        rec_name = request.POST.get('a5')
        rec_mobile = request.POST.get('a6')
        rec_address = request.POST.get('a8')
        rec_GST = request.POST.get('receivergst')

        # Check if the Consignor already exists
        consignor, created = Consignor.objects.update_or_create(
            sender_name=send_name,
            defaults={
                'sender_mobile': send_mobile,
                'sender_address': send_address,
                'sender_GST': sender_GST,
                'branch': uname,
                'cust_id': consignor_id  # Temporarily set cust_id to None
            }
        )

        # If the consignor was created, assign a new cust_id
        if created:
            consignor_id = consignor.cust_id  # Use the newly created cust_id
        else:
            consignor_id = consignor.cust_id  # Retain existing cust_id if not created

        # Save consignor mobile number in UserLogin table
        UserLogin.objects.update_or_create(
            email=send_mobile,  # Use sender_mobile as the unique key
            defaults={
                'username': send_name,  # Set username to sender_name
                # Add any other fields as necessary
            }
        )

        # Check if the Consignee already exists
        consignee, created = Consignee.objects.update_or_create(
            receiver_name=rec_name,
            defaults={
                'receiver_mobile': rec_mobile,
                'receiver_address': rec_address,
                'receiver_GST': rec_GST,
                'branch': uname,
                'cust_id': cust_id  # Temporarily set cust_id to None
            }
        )

        # Save consignee mobile number in UserLogin table
        UserLogin.objects.update_or_create(
            email=rec_mobile,  # Use receiver_mobile as the unique key
            defaults={
                'username': rec_name,  # Set username to receiver_name
                # Add any other fields as necessary
            }
        )

        # If the consignee was created, assign a new cust_id
        if created:
            cust_id = consignee.cust_id  # Use the newly created cust_id
        else:
            cust_id = consignee.cust_id  # Retain existing cust_id if not created

        # Handling copies
        copies = []
        if request.POST.get('consignor_copy'):
            copies.append('Consignor Copy')
        if request.POST.get('consignee_copy'):
            copies.append('Consignee Copy')
        if request.POST.get('lorry_copy'):
            copies.append('Lorry Copy')
        copy_type = ', '.join(copies)  # Combine into a single string



        # Handling product entries
        products = request.POST.getlist('product[]')
        pieces = request.POST.getlist('pieces[]')

        # Other consignment details
        delivery = request.POST.get('delivery_option')
        prod_invoice = request.POST.get('prod_invoice')
        prod_price = request.POST.get('prod_price')
        weight = float(request.POST.get('weight') or 0)
        weightAmt = float(request.POST.get('weightAmt') or 0)
        freight = float(request.POST.get('freight') or 0)
        hamali = float(request.POST.get('hamali') or 0)
        door_charge = float(request.POST.get('door_charge') or 0)
        st_charge = float(request.POST.get('st_charge') or 0)
        cost = float(request.POST.get('cost') or 0)
        bal = float(request.POST.get('balance') or 0)
        pay_status = request.POST.get('payment')
        route_from = request.POST.get('from')
        route_to = request.POST.get('to')
        eway_bill = request.POST.get('ewaybill_no')


        utype = request.session.get('utype')
        branch_value = 'admin' if utype == 'admin' else uname

        # Determine the appropriate name based on pay_status
        if pay_status == 'Consigner_AC':
            account_name = send_name

        elif pay_status == 'Consignee_AC':
            account_name = rec_name
        else:
            account_name = send_name  # Default to sender_name if pay_status is neither
        # Create consignment records
        for product, piece in zip(products, pieces):
            if not product or not piece:
                continue
            AddConsignment.objects.create(
                track_id=con_id,
                Consignment_id=Consignment_id,
                sender_name=send_name,
                sender_mobile=send_mobile,
                sender_address=send_address,
                sender_GST=sender_GST,
                receiver_name=rec_name,
                receiver_mobile=rec_mobile,
                receiver_address=rec_address,
                receiver_GST=rec_GST,
                desc_product=product,
                pieces=piece,
                prod_invoice=prod_invoice,
                prod_price=prod_price,
                weightAmt=weightAmt,
                weight=weight,
                balance=bal,
                freight=freight,
                hamali=hamali,
                door_charge=door_charge,
                st_charge=st_charge,
                route_from=route_from,
                route_to=route_to,
                total_cost=cost,
                date=con_date,
                pay_status=pay_status,
                branch=branch_value,
                name=username,
                time=current_time,
                copy_type=copy_type,
                delivery=delivery,
                eway_bill=eway_bill,
                consignment_status='Pending',
                branchemail=branchemail,
                status='Consignment Added'

            )
            AddConsignmentTemp.objects.create(
                track_id=con_id,
                Consignment_id=Consignment_id,
                sender_name=send_name,
                sender_mobile=send_mobile,
                sender_address=send_address,
                sender_GST=sender_GST,
                receiver_name=rec_name,
                receiver_mobile=rec_mobile,
                receiver_address=rec_address,
                receiver_GST=rec_GST,
                desc_product=product,
                pieces=piece,
                prod_invoice=prod_invoice,
                prod_price=prod_price,
                weightAmt=weightAmt,
                weight=weight,
                balance=bal,
                freight=freight,
                hamali=hamali,
                door_charge=door_charge,
                st_charge=st_charge,
                route_from=route_from,
                route_to=route_to,
                total_cost=cost,
                date=con_date,
                pay_status=pay_status,
                branch=branch_value,
                name=username,
                time=current_time,
                copy_type=copy_type,
                delivery=delivery,
                eway_bill=eway_bill
            )

        # Only handle the Account model if pay_status is 'Consigner_AC' or 'Consignee_AC'
        if pay_status in ['Consigner_AC', 'Consignee_AC']:
            try:
                # Confirm this block executes
                print(f"Attempting to save to Account with track_id {con_id}, sender_name {account_name}, cost {cost}")

                previous_balance_entry = Account.objects.filter(sender_name=account_name).order_by('-Date').first()
                previous_balance = float(previous_balance_entry.Balance) if previous_balance_entry else 0.0
                updated_balance = previous_balance + cost

                # Proceed to save/update account data
                Account.objects.update_or_create(
                    track_number=con_id,
                    defaults={
                        'sender_name': account_name,
                        'Date': now,
                        'particulars': f'LR: {con_id}',
                        'debit': cost,
                        'credit': 0,
                        'TrType': 'sal',
                        'Balance': updated_balance,
                        'Branch': branch_value,  # Use Branch instead of branch
                        'headname': username
                    }
                )

                print(f"Account record for track_id {con_id} saved successfully.")
            except Exception as e:
                print(f"Error updating account: {str(e)}")

        #send_jsk_message([send_mobile, rec_mobile],
                         #f"Order is confirmed with Raichur parcel service. LRno - {con_id} Sender - {send_name} Receiver - {rec_name} For more click below.https://raichurparcelservices.com/customerLogin")
        return redirect('branchprintConsignment', track_id=con_id)

    return render(request, 'branchConsignment.html')


def branchprintConsignment(request, track_id):
    grouped_userdata = {}
    copy_types = []
    totalqty = 0  # Initialize total quantity

    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        uid = request.session.get('username')
        branchdetails = Branch.objects.get(email=uid)

        if not consignments.exists():
            return render(request, '404.html')  # Handle case where no consignments are found.

        # Loop over each consignment item to gather details individually
        for consignment in consignments:
            if consignment.track_id not in grouped_userdata:
                # Initialize data structure for each track_id
                grouped_userdata[consignment.track_id] = {
                    field.name: getattr(consignment, field.name) for field in AddConsignment._meta.fields
                }
                grouped_userdata[consignment.track_id]['consignment_list'] = []  # To store individual products

            # Add each consignment's product details as a separate entry
            consignment_details = {
                'pieces': consignment.pieces,
                'desc_product': consignment.desc_product,

            }
            grouped_userdata[consignment.track_id]['consignment_list'].append(consignment_details)
            totalqty += consignment.pieces  # Sum up the pieces for total quantity

            if consignment.copy_type not in copy_types:
                copy_types.append(consignment.copy_type)

    except ObjectDoesNotExist:
        grouped_userdata = {}

    return render(request, 'branchprintConsignment.html', {
        'grouped_userdata': grouped_userdata,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types) , # Include the aggregated copy types
        'totalqty': totalqty  # Pass total quantity to the template

    })




def branchviewconsignment(request):
    uid = request.session.get('username')
    grouped_userdata = {}

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname  # Adjust if the branch info is stored differently

            consigner = request.POST.get('consigner')
            consigee = request.POST.get('consignee')
            track_id = request.POST.get('lrno')

            from_date_str = request.POST.get('from_date')
            to_date_str = request.POST.get('to_date')

            # Parse dates
            from_date = parse_date(from_date_str) if from_date_str else None
            to_date = parse_date(to_date_str) if to_date_str else None

            # Fetch consignments for the branch
            consignments = AddConsignment.objects.filter(branch=user_branch)

            if consigner:
                consignments = consignments.filter(sender_name=consigner)
            if consigee:
                consignments = consignments.filter(receiver_name=consigee)
            if track_id:
                consignments = consignments.filter(track_id=track_id)

            if from_date and to_date:
                consignments = consignments.filter(date__range=(from_date, to_date))
            elif from_date:
                consignments = consignments.filter(date__gte=from_date)
            elif to_date:
                consignments = consignments.filter(date__lte=to_date)

            # Group consignments by track_id and concatenate product details
            for consignment in consignments:
                track_id = consignment.track_id
                if track_id not in grouped_userdata:
                    grouped_userdata[track_id] = {
                        'route_from': consignment.route_from,
                        'route_to': consignment.route_to,
                        'sender_name': consignment.sender_name,
                        'sender_mobile': consignment.sender_mobile,
                        'receiver_name': consignment.receiver_name,
                        'receiver_mobile': consignment.receiver_mobile,
                        'total_cost': consignment.total_cost,
                        'pieces': 0,
                        'weight':consignment.weight,
                        'pay_status': consignment.pay_status,
                        'products': []
                    }
                # Aggregate total cost
                grouped_userdata[track_id]['pieces'] += consignment.pieces
                # Concatenate product details without ID
                product_detail = consignment.desc_product
                grouped_userdata[track_id]['products'].append(product_detail)

        except ObjectDoesNotExist:
            pass

    # Convert the list of product details to a single string
    for track_id, details in grouped_userdata.items():
        details['products'] = ', '.join(details['products'])

    return render(request, 'branchviewConsignment.html', {'grouped_userdata': grouped_userdata})


def branchMaster(request):
    uid = request.session['username']
    email=Branch.objects.get(email=uid)
    bid = email.id
    data = Branch.objects.filter(id=bid).first()  # Retrieve a single object or None
    if request.method == "POST":
        companyname = request.POST.get('companyname')
        phonenumber = request.POST.get('phonenumber')
        email = request.POST.get('email')
        gst = request.POST.get('gst')
        address = request.POST.get('address')
        image= request.POST.get('image')

        # Update the object
        data.companyname = companyname
        data.phonenumber = phonenumber
        data.email = email
        data.gst = gst
        data.address = address
        data.image=image

        data.save()

        # Redirect to a different URL after successful update
        base_url = reverse('branchMaster')
        return redirect(base_url)

    return render(request, 'branchMaster.html', {'data': data})


from django.core.exceptions import ObjectDoesNotExist

from django.core.exceptions import ObjectDoesNotExist

def branchconsignment_edit(request, pk):
    # Fetch all consignment objects with the given track_id
    userdatas = AddConsignment.objects.filter(track_id=pk)
    userdata = userdatas.first()
    # Ensure the date is formatted as 'YYYY-MM-DD'

    # Fetch all products under this consignment, multiple objects allowed
    products = AddConsignment.objects.filter(track_id=pk).order_by('id')  # Ordering by 'id' or any other field

    # Fetch consignment temp data if it exists
    userdatat = AddConsignmentTemp.objects.filter(track_id=pk)
    userdatatemps = userdatat.first()
    userdatatemp = AddConsignmentTemp.objects.filter(track_id=pk).order_by('id')

    if request.method == "POST":
        # Update userdata fields for all records with the same track_id
        userdata.route_from = request.POST.get('from')
        userdata.route_to = request.POST.get('to')
        userdata.sender_name = request.POST.get('a1')
        userdata.receiver_name = request.POST.get('a5')
        userdata.total_cost = request.POST.get('cost')
        userdata.weight = request.POST.get('weight')
        userdata.balance = request.POST.get('bal')
        userdata.pay_status = request.POST.get('payment')
        userdata.sender_address = request.POST.get('a4')
        userdata.sender_mobile = request.POST.get('a2')
        userdata.sender_GST = request.POST.get('sendergst')
        userdata.receiver_address = request.POST.get('a8')
        userdata.receiver_mobile = request.POST.get('a6')
        userdata.receiver_GST = request.POST.get('receivergst')
        userdata.prod_invoice = request.POST.get('prod_invoice')
        userdata.prod_price = request.POST.get('prod_price')
        userdata.weightAmt = request.POST.get('weightAmt')
        userdata.freight = request.POST.get('freight')
        userdata.hamali = request.POST.get('hamali')
        userdata.door_charge = request.POST.get('door_charge')
        userdata.st_charge = request.POST.get('st_charge')
        userdata.save()

        # Update AddConsignmentTemp if it exists
        if userdatatemps:
            userdatatemps.route_from = request.POST.get('from')
            userdatatemps.route_to = request.POST.get('to')
            userdatatemps.sender_name = request.POST.get('a1')
            userdatatemps.receiver_name = request.POST.get('a5')
            userdatatemps.total_cost = request.POST.get('cost')
            userdatatemps.weight = request.POST.get('weight')
            userdatatemps.balance = request.POST.get('bal')
            userdatatemps.pay_status = request.POST.get('payment')
            userdatatemps.sender_address = request.POST.get('a4')
            userdatatemps.sender_mobile = request.POST.get('a2')
            userdatatemps.sender_GST = request.POST.get('sendergst')
            userdatatemps.receiver_address = request.POST.get('a8')
            userdatatemps.receiver_mobile = request.POST.get('a6')
            userdatatemps.receiver_GST = request.POST.get('receivergst')
            userdatatemps.prod_invoice = request.POST.get('prod_invoice')
            userdatatemps.prod_price = request.POST.get('prod_price')
            userdatatemps.weightAmt = request.POST.get('weightAmt')
            userdatatemps.freight = request.POST.get('freight')
            userdatatemps.hamali = request.POST.get('hamali')
            userdatatemps.door_charge = request.POST.get('door_charge')
            userdatatemps.st_charge = request.POST.get('st_charge')
            userdatatemps.save()

            # Handling product updates for AddConsignment
            products_list = request.POST.getlist('product[]')  # Product descriptions from form
            pieces_list = request.POST.getlist('pieces[]')  # Pieces data from form

            # Ensure row-by-row updates for AddConsignment
            for i, (product_desc, piece) in enumerate(zip(products_list, pieces_list)):
                if i < len(products):  # Only update existing rows in the DB
                    product_obj = products[i]  # Fetch the i-th product object
                    product_obj.desc_product = product_desc
                    product_obj.pieces = piece
                    product_obj.save()

            # Handle product updates for AddConsignmentTemp, if userdatatemp exists
            if userdatatemp.exists():
                for i, (product_desct, piecet) in enumerate(zip(products_list, pieces_list)):
                    if i < len(userdatatemp):  # Only update existing rows in the DB
                        product_obj_temp = userdatatemp[i]  # Fetch the i-th product object
                        product_obj_temp.desc_product = product_desct
                        product_obj_temp.pieces = piecet
                        product_obj_temp.save()

        # Aggregate product data for TripSheetPrem and TripSheetTemp
        related_products = AddConsignment.objects.filter(track_id=userdata.track_id)
        desc_combined = ', '.join([product.desc_product for product in related_products if product.desc_product])
        total_qty = sum([int(product.pieces) for product in related_products if product.pieces])

        # Update TripSheetPrem and TripSheetTemp if track_id matches LRno
        tripsheet_prem = TripSheetPrem.objects.filter(LRno=pk).first()
        tripsheet_temp = TripSheetTemp.objects.filter(LRno=pk).first()

        # Make sure both desc and qty are updated every time
        if tripsheet_prem:
            tripsheet_prem.desc = desc_combined  # Update desc with combined descriptions
            tripsheet_prem.qty = total_qty  # Update qty with total pieces
            tripsheet_prem.total_cost = userdata.total_cost
            tripsheet_prem.freight = userdata.freight
            tripsheet_prem.hamali = userdata.hamali
            tripsheet_prem.st_charge = userdata.st_charge
            tripsheet_prem.door_charge = userdata.door_charge
            tripsheet_prem.weightAmt = userdata.weightAmt
            tripsheet_prem.balance = userdata.balance
            tripsheet_prem.pay_status = userdata.pay_status
            tripsheet_prem.save()

        if tripsheet_temp:
            tripsheet_temp.desc = desc_combined  # Update desc with combined descriptions
            tripsheet_temp.qty = total_qty  # Update qty with total pieces
            tripsheet_temp.total_cost = userdata.total_cost
            tripsheet_temp.freight = userdata.freight
            tripsheet_temp.hamali = userdata.hamali
            tripsheet_temp.st_charge = userdata.st_charge
            tripsheet_temp.door_charge = userdata.door_charge
            tripsheet_temp.weightAmt = userdata.weightAmt
            tripsheet_temp.balance = userdata.balance
            tripsheet_temp.pay_status = userdata.pay_status
            tripsheet_temp.save()

        # Handling Account model update
        pay_status = userdata.pay_status
        cost = userdata.total_cost
        account_name = None

        if pay_status == 'Consigner_AC':
            account_name = userdata.sender_name
        elif pay_status == 'Consignee_AC':
            account_name = userdata.receiver_name
        else:
            account_name = userdata.sender_name  # Default to sender_name if pay_status is neither

        if pay_status in ['Consigner_AC', 'Consignee_AC']:
            try:
                from datetime import datetime  # Ensure proper imports

                # Parse date and time fields
                cost = float(userdata.total_cost)  # Ensure cost is a float
                date = userdata.date  # e.g., '2025-01-10'
                time = userdata.time

                if isinstance(date, str):
                    date = datetime.strptime(date, '%Y-%m-%d').date()
                if isinstance(time, str):
                    time = datetime.strptime(time, '%H:%M:%S').time()

                combined_datetime = datetime.combine(date, time)

                # Fetch or create the account entry
                existing_account_entry = Account.objects.filter(track_number=userdata.track_id).first()

                if existing_account_entry:
                    # Update the existing entry
                    existing_account_entry.Date = datetime.now()
                    existing_account_entry.debit = cost  # Update with new debit value
                    existing_account_entry.particulars = f"{userdata.track_id} Amount Debited"
                    existing_account_entry.headname = request.user.username
                    existing_account_entry.Branch = userdata.branch
                    existing_account_entry.save()
                else:
                    # Create a new entry
                    Account.objects.create(
                        track_number=userdata.track_id,
                        Date=combined_datetime,
                        debit=cost,
                        credit=0,
                        TrType="sal",
                        particulars=f"{userdata.track_id} Amount Debited",
                        Balance=0,  # Balance will be recalculated below
                        sender_name=account_name,
                        headname=request.user.username,
                        Branch=userdata.branch
                    )

                # Fetch all entries for the sender_name ordered by track_number
                account_entries = Account.objects.filter(sender_name=account_name).order_by('track_number', 'Date')

                # Initialize the previous balance
                previous_balance = 0.0  # Start with a float value

                # Recalculate balance for each entry
                for account_entry in account_entries:
                    # Convert debit, credit to floats
                    debit = float(account_entry.debit or 0)
                    credit = float(account_entry.credit or 0)

                    if account_entry.track_number == userdata.track_id:
                        # Use the updated debit value for the matching track_number
                        account_entry.Balance = previous_balance + cost - credit
                    else:
                        # Use the existing debit value for other entries
                        account_entry.Balance = previous_balance + debit - credit

                    # Update previous balance for the next iteration
                    previous_balance = account_entry.Balance

                    # Save the updated entry
                    account_entry.save()

                print(f"Balances recalculated for sender: {account_name}")

            except Exception as e:
                print(f"Error updating/creating Account entry: {e}")

        return redirect(reverse('branchviewconsignment'))

    return render(request, 'branchconsignment_edit.html', {'userdata': userdata, 'products': userdatas})


def branchconsignment_delete(request, pk):
    # Fetch all AddConsignment instances that match the track_id
    udata_list = AddConsignment.objects.filter(track_id=pk)

    # Ensure there are records in udata_list before proceeding
    if not udata_list.exists():
        # Handle the case where no consignments are found (optional)
        return redirect('adminView_Consignment')

    # Get the sender_name from the first object in the QuerySet
    if udata_list.first().pay_status == 'Consigner_AC':
        sender_name = udata_list.first().sender_name
    elif udata_list.first().pay_status == 'Consignee_AC':
        sender_name = udata_list.first().receiver_name
    # Iterate through each consignment and save its data to DeleteConsignment
    for udata in udata_list:
        # Save the existing consignment data into DeleteConsignment before deletion
        del_consignment = DeleteConsignment(
            track_id=udata.track_id,
            sender_name=udata.sender_name,
            sender_mobile=udata.sender_mobile,
            sender_address=udata.sender_address,
            sender_GST=udata.sender_GST,
            receiver_name=udata.receiver_name,
            receiver_mobile=udata.receiver_mobile,
            receiver_address=udata.receiver_address,
            receiver_GST=udata.receiver_GST,
            total_cost=udata.total_cost,
            date=udata.date,
            pay_status=udata.pay_status,
            route_from=udata.route_from,
            route_to=udata.route_to,
            desc_product=udata.desc_product,
            pieces=udata.pieces,
            prod_invoice=udata.prod_invoice,
            prod_price=udata.prod_price,
            weight=udata.weight,
            freight=udata.freight,
            hamali=udata.hamali,
            door_charge=udata.door_charge,
            st_charge=udata.st_charge,
            Consignment_id=udata.track_id,  # Save the consignment ID here
            branch=udata.branch,
            name=udata.sender_name,  # Assuming sender_name is the name of the person who created the consignment
            balance=udata.balance,
            time=udata.time,  # Save the current timestamp
            copy_type=udata.copy_type,  # You can assign a copy type if needed, for record-keeping
            weightAmt=udata.weightAmt,
            delivery=udata.delivery,
            eway_bill=udata.eway_bill,
        )
        del_consignment.save()  # Save the consignment data before deletion

        # Check if related data exists in AddConsignmentTemp and delete
        if AddConsignmentTemp.objects.filter(track_id=udata.track_id).exists():
            utdata = AddConsignmentTemp.objects.filter(track_id=udata.track_id)
            utdata.delete()  # Delete only if it exists

        # Check if related data exists in Account and delete
        if Account.objects.filter(track_number=udata.track_id).exists():
            accountdata = Account.objects.get(track_number=udata.track_id)
            accountdata.delete()  # Delete only if it exists

        # Check and delete from TripSheetPrem if exists
        tripdatap = TripSheetPrem.objects.filter(LRno=pk).first()
        if tripdatap:
            tripdatap.delete()

        # Check and delete from TripSheetTemp if exists
        tripdatat = TripSheetTemp.objects.filter(LRno=pk).first()
        if tripdatat:
            tripdatat.delete()

        # Delete the consignment
        udata.delete()
    update_account_balances(sender_name)


    # Redirect to the desired view
    base_url = reverse('adminView_Consignment')
    return redirect(base_url)


from decimal import Decimal


def update_account_balances(sender_name):
    """
    Update balances in the Account table for a specific sender_name after a record is deleted.
    """
    # Filter accounts by sender_name and order them sequentially
    accounts = Account.objects.filter(sender_name=sender_name).order_by('track_number')
    previous_balance = Decimal(0)

    for index, account in enumerate(accounts):
        debit = Decimal(account.debit) if account.debit else Decimal(0)
        credit = Decimal(account.credit) if account.credit else Decimal(0)

        # Calculate the current balance
        current_balance = previous_balance +  debit- credit

        # Update the balance for the current record
        account.Balance = current_balance
        account.save()

        # Update previous_balance for the next record
        previous_balance = current_balance

    return


# Example usage:


def deleteConsignment(request):
    grouped_userdata = {}  # Initialize as an empty dictionary to group data

    # Start with a base queryset
    queryset = DeleteConsignment.objects.all()

    if request.method == 'POST':
        branch = request.POST.get('t2')
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')
        consigner = request.POST.get('consigner')
        consignee = request.POST.get('consignee')
        track_id = request.POST.get('lrno')

        # Parse dates
        from_date = parse_date(from_date_str) if from_date_str else None
        to_date = parse_date(to_date_str) if to_date_str else None

        print("Branch: {}".format(branch))  # Debugging: Print the branch name
        print("From Date: {}".format(from_date))  # Debugging: Print the from date
        print("To Date: {}".format(to_date))  # Debugging: Print the to date

        # Apply filters only if they are provided
        if branch:
            queryset = queryset.filter(branch=branch)
        if consigner:
            queryset = queryset.filter(sender_name=consigner)
        if consignee:
            queryset = queryset.filter(receiver_name=consignee)
        if track_id:
            queryset = queryset.filter(track_id=track_id)

        # Apply date filters
        if from_date and to_date:
            queryset = queryset.filter(date__range=(from_date, to_date))
        elif from_date:
            queryset = queryset.filter(date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(date__lte=to_date)

    # Group consignments by track_id and concatenate product details
    for consignment in queryset:
        track_id = consignment.track_id

        if track_id not in grouped_userdata:
            grouped_userdata[track_id] = {
                'branch': consignment.branch,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'sender_name': consignment.sender_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_name': consignment.receiver_name,
                'receiver_mobile': consignment.receiver_mobile,
                'total_cost': consignment.total_cost,
                'pieces': 0,
                'weight': consignment.weight,
                'pay_status': consignment.pay_status,
                'products': []
            }
        # Aggregate total cost and pieces
        # Aggregate total cost and pieces, ensuring total_cost defaults to 0 if None
        grouped_userdata[track_id]['pieces'] += (consignment.pieces or 0)

        # Concatenate product details without ID
        product_detail = consignment.desc_product
        grouped_userdata[track_id]['products'].append(product_detail)

    # Convert the list of product details to a single string
    for track_id, details in grouped_userdata.items():
        details['products'] = ', '.join(details['products'])

    # Render the template with grouped data
    return render(request, 'deleteRecovery.html', {'grouped_userdata': grouped_userdata})


def deleteRecovery(request, pk):
    try:
        print(f"Attempting to recover consignments with track_id {pk}")

        # Fetch consignment(s) from DeleteConsignment based on track_id
        del_consignments = DeleteConsignment.objects.filter(track_id=pk)
        if not del_consignments.exists():
            print(f"No consignments found with track_id {pk}")
            return HttpResponse("Consignment not found", status=404)

        print(f"Fetched {len(del_consignments)} consignments with track_id {pk}")

        with transaction.atomic():  # Ensure the entire operation is atomic
            for index, del_consignment in enumerate(del_consignments):
                print(f"Processing consignment {index + 1}/{len(del_consignments)}: {vars(del_consignment)}")

                # Recover into AddConsignment
                add_consignment = AddConsignment(
                    track_id=del_consignment.track_id,
                    sender_name=del_consignment.sender_name,
                    sender_mobile=del_consignment.sender_mobile,
                    sender_address=del_consignment.sender_address,
                    sender_GST=del_consignment.sender_GST,
                    receiver_name=del_consignment.receiver_name,
                    receiver_mobile=del_consignment.receiver_mobile,
                    receiver_address=del_consignment.receiver_address,
                    receiver_GST=del_consignment.receiver_GST,
                    total_cost=del_consignment.total_cost,
                    date=del_consignment.date,
                    pay_status=del_consignment.pay_status,
                    route_from=del_consignment.route_from,
                    route_to=del_consignment.route_to,
                    desc_product=del_consignment.desc_product,
                    pieces=del_consignment.pieces,
                    prod_invoice=del_consignment.prod_invoice,
                    prod_price=del_consignment.prod_price,
                    weight=del_consignment.weight,
                    freight=del_consignment.freight,
                    hamali=del_consignment.hamali,
                    door_charge=del_consignment.door_charge,
                    st_charge=del_consignment.st_charge,
                    Consignment_id=del_consignment.track_id,
                    branch=del_consignment.branch,
                    name=del_consignment.sender_name,
                    balance=del_consignment.balance,
                    time=del_consignment.time,
                    copy_type=del_consignment.copy_type,
                    weightAmt=del_consignment.weightAmt,
                    delivery=del_consignment.delivery,
                    eway_bill=del_consignment.eway_bill,
                )
                add_consignment.save()
                print(f"AddConsignment saved with track_id {add_consignment.track_id}")

                # Recover into AddConsignmentTemp
                add_consignment_temp = AddConsignmentTemp(
                    track_id=del_consignment.track_id,
                    sender_name=del_consignment.sender_name,
                    sender_mobile=del_consignment.sender_mobile,
                    sender_address=del_consignment.sender_address,
                    sender_GST=del_consignment.sender_GST,
                    receiver_name=del_consignment.receiver_name,
                    receiver_mobile=del_consignment.receiver_mobile,
                    receiver_address=del_consignment.receiver_address,
                    receiver_GST=del_consignment.receiver_GST,
                    total_cost=del_consignment.total_cost,
                    date=del_consignment.date,
                    pay_status=del_consignment.pay_status,
                    route_from=del_consignment.route_from,
                    route_to=del_consignment.route_to,
                    desc_product=del_consignment.desc_product,
                    pieces=del_consignment.pieces,
                    prod_invoice=del_consignment.prod_invoice,
                    prod_price=del_consignment.prod_price,
                    weight=del_consignment.weight,
                    freight=del_consignment.freight,
                    hamali=del_consignment.hamali,
                    door_charge=del_consignment.door_charge,
                    st_charge=del_consignment.st_charge,
                    Consignment_id=del_consignment.track_id,
                    branch=del_consignment.branch,
                    name=del_consignment.sender_name,
                    balance=del_consignment.balance,
                    time=del_consignment.time,
                    copy_type=del_consignment.copy_type,
                    weightAmt=del_consignment.weightAmt,
                    delivery=del_consignment.delivery,
                    eway_bill=del_consignment.eway_bill,
                    status='Consignment Added',
                    consignment_status='Pending'
                )
                add_consignment_temp.save()
                print(f"AddConsignmentTemp saved with track_id {add_consignment_temp.track_id}")

                # Handle Account updates only for the first consignment
                if index == 0 and del_consignment.pay_status in ['Consigner_AC', 'Consignee_AC']:
                    try:
                        date = del_consignment.date  # e.g., '2025-01-10'
                        time = del_consignment.time

                        if isinstance(date, str):
                            # Convert string to date
                            date = datetime.strptime(date, '%Y-%m-%d').date()
                        if isinstance(time, str):
                            # Convert string to time
                            time = datetime.strptime(time, '%H:%M:%S').time()

                            # Combine into a single datetime object
                        combined_datetime = datetime.combine(date, time)
                        print(f"Updating Account for {del_consignment.sender_name}")
                        previous_balance_entry = Account.objects.filter(
                            sender_name=del_consignment.sender_name).order_by('-Date').first()
                        previous_balance = float(previous_balance_entry.Balance) if previous_balance_entry else 0.0
                        updated_balance = previous_balance + del_consignment.total_cost

                        account_entry, created = Account.objects.update_or_create(
                            track_number=del_consignment.track_id,
                            defaults={
                                'Date': combined_datetime,
                                'debit': del_consignment.total_cost,
                                'credit': 0,
                                'TrType': "sal",
                                'particulars': f"{del_consignment.track_id} Amount Debited",
                                'Balance': updated_balance,
                                'sender_name': del_consignment.sender_name,
                                'headname': request.user.username,
                                'Branch': del_consignment.branch,
                            }
                        )
                        print(f"Account entry {'created' if created else 'updated'}: {account_entry}")
                    except Exception as e:
                        print(f"Error updating Account table: {e}")
                        raise

            # Delete all consignments with the same track_id
            del_consignments.delete()
            print(f"All consignments with track_id {pk} deleted.")

        # Redirect to the deleteConsignment page
        return redirect('deleteConsignment')

    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse(f"Error: {e}", status=500)


def branchinvoiceConsignment(request, track_id):
    grouped_userdata = {}
    copy_types = []
    totalqty = 0  # Initialize total quantity

    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        uid = request.session.get('username')
        branchdetails = Branch.objects.get(email=uid)

        if not consignments.exists():
            return render(request, '404.html')  # Handle case where no consignments are found.

        # Loop over each consignment item to gather details individually
        for consignment in consignments:
            if consignment.track_id not in grouped_userdata:
                # Initialize data structure for each track_id
                grouped_userdata[consignment.track_id] = {
                    field.name: getattr(consignment, field.name) for field in AddConsignment._meta.fields
                }
                grouped_userdata[consignment.track_id]['consignment_list'] = []  # To store individual products

            # Add each consignment's product details as a separate entry
            consignment_details = {
                'pieces': consignment.pieces,
                'desc_product': consignment.desc_product,

            }
            grouped_userdata[consignment.track_id]['consignment_list'].append(consignment_details)
            totalqty += consignment.pieces  # Sum up the pieces for total quantity

            if consignment.copy_type not in copy_types:
                copy_types.append(consignment.copy_type)

    except ObjectDoesNotExist:
        grouped_userdata = {}

    return render(request, 'branchinvoiceConsignment.html', {
        'grouped_userdata': grouped_userdata,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types,),  # Aggregated copy types
        'totalqty': totalqty  # Pass total quantity to the template

    })


def branchaddTrack(request):
    userid = request.session.get('username')
    userdata = Branch.objects.get(email=userid)
    uname = userdata.companyname
    consignments = AddConsignment.objects.filter(branch=uname).order_by('-id')

    if request.method == "POST":
        now = datetime.datetime.now()
        con_date = now.strftime("%Y-%m-%d")

        track_id = request.POST.get('a1')
        status = request.POST.get('status')  # Retrieve status from the form

        # Retrieve custom status if "Other" is selected
        if status == "Other":
            custom_status = request.POST.get('a2')
        else:
            custom_status = None

        # Retrieve username from session and fetch the corresponding branch
        uid = request.session.get('username')

        if uid:
                userdata = Branch.objects.get(email=uid)
                uname = userdata.companyname

                # Check utype to determine the branch value
                utype = request.session.get('utype')
                branch_value = 'admin' if utype == 'admin' else uname

                # Filter consignment data based on the branch
                consignments = AddConsignment.objects.filter(branch=uname).order_by('-id')

                # Create AddTrack object
                AddTrack.objects.create(
                    track_id=track_id,
                    description=status,
                    date=con_date,
                    branch=branch_value
                )

        else:
            # Handle the case where session data is missing
            consignments = AddConsignment.objects.none()
            return render(request, 'branchaddTrack.html', {'consignments': consignments, 'msg': 'Session data missing'})

    return render(request, 'branchaddTrack.html', {'consignments': consignments})


def branchsearch_results(request):
    tracker_id = request.GET.get('tracker_id')
    userid = request.session.get('username')
    userdata = Branch.objects.get(email=userid)
    uname = userdata.companyname
    consignments = AddConsignment.objects.filter(branch=uname).order_by('-id')

    if tracker_id:
        try:
            trackers = AddTrack.objects.filter(track_id=tracker_id)
            if trackers.exists():
                return render(request, 'branchsearch_results.html', {'trackers': trackers, 'consignments': consignments})
            else:
                message = f"No tracking information found for ID: {tracker_id}"
                return render(request, 'branchsearch_results.html', {'message': message, 'consignments': consignments})
        except Exception as e:
            message = f"Error occurred: {str(e)}"
            return render(request, 'branchsearch_results.html', {'message': message, 'consignments': consignments})
    else:
        return render(request, 'branchsearch_results.html', {'message': "Please enter a tracker ID.", 'consignments': consignments})


def branchtrack_delete(request,pk):
    udata=AddTrack.objects.get(id=pk)
    udata.delete()
    base_url=reverse('branchsearch_results')
    return redirect(base_url)


def get_vehicle_numbers(request):
    query = request.GET.get('query', '')
    if query:
        vehicle_numbers = Vehicle.objects.filter(vehicle_number__icontains=query).values_list('vehicle_number', flat=True)
        print('Vehicle numbers:', list(vehicle_numbers))  # Debugging: check the data in the terminal
        return JsonResponse(list(vehicle_numbers), safe=False)
    return JsonResponse([], safe=False)

def get_driver_name(request):
    query = request.GET.get('query', '')
    if query:
        driver_name = Driver.objects.filter(driver_name__icontains=query).values_list('driver_name', flat=True)
        print('Driver Name:', list(driver_name))  # Debugging: check the data in the terminal
        return JsonResponse(list(driver_name), safe=False)
    return JsonResponse([], safe=False)

def get_branch(request):
    query = request.GET.get('query', '')
    if query:
        companyname = Branch.objects.filter(companyname__icontains=query).values_list('companyname', flat=True)
        print('Branch Name:', list(companyname))  # Debugging: check the data in the terminal
        return JsonResponse(list(companyname), safe=False)
    return JsonResponse([], safe=False)

def get_destination(request):
    query = request.GET.get('query', '')
    if query:
        # Filter and get distinct route_to values
        route_to = AddConsignment.objects.filter(route_to__icontains=query).values_list('route_to', flat=True).distinct()
        print('Distinct route_to numbers:', list(route_to))  # Debugging: check the data in the terminal
        return JsonResponse(list(route_to), safe=False)
    return JsonResponse([], safe=False)




from collections import defaultdict

def addTripSheet(request):
    route_to = AddConsignmentTemp.objects.values_list('route_to', flat=True).distinct()
    addtrip = defaultdict(
        lambda: {'desc_product': [], 'pieces': 0, 'receiver_name': '', 'pay_status': '', 'route_to': '', 'total': '',
                 'weightAMt': '', 'freight': '', 'hamali': '', 'door_charge': '', 'st_charge': '','balance':''})
    no_data_found = False  # Flag to check if data was found

    uid = request.session.get('username')
    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            if request.method == 'POST':
                route_to = request.POST.get('dest')

                if user_branch:
                    consignments = AddConsignmentTemp.objects.filter(
                        route_to=route_to,
                    )

                    if consignments.exists():
                        for consignment in consignments:
                            consignment_data = addtrip[consignment.track_id]
                            consignment_data['desc_product'].append(consignment.desc_product)
                            consignment_data['pieces'] += consignment.pieces
                            consignment_data['route_to'] = consignment.route_to
                            consignment_data['receiver_name'] = consignment.receiver_name
                            consignment_data['pay_status'] = consignment.pay_status
                            consignment_data['total_cost'] = consignment.total_cost
                            consignment_data['weightAmt'] = consignment.weightAmt
                            consignment_data['freight'] = consignment.freight
                            consignment_data['hamali'] = consignment.hamali
                            consignment_data['door_charge'] = consignment.door_charge
                            consignment_data['st_charge'] = consignment.st_charge
                            consignment_data['balance'] = consignment.balance
                    else:
                        no_data_found = True  # Set the flag if no data is found

            addtrip = [
                {
                    'track_id': track_id,
                    'desc_product': ', '.join(consignment_data['desc_product']),
                    'pieces': consignment_data['pieces'],
                    'route_to': consignment_data['route_to'],
                    'receiver_name': consignment_data['receiver_name'],
                    'pay_status': consignment_data['pay_status'],
                    'total_cost': consignment_data['total_cost'],
                    'weightAmt': consignment_data['weightAmt'],
                    'freight': consignment_data['freight'],
                    'hamali': consignment_data['hamali'],
                    'door_charge': consignment_data['door_charge'],
                    'st_charge': consignment_data['st_charge'],
                    'balance': consignment_data['balance']
                }
                for track_id, consignment_data in addtrip.items()
            ]

        except Branch.DoesNotExist:
            addtrip = []
            no_data_found = True  # Set the flag if the branch does not exist

    return render(request, 'addTripSheet.html', {
        'route_to': route_to,
        'trip': addtrip,
        'no_data_found': no_data_found  # Pass the flag to the template
    })

def saveTripSheetList(request):
    print("saveTripSheet function called")
    if request.method == 'POST':
        print("POST request received")  # Debugging statement


        uid = request.session.get('username')
        if uid:
            try:
                branch = Branch.objects.get(email=uid)
                branchname = branch.companyname
                username = branch.headname

                now = datetime.now()
                con_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")


                total_rows = int(request.POST.get('total_rows', 0))


                selected_rows = request.POST.getlist('selected_rows')

                for i in range(1, total_rows + 1):
                    if str(i) in selected_rows:  # Only process if the row is selected
                        track_id = request.POST.get(f'track_id_{i}')
                        pieces = request.POST.get(f'pieces_{i}')
                        desc_product = request.POST.get(f'desc_product_{i}')
                        route_to = request.POST.get(f'route_to_{i}')
                        receiver_name = request.POST.get(f'receiver_name_{i}')
                        pay_status = request.POST.get(f'pay_status_{i}')
                        total_cost = request.POST.get(f'total_cost{i}')
                        weightAmt = request.POST.get(f'weightAmt{i}')
                        freight = request.POST.get(f'freight{i}')
                        hamali = request.POST.get(f'hamali{i}')
                        door_charge = request.POST.get(f'door_charge{i}')
                        st_charge = request.POST.get(f'st_charge{i}')
                        balance = request.POST.get(f'balance{i}')

                        print(f"Track ID: {track_id}, Pieces: {pieces}, Description: {desc_product}, Route: {route_to}, Receiver: {receiver_name}, Pay Status: {pay_status}, total_cost:{total_cost},weightAmt:{weightAmt},freight:{freight},hamali:{hamali},door_charge:{door_charge},st_charge:{st_charge}")  # Debugging statement


                        # Save to TripSheetTemp
                        TripSheetTemp.objects.create(
                            LRno=track_id,
                            qty=pieces,
                            desc=desc_product,
                            dest=route_to,
                            consignee=receiver_name,
                            pay_status=pay_status,
                            branch=branchname,
                            username=username,
                            Date=con_date,
                            total_cost=total_cost,
                            weightAmt=weightAmt,
                            freight=freight,
                            hamali=hamali,
                            door_charge=door_charge,
                            st_charge=st_charge,
                            balance=balance,
                            )

                        # Delete from AddConsignmentTemp
                        AddConsignmentTemp.objects.filter(track_id=track_id).delete()

                        print(f"Data for Track ID {track_id} saved and deleted from AddConsignmentTemp successfully.")  # Debugging statement
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('addTripSheet')  # Replace with your desired success URL

    print("Not a POST request, redirecting back to form.")  # Debugging statement
    return render(request, 'addTripSheet.html')  # Redirect back to the form if not a POST request



def addTripSheetList(request):
    addtrip = []
    uid = request.session.get('username')
    no_data_found = False
    unique_destinations = []
    destination_order = {}

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname
            date = request.POST.get('date') if request.method == 'POST' else None

            # Fetch trip records even for GET requests
            if date:
                consignments = TripSheetTemp.objects.filter(Date=date)
            else:
                consignments = TripSheetTemp.objects.all()

            # Extract unique destinations
            unique_destinations = list(OrderedDict.fromkeys(consignment.dest for consignment in consignments))

            if request.method == 'POST' and date:
                # Get the destination positions from the frontend
                for dest in unique_destinations:
                    pos = request.POST.get(f'position_{dest}')
                    if pos:
                        destination_order[dest] = int(pos)

                # Sort destinations by assigned position
                sorted_destinations = sorted(destination_order.keys(), key=lambda x: destination_order[x])

                # Sort trip records based on destination order
                addtrip = sorted(
                    [
                        {
                            'track_id': consignment.LRno,
                            'desc': consignment.desc,
                            'qty': consignment.qty,
                            'dest': consignment.dest,
                            'consignee': consignment.consignee,
                            'pay_status': consignment.pay_status,
                            'total_cost': consignment.total_cost,
                            'weightAmt': consignment.weightAmt,
                            'freight': consignment.freight,
                            'hamali': consignment.hamali,
                            'door_charge': consignment.door_charge,
                            'st_charge': consignment.st_charge,
                            'balance': consignment.balance,
                        }
                        for consignment in consignments
                    ],
                    key=lambda x: destination_order.get(x['dest'], float('inf'))
                )

                no_data_found = not addtrip

        except Branch.DoesNotExist:
            addtrip = []
            no_data_found = True

    return render(request, 'addTripSheetList.html', {
        'trip': addtrip,
        'no_data_found': no_data_found,
        'unique_destinations': unique_destinations
    })



def saveTripSheet(request):
    print("saveTripSheet function called")

    if request.method == 'POST':
        print("POST request received")

        last_trip_id = TripSheetPrem.objects.aggregate(Max('trip_id'))['trip_id__max']
        trip_id = int(last_trip_id) + 1 if last_trip_id else 1000
        con_id = str(trip_id)

        uid = request.session.get('username')
        if uid:
            try:
                branch = Branch.objects.get(email=uid)
                branchname = branch.companyname
                username = branch.headname

                now = datetime.now()
                con_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")

                # Get form data and ensure valid defaults
                vehicle = request.POST.get('vehical', '').strip()
                drivername = request.POST.get('drivername', '').strip()
                adv = request.POST.get('advance', 0) or 0
                ltrate = request.POST.get('ltrate', 0) or 0
                ltr = request.POST.get('liter', 0) or 0

                literate = float(ltrate)
                liter = float(ltr)
                diesel_total = literate * liter

                print(f"Vehicle: {vehicle}, Driver: {drivername}, Advance: {adv}, LTRate: {ltrate}, Liter: {ltr}")

                if vehicle and drivername:  # Ensure valid data before saving
                    driver = Driver.objects.get(driver_name=drivername)
                    phone = driver.phone_number

                    Disel.objects.create(
                        Date=con_date,
                        vehicalno=vehicle,
                        drivername=drivername,
                        ltrate=ltrate,
                        liter=ltr,
                        total=diesel_total,
                        trip_id=con_id
                    )

                    total_rows = int(request.POST.get('total_rows', 0))

                    for i in range(1, total_rows + 1):
                        track_id = request.POST.get(f'track_id_{i}')
                        desc = request.POST.get(f'desc_{i}')
                        qty = request.POST.get(f'qty_{i}')
                        dest = request.POST.get(f'dest_{i}')
                        consignee = request.POST.get(f'consignee_{i}')
                        total_cost = request.POST.get(f'total_cost_{i}')
                        pay_status = request.POST.get(f'pay_status_{i}')
                        weightAmt = request.POST.get(f'weightAmt_{i}')
                        freight = request.POST.get(f'freight_{i}')
                        hamali = request.POST.get(f'hamali_{i}')
                        door_charge = request.POST.get(f'door_charge_{i}')
                        st_charge = request.POST.get(f'st_charge_{i}')
                        balance = request.POST.get(f'balance_{i}')

                        print(f"Track ID: {track_id}, Description: {desc}, Quantity: {qty}")

                        if track_id and qty:  # Ensure required fields are not empty
                            TripSheetPrem.objects.create(
                                LRno=track_id,
                                qty=qty,
                                desc=desc,
                                dest=dest,
                                consignee=consignee,
                                pay_status=pay_status,
                                VehicalNo=vehicle,
                                DriverName=drivername,
                                DriverNumber=phone,
                                branch=branchname,
                                username=username,
                                Date=con_date,
                                Time=current_time,
                                AdvGiven=adv,
                                LTRate=ltrate,
                                Ltr=ltr,
                                total_cost=total_cost,
                                weightAmt=weightAmt,
                                freight=freight,
                                hamali=hamali,
                                door_charge=door_charge,
                                st_charge=st_charge,
                                balance=balance,
                                trip_id=con_id,
                                status='TripSheet Added',
                            )

                            TripSheetTemp.objects.filter(LRno=track_id).delete()

                            print(f"Data for Track ID {track_id} saved successfully.")
                else:
                    print("Vehicle or driver name missing.")
            except Branch.DoesNotExist:
                print("Branch does not exist.")
            except Driver.DoesNotExist:
                print("Driver not found.")

        else:
            print("No username found in session.")

        return redirect('addTripSheetList')

    return render(request, 'addTripSheetList.html')


from django.db.models import Sum, F, FloatField

def tripSheet(request):
    return render(request,'tripSheet.html')

def tripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    grand_total = {
        'ToPay': 0,
        'Paid': 0,
        'Consigner_AC': 0,
        'Consignee_AC': 0,
        'grand_freight': 0,
        'grand_hamali': 0,
        'grand_st_charge': 0,
        'grand_door_charge': 0,
        'grand_weightAmt': 0,
        'grand_balance': 0,
        'grand_total': 0
    }
    summary = {
        'ToPay': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0},
        'Paid': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0},
        'Consigner_AC': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0},
        'Consignee_AC': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0}
    }

    uid = request.session.get('username')

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            if request.method == 'POST':
                vehicle_number = request.POST.get('vehical')
                date = request.POST.get('t3')

                if date:
                    trips = TripSheetPrem.objects.filter(
                        VehicalNo=vehicle_number,
                        Date=date,
                    )
                    # Calculate total quantity
                    total_qty = trips.aggregate(total_qty=Sum('qty'))['total_qty'] or 0

                    # Aggregate data based on pay_status
                    statuses = ['ToPay', 'Paid', 'Consigner_AC', 'Consignee_AC']
                    for status in statuses:
                        status_trips = trips.filter(pay_status=status)
                        summary[status]['freight'] = status_trips.aggregate(total=Sum('freight'))['total'] or 0
                        summary[status]['hamali'] = status_trips.aggregate(total=Sum('hamali'))['total'] or 0
                        summary[status]['st_charge'] = status_trips.aggregate(total=Sum('st_charge'))['total'] or 0
                        summary[status]['door_charge'] = status_trips.aggregate(total=Sum('door_charge'))['total'] or 0
                        summary[status]['weightAmt'] = status_trips.aggregate(total=Sum('weightAmt'))['total'] or 0
                        summary[status]['balance'] = status_trips.aggregate(total=Sum('balance'))['total'] or 0
                        summary[status]['total_cost'] = status_trips.aggregate(total=Sum('total_cost'))['total'] or 0

                        # Update grand totals
                        grand_total[status] = summary[status]['total_cost']
                        grand_total['grand_freight'] += summary[status]['freight']
                        grand_total['grand_hamali'] += summary[status]['hamali']
                        grand_total['grand_st_charge'] += summary[status]['st_charge']
                        grand_total['grand_door_charge'] += summary[status]['door_charge']
                        grand_total['grand_weightAmt'] += summary[status]['weightAmt']
                        grand_total['grand_balance'] += summary[status]['balance']
                        grand_total['grand_total'] += summary[status]['total_cost']

                    # Calculate the total value using the first row
                    if trips.exists():
                        first_trip = trips.first()
                        total_ltr_value = float(
                            first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
                        total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                        total_value = total_ltr_value + total_adv_given
                    else:
                        total_value = 0.0

        except ObjectDoesNotExist:
            trips = TripSheetTemp.objects.none()

    return render(request, 'TripSheetList.html', {
        'trips': trips,
        'total_value': total_value,
        'total_qty': total_qty,
        'grand_total': grand_total,
        'summary': summary
    })


@require_POST
def delete_trip_sheet_data(request):
    vehicle_number = request.POST.get('vehical')
    date = request.POST.get('t3')
    uid = request.session.get('username')

    print(f"Received vehicle_number: {vehicle_number}, date: {date}, uid: {uid}")

    if uid and vehicle_number and date:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname
            TripSheetTemp.objects.filter(
                VehicalNo=vehicle_number,
                Date=date,
            ).delete()
            return JsonResponse({'status': 'success'})
        except ObjectDoesNotExist:
            print("Branch does not exist.")
            return JsonResponse({'status': 'error', 'message': 'Branch does not exist'})

    print("Invalid parameters received.")
    return JsonResponse({'status': 'error', 'message': 'Invalid parameters'})
def viewTripSheetList(request):
    grouped_trips = []
    uid = request.session.get('username')

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            if request.method == 'POST':
                date = request.POST.get('t3')

                if date:
                    # Group by VehicalNo and Date, and annotate with count
                    grouped_trips = (
                        TripSheetPrem.objects
                        .filter(Date=date)
                        .values('VehicalNo', 'Date')
                        .annotate(trip_count=Count('id'))
                    )

        except ObjectDoesNotExist:
            grouped_trips = []

    return render(request, 'viewTripSheetList.html', {
        'grouped_trips': grouped_trips
    })


from collections import OrderedDict


def editTripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    grand_total = {
        'ToPay': 0,
        'Paid': 0,
        'Consigner_AC': 0,
        'Consignee_AC': 0,
        'grand_freight': 0,
        'grand_hamali': 0,
        'grand_st_charge': 0,
        'grand_door_charge': 0,
        'grand_weightAmt': 0,
        'grand_balance': 0,
        'grand_total': 0
    }
    summary = {status: {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0,
                        'balance': 0} for status in grand_total.keys() if
               status not in ['grand_freight', 'grand_hamali', 'grand_st_charge', 'grand_door_charge',
                              'grand_weightAmt', 'grand_balance', 'grand_total']}

    uid = request.session.get('username')

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            if request.method == 'POST':
                vehicle_number = request.POST.get('vehical')
                date_str = request.POST.get('t3')

                if date_str:
                    date = date_str  # Assuming yyyy-mm-dd format

                    trips = TripSheetPrem.objects.filter(
                        VehicalNo=vehicle_number,
                        Date=date,
                    ).order_by('id')  # Maintain input order

                    dest_order = []
                    trip_dict = {}

                    for trip in trips:
                        dest = trip.dest
                        if dest not in trip_dict:
                            trip_dict[dest] = []
                            dest_order.append(dest)
                        trip_dict[dest].append(trip)

                    ordered_trips = []
                    for dest in dest_order:
                        ordered_trips.extend(trip_dict[dest])

                    total_qty = sum(trip.qty or 0 for trip in ordered_trips)

                    for status in summary.keys():
                        status_trips = [trip for trip in ordered_trips if trip.pay_status == status]
                        summary[status]['freight'] = sum(trip.freight or 0 for trip in status_trips)
                        summary[status]['hamali'] = sum(trip.hamali or 0 for trip in status_trips)
                        summary[status]['st_charge'] = sum(trip.st_charge or 0 for trip in status_trips)
                        summary[status]['door_charge'] = sum(trip.door_charge or 0 for trip in status_trips)
                        summary[status]['weightAmt'] = sum(trip.weightAmt or 0 for trip in status_trips)
                        summary[status]['balance'] = sum(trip.balance or 0 for trip in status_trips)
                        summary[status]['total_cost'] = sum(trip.total_cost or 0 for trip in status_trips)

                        grand_total[status] = summary[status]['total_cost']
                        grand_total['grand_freight'] += summary[status]['freight']
                        grand_total['grand_hamali'] += summary[status]['hamali']
                        grand_total['grand_st_charge'] += summary[status]['st_charge']
                        grand_total['grand_door_charge'] += summary[status]['door_charge']
                        grand_total['grand_weightAmt'] += summary[status]['weightAmt']
                        grand_total['grand_balance'] += summary[status]['balance']
                        grand_total['grand_total'] += summary[status]['total_cost']

                    if ordered_trips:
                        first_trip = ordered_trips[0]
                        total_ltr_value = float(
                            first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
                        total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                        total_value = total_ltr_value + total_adv_given
                    else:
                        total_value = 0.0

        except Branch.DoesNotExist:
            ordered_trips = []

    return render(request, 'editTripSheetList.html', {
        'trips': trips,
        'total_value': total_value,
        'total_qty': total_qty,
        'grand_total': grand_total,
        'summary': summary
    })

def update_view(request):
    if request.method == "POST":
        trip_id = request.POST.get("trip_id")
        print(f"Received trip_id: {trip_id}")  # Debugging line

        # Fetch all records with the matching trip_id
        trips = TripSheetPrem.objects.filter(trip_id=trip_id)

        if trips.exists():
            print(f"Found {trips.count()} trip records to update")
            for trip in trips:
                # Update the fields for each trip
                trip.LTRate = request.POST.get("ltrate")
                trip.Ltr = request.POST.get("ltr")
                trip.AdvGiven = request.POST.get("advgiven")
                trip.commission = request.POST.get("commission")
                trip.save()

            # Redirect after saving
            return redirect('viewTripSheetList')  # Replace with your success URL
        else:
            print("No trip records found")
            return render(request, 'editTripSheetList.html', {'error_message': 'No trips found with the provided trip_id.'})

    return render(request, 'editTripSheetList.html')  # Replace with your template

from collections import OrderedDict

def printTripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    grand_total = {
        'ToPay': 0,
        'Paid': 0,
        'Consigner_AC': 0,
        'Consignee_AC': 0,
        'grand_freight': 0,
        'grand_hamali': 0,
        'grand_st_charge': 0,
        'grand_door_charge': 0,
        'grand_weightAmt': 0,
        'grand_balance': 0,
        'grand_total': 0
    }
    summary = {
        'ToPay': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0},
        'Paid': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0},
        'Consigner_AC': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0},
        'Consignee_AC': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0}
    }

    uid = request.session.get('username')

    if uid:
        try:
            branch = Branch.objects.get(email=uid)
            user_branch = branch.companyname

            vehical_no = request.POST.get('vehical')
            date = request.POST.get('t3')

            # Fetch trips in order of entry (not by destination)
            trips = TripSheetPrem.objects.filter(
                VehicalNo=vehical_no,
                Date=date,
            ).order_by('id')  # Order by ID to maintain input sequence

            # **Step 1: Capture first appearance order of destinations**
            dest_order = []
            trip_dict = {}

            for trip in trips:
                dest = trip.dest
                if dest not in trip_dict:
                    trip_dict[dest] = []
                    dest_order.append(dest)  # Store first appearance order
                trip_dict[dest].append(trip)

            # **Step 2: Reorder trips based on first-appearance destination order**
            ordered_trips = []
            for dest in dest_order:
                ordered_trips.extend(trip_dict[dest])  # Add all trips for this destination

            # Calculate total quantity
            total_qty = sum(trip.qty or 0 for trip in ordered_trips)

            # Aggregate data based on pay_status
            statuses = ['ToPay', 'Paid', 'Consigner_AC', 'Consignee_AC']
            for status in statuses:
                status_trips = [trip for trip in ordered_trips if trip.pay_status == status]
                summary[status]['freight'] = sum(trip.freight or 0 for trip in status_trips)
                summary[status]['hamali'] = sum(trip.hamali or 0 for trip in status_trips)
                summary[status]['st_charge'] = sum(trip.st_charge or 0 for trip in status_trips)
                summary[status]['door_charge'] = sum(trip.door_charge or 0 for trip in status_trips)
                summary[status]['weightAmt'] = sum(trip.weightAmt or 0 for trip in status_trips)
                summary[status]['balance'] = sum(trip.balance or 0 for trip in status_trips)
                summary[status]['total_cost'] = sum(trip.total_cost or 0 for trip in status_trips)

                # Update grand totals
                grand_total[status] = summary[status]['total_cost']
                grand_total['grand_freight'] += summary[status]['freight']
                grand_total['grand_hamali'] += summary[status]['hamali']
                grand_total['grand_st_charge'] += summary[status]['st_charge']
                grand_total['grand_door_charge'] += summary[status]['door_charge']
                grand_total['grand_weightAmt'] += summary[status]['weightAmt']
                grand_total['grand_balance'] += summary[status]['balance']
                grand_total['grand_total'] += summary[status]['total_cost']

            # Calculate the total value using the first row
            if ordered_trips:
                first_trip = ordered_trips[0]
                total_ltr_value = float(first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
                total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                total_value = total_ltr_value
            else:
                total_value = 0.0

        except Branch.DoesNotExist:
            ordered_trips = []  # Handle case where Branch does not exist

    return render(request, 'printTripSheetList.html', {

        'trips': trips,  # Pass ordered trips
        'total_value': total_value,
        'total_qty': total_qty,
        'grand_total': grand_total,
        'summary': summary
    })



def adminTripSheet(request):
    grouped_trips = []

    if request.method == 'POST':
        vehicle_number = request.POST.get('vehical')
        branch = request.POST.get('t2')
        date = request.POST.get('t3')

        if date:
            # Group by VehicalNo and Date, and annotate with count
            grouped_trips = (
                TripSheetPrem.objects
                .filter(Date=date, VehicalNo=vehicle_number,branch=branch)
                .values('VehicalNo', 'Date','branch')
                .annotate(trip_count=Count('id'))
            )
    return render(request, 'adminTripSheet.html', {
        'grouped_trips': grouped_trips
    })

from collections import OrderedDict

def adminPrintTripSheetList(request, vehical_no, date, branch):
    trips = []
    total_value = 0
    total_qty = 0
    grand_total = {
        'ToPay': 0,
        'Paid': 0,
        'Consigner_AC': 0,
        'Consignee_AC': 0,
        'grand_freight': 0,
        'grand_hamali': 0,
        'grand_st_charge': 0,
        'grand_door_charge': 0,
        'grand_weightAmt': 0,
        'grand_balance': 0,
        'grand_total': 0
    }
    summary = {status: {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0} for status in grand_total.keys() if status not in ['grand_freight', 'grand_hamali', 'grand_st_charge', 'grand_door_charge', 'grand_weightAmt', 'grand_balance', 'grand_total']}

    # Fetch trips and order by entry sequence
    trips = TripSheetPrem.objects.filter(
        VehicalNo=vehical_no,
        Date=date,
        branch=branch
    ).order_by('id')

    # **Step 1: Capture first appearance order of destinations**
    dest_order = []
    trip_dict = {}

    for trip in trips:
        dest = trip.dest
        if dest not in trip_dict:
            trip_dict[dest] = []
            dest_order.append(dest)
        trip_dict[dest].append(trip)

    # **Step 2: Reorder trips based on first-appearance destination order**
    ordered_trips = []
    for dest in dest_order:
        ordered_trips.extend(trip_dict[dest])

    # Calculate total quantity
    total_qty = sum(trip.qty or 0 for trip in ordered_trips)

    for status in summary.keys():
        status_trips = [trip for trip in ordered_trips if trip.pay_status == status]
        summary[status]['freight'] = sum(trip.freight or 0 for trip in status_trips)
        summary[status]['hamali'] = sum(trip.hamali or 0 for trip in status_trips)
        summary[status]['st_charge'] = sum(trip.st_charge or 0 for trip in status_trips)
        summary[status]['door_charge'] = sum(trip.door_charge or 0 for trip in status_trips)
        summary[status]['weightAmt'] = sum(trip.weightAmt or 0 for trip in status_trips)
        summary[status]['balance'] = sum(trip.balance or 0 for trip in status_trips)
        summary[status]['total_cost'] = sum(trip.total_cost or 0 for trip in status_trips)

        grand_total[status] = summary[status]['total_cost']
        grand_total['grand_freight'] += summary[status]['freight']
        grand_total['grand_hamali'] += summary[status]['hamali']
        grand_total['grand_st_charge'] += summary[status]['st_charge']
        grand_total['grand_door_charge'] += summary[status]['door_charge']
        grand_total['grand_weightAmt'] += summary[status]['weightAmt']
        grand_total['grand_balance'] += summary[status]['balance']
        grand_total['grand_total'] += summary[status]['total_cost']

    if ordered_trips:
        first_trip = ordered_trips[0]
        total_ltr_value = float(first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
        total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
        total_value = total_ltr_value
    else:
        total_value = 0.0

    return render(request, 'adminPrintTripSheetList.html', {
        'trips': trips,
        'total_value': total_value,
        'total_qty': total_qty,
        'grand_total': grand_total,
        'summary': summary
    })


def staff(request):
    if request.method == "POST":

        uid = request.session.get('username')
        branch=Branch.objects.get(email=uid)
        branchname=branch.companyname
        branchemail = branch.email

        staff = random.randint(111111, 999999)
        staffid = str(staff)

        staffname = request.POST.get('staffname')
        staffPhone = request.POST.get('staffPhone')
        staffaddress = request.POST.get('staffaddress')
        aadhar=request.POST.get('aadhar')
        passbook = request.POST.get('passbookno')

        passport = request.POST.get('passport')
        passbookphoto = request.POST.get('passport')

        passportfile = request.FILES['passport']
        fs = FileSystemStorage()
        filepassport = fs.save(passportfile.name, passportfile)
        upload_file_url = fs.url(filepassport)
        path = os.path.join(BASE_DIR, '/media/' + filepassport)

        passbookfile = request.FILES['passbook']
        fs = FileSystemStorage()
        filepassbook = fs.save(passportfile.name, passbookfile)
        upload_file_url = fs.url(filepassbook)
        path = os.path.join(BASE_DIR, '/media/' + filepassbook)

        utype = 'staff'

        if Login.objects.filter(username=staffPhone).exists():
            messages.error(request, 'Username (Phone) already exists.')
            return render(request, 'staff.html')

        Staff.objects.create(
            staffname=staffname,
            staffPhone=staffPhone,
            staffaddress=staffaddress,
            aadhar=aadhar,
            staffid=staffid,
            Branch=branchname,
            passport=passportfile,
            passbook=passbook,
            passbookphoto=passbookfile,
            branchemail=branchemail
        )
        Login.objects.create(utype=utype, username=staffPhone, password=staffid,name=staffname)

    return render(request, 'staff.html')



def view_staff(request):
    uid = request.session.get('username')
    branch = Branch.objects.get(email=uid)
    branchname = branch.companyname
    name = request.POST.get('name', '')
    if branch:
        # Filter staff data based on the branch name (case-insensitive search)
        staff_data = Staff.objects.filter(staffname__icontains=name,Branch=branchname)
    else:
        staff_data=Staff.objects.filter(Branch=branchname)
    return render(request,'view_staff.html',{'data':staff_data})

def get_staff(request):
    query = request.GET.get('query', '')
    if query:
        staffname = Staff.objects.filter(staffname__icontains=query).values_list('staffname', flat=True)
        print('Staff Name:', list(staffname))  # Debugging: check the data in the terminal
        return JsonResponse(list(staffname), safe=False)
    return JsonResponse([], safe=False)

def delete_staff(request, pk):
    try:
        staff = Staff.objects.get(id=pk)

        user = Login.objects.filter(username=staff.staffPhone).first()
        if user:
            user.delete()
        staff.delete()

    except ObjectDoesNotExist:
        pass
    base_url = reverse('view_staff')
    return redirect(base_url)

def edit_staff(request, pk):
    # Retrieve the Staff record
    data = Staff.objects.filter(id=pk).first()  # Retrieve a single object or None

    if not data:
        return HttpResponse("Staff record not found.", status=404)

    # Store the original staffPhone
    original_staffPhone = data.staffPhone

    if request.method == "POST":
        # Get updated values from the POST request
        staffname = request.POST.get('staffname')
        staffPhone = request.POST.get('staffPhone')
        staffaddress = request.POST.get('staffaddress')
        aadhar = request.POST.get('aadhar')
        staffid = request.POST.get('staffid')

        # Update the Staff object
        data.staffname = staffname
        data.staffPhone = staffPhone
        data.staffaddress = staffaddress
        data.aadhar = aadhar
        data.staffid = staffid
        data.save()

        # Update the Login record using the original staffPhone
        user = Login.objects.filter(username=original_staffPhone).first()  # Fetch the user with the original phone number
        if user:
            user.username = staffPhone  # Update username to the new phone number
            user.name = staffname  # Update name
            user.password = staffid  # Update password if necessary
            user.save()

        # Redirect to a different URL after successful update
        base_url = reverse('view_staff')
        return redirect(base_url)

    return render(request, 'edit_staff.html', {'data': data})

def staffAddTripSheet(request):
    route_to = AddConsignmentTemp.objects.values_list('route_to', flat=True).distinct()
    addtrip = defaultdict(
        lambda: {'desc_product': [], 'pieces': 0, 'receiver_name': '', 'pay_status': '', 'route_to': '', 'total': '',
                 'weightAMt': '', 'balance': '', 'freight': '', 'hamali': '', 'door_charge': '', 'st_charge': ''})
    no_data_found = False  # Flag to check if data was found

    uid = request.session.get('username')
    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch

            if request.method == 'POST':
                route_to = request.POST.get('dest')

                if user_branch:
                    consignments = AddConsignmentTemp.objects.filter(
                        route_to=route_to,
                    )

                    if consignments.exists():
                        for consignment in consignments:
                            consignment_data = addtrip[consignment.track_id]
                            consignment_data['desc_product'].append(consignment.desc_product)
                            consignment_data['pieces'] += consignment.pieces
                            consignment_data['route_to'] = consignment.route_to
                            consignment_data['receiver_name'] = consignment.receiver_name
                            consignment_data['pay_status'] = consignment.pay_status
                            consignment_data['total_cost'] = consignment.total_cost
                            consignment_data['weightAmt'] = consignment.weightAmt
                            consignment_data['freight'] = consignment.freight
                            consignment_data['hamali'] = consignment.hamali
                            consignment_data['door_charge'] = consignment.door_charge
                            consignment_data['st_charge'] = consignment.st_charge
                            consignment_data['balance'] = consignment.balance
                    else:
                        no_data_found = True  # Set the flag if no data is found

            addtrip = [
                {
                    'track_id': track_id,
                    'desc_product': ', '.join(consignment_data['desc_product']),
                    'pieces': consignment_data['pieces'],
                    'route_to': consignment_data['route_to'],
                    'receiver_name': consignment_data['receiver_name'],
                    'pay_status': consignment_data['pay_status'],
                    'total_cost': consignment_data['total_cost'],
                    'weightAmt': consignment_data['weightAmt'],
                    'freight': consignment_data['freight'],
                    'hamali': consignment_data['hamali'],
                    'door_charge': consignment_data['door_charge'],
                    'st_charge': consignment_data['st_charge'],
                    'balance': consignment_data['balance']
                }
                for track_id, consignment_data in addtrip.items()
            ]

        except Branch.DoesNotExist:
            addtrip = []
            no_data_found = True  # Set the flag if the branch does not exist

        return render(request, 'staffAddTripSheet.html', {
            'route_to': route_to,
            'trip': addtrip,
            'no_data_found': no_data_found  # Pass the flag to the template
        })

def staffsaveTripSheetList(request):
    print("staffsaveTripSheetList function called")
    if request.method == 'POST':
        print("POST request received")  # Debugging statement


        uid = request.session.get('username')
        if uid:
            try:
                branch = Staff.objects.get(staffPhone=uid)
                branchname = branch.Branch
                username = branch.staffname

                now = datetime.now()
                con_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")

                total_rows = int(request.POST.get('total_rows', 0))

                selected_rows = request.POST.getlist('selected_rows')

                for i in range(1, total_rows + 1):
                    if str(i) in selected_rows:  # Only process if the row is selected
                        track_id = request.POST.get(f'track_id_{i}')
                        pieces = request.POST.get(f'pieces_{i}')
                        desc_product = request.POST.get(f'desc_product_{i}')
                        route_to = request.POST.get(f'route_to_{i}')
                        receiver_name = request.POST.get(f'receiver_name_{i}')
                        pay_status = request.POST.get(f'pay_status_{i}')
                        total_cost = request.POST.get(f'total_cost{i}')
                        weightAmt = request.POST.get(f'weightAmt{i}')
                        freight = request.POST.get(f'freight{i}')
                        hamali = request.POST.get(f'hamali{i}')
                        door_charge = request.POST.get(f'door_charge{i}')
                        st_charge = request.POST.get(f'st_charge{i}')
                        balance = request.POST.get(f'balance{i}')

                        print(
                            f"Track ID: {track_id}, Pieces: {pieces}, Description: {desc_product}, Route: {route_to}, Receiver: {receiver_name}, Pay Status: {pay_status}, total_cost:{total_cost},weightAmt:{weightAmt},freight:{freight},hamali:{hamali},door_charge:{door_charge},st_charge:{st_charge}")  # Debugging statement

                        # Save to TripSheetTemp
                        TripSheetTemp.objects.create(
                            LRno=track_id,
                            qty=pieces,
                            desc=desc_product,
                            dest=route_to,
                            consignee=receiver_name,
                            pay_status=pay_status,
                            branch=branchname,
                            username=username,
                            Date=con_date,
                            total_cost=total_cost,
                            weightAmt=weightAmt,
                            freight=freight,
                            hamali=hamali,
                            door_charge=door_charge,
                            st_charge=st_charge,
                            balance=balance,
                        )

                        # Delete from AddConsignmentTemp
                        AddConsignmentTemp.objects.filter(track_id=track_id).delete()

                        print(f"Data for Track ID {track_id} saved and deleted from AddConsignmentTemp successfully.")  # Debugging statement
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('staffAddTripSheet')  # Replace with your desired success URL

    print("Not a POST request, redirecting back to form.")  # Debugging statement
    return render(request, 'staffAddTripSheet.html')  # Redirect back to the form if not a POST request


def staffAddTripSheetList(request):
    addtrip = []
    uid = request.session.get('username')
    no_data_found = False
    unique_destinations = []
    destination_order = {}

    if uid:
        try:
            staff = Staff.objects.get(staffPhone=uid)
            user_branch = staff.Branch
            date = request.POST.get('date') if request.method == 'POST' else None

            # Fetch trip records even for GET requests
            if date:
                consignments = TripSheetTemp.objects.filter(Date=date)
            else:
                consignments = TripSheetTemp.objects.all()

            # Extract unique destinations
            unique_destinations = list(OrderedDict.fromkeys(consignment.dest for consignment in consignments))

            if request.method == 'POST' and date:
                # Get the destination positions from the frontend
                for dest in unique_destinations:
                    pos = request.POST.get(f'position_{dest}')
                    if pos:
                        destination_order[dest] = int(pos)

                # Sort destinations by assigned position
                sorted_destinations = sorted(destination_order.keys(), key=lambda x: destination_order[x])

                # Sort trip records based on destination order
                addtrip = sorted(
                    [
                        {
                            'track_id': consignment.LRno,
                            'desc': consignment.desc,
                            'qty': consignment.qty,
                            'dest': consignment.dest,
                            'consignee': consignment.consignee,
                            'pay_status': consignment.pay_status,
                            'total_cost': consignment.total_cost,
                            'weightAmt': consignment.weightAmt,
                            'freight': consignment.freight,
                            'hamali': consignment.hamali,
                            'door_charge': consignment.door_charge,
                            'st_charge': consignment.st_charge,
                            'balance': consignment.balance,
                        }
                        for consignment in consignments
                    ],
                    key=lambda x: destination_order.get(x['dest'], float('inf'))
                )

                no_data_found = not addtrip

        except Branch.DoesNotExist:
            addtrip = []
            no_data_found = True

        # Render the template with the trip data and no_data_found flag
        return render(request, 'staffAddTripSheetList.html', {
            'trip': addtrip,
            'no_data_found': no_data_found,
            'unique_destinations': unique_destinations
        })


def staffSaveTripSheet(request):
    print("staffSaveTripSheet function called")
    if request.method == 'POST':
        print("POST request received")  # Debugging statement

        last_trip_id = TripSheetPrem.objects.aggregate(Max('trip_id'))['trip_id__max']
        trip_id = int(last_trip_id) + 1 if last_trip_id else 1000  # Start from a defined base if no entries exist
        con_id = str(trip_id)

        uid = request.session.get('username')
        if uid:
            try:
                branch = Staff.objects.get(staffPhone=uid)
                branchname = branch.Branch
                username = branch.staffname

                now = datetime.now()
                con_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")

                # Get form data
                vehicle = request.POST.get('vehical')
                drivername = request.POST.get('drivername')
                adv = request.POST.get('advance')
                ltrate = request.POST.get('ltrate') or 0
                ltr = request.POST.get('liter') or 0

                literate = float(ltrate)
                liter = float(ltr)
                diesel_total = literate * liter

                driver = Driver.objects.get(driver_name=drivername)
                phone = driver.phone_number

                # Save to Disel table
                Disel.objects.create(
                    Date=con_date,
                    vehicalno=vehicle,
                    drivername=drivername,
                    ltrate=ltrate,
                    liter=ltr,
                    total=diesel_total,  # Diesel total cost
                    trip_id=con_id
                )

                total_rows = int(request.POST.get('total_rows', 0))

                print(f"Vehicle: {vehicle}, Driver Name: {drivername}")  # Debugging statement

                for i in range(1, total_rows + 1):
                    track_id = request.POST.get(f'track_id_{i}')
                    desc = request.POST.get(f'desc_{i}')
                    qty = request.POST.get(f'qty_{i}')
                    dest = request.POST.get(f'dest_{i}')
                    consignee = request.POST.get(f'consignee_{i}')
                    total_cost = request.POST.get(f'total_cost_{i}')
                    pay_status = request.POST.get(f'pay_status_{i}')
                    weightAmt = request.POST.get(f'weightAmt_{i}')
                    freight = request.POST.get(f'freight_{i}')
                    hamali = request.POST.get(f'hamali_{i}')
                    door_charge = request.POST.get(f'door_charge_{i}')
                    st_charge = request.POST.get(f'st_charge_{i}')
                    balance = request.POST.get(f'balance_{i}')

                    print(
                        f"Track ID: {track_id}, Description: {desc}, Quantity: {qty}, Route: {dest}, Receiver: {consignee}")  # Debugging

                    # Save to TripSheetPrem
                    TripSheetPrem.objects.create(
                        LRno=track_id,
                        qty=qty,
                        desc=desc,
                        dest=dest,
                        consignee=consignee,
                        pay_status=pay_status,
                        VehicalNo=vehicle,
                        DriverName=drivername,
                        DriverNumber=phone,
                        branch=branchname,
                        username=username,
                        Date=con_date,
                        Time=current_time,
                        AdvGiven=adv,
                        LTRate=ltrate,
                        Ltr=ltr,
                        total_cost=total_cost,
                        weightAmt=float(weightAmt),
                        freight=freight,
                        hamali=hamali,
                        door_charge=door_charge,
                        st_charge=st_charge,
                        balance=balance,
                        trip_id=con_id,
                        status='TripSheet Added',
                    )

                    # Delete from AddConsignmentTemp
                    TripSheetTemp.objects.filter(LRno=track_id).delete()

                    print(f"Data for Track ID {track_id} saved successfully.")  # Debugging statement


            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
            else:
                print("No username found in session.")  # Debugging statement

    return redirect('staffAddTripSheetList')  # Replace with your desired success URL

    print("Not a POST request, redirecting back to form.")  # Debugging statement
    return render(request, 'staffAddTripSheetList.html')  # Redirect back to the form if not a POST request

def staffTripSheet(request):
    return render(request,'staffTripSheet.html')

def staffTripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    grand_total = {
        'ToPay': 0,
        'Paid': 0,
        'Consigner_AC': 0,
        'Consignee_AC': 0,
        'grand_freight': 0,
        'grand_hamali': 0,
        'grand_st_charge': 0,
        'grand_door_charge': 0,
        'grand_weightAmt': 0,
        'grand_balance': 0,
        'grand_total': 0
    }
    summary = {
        'ToPay': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0,'balance': 0, 'total_cost': 0},
        'Paid': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0,'balance': 0, 'total_cost': 0},
        'Consigner_AC': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0,'balance': 0, 'total_cost': 0},
        'Consignee_AC': {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0,'balance': 0, 'total_cost': 0}
    }

    uid = request.session.get('username')

    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch

            if request.method == 'POST':
                vehicle_number = request.POST.get('vehical')
                date = request.POST.get('t3')

                if date:
                    trips = TripSheetPrem.objects.filter(
                        VehicalNo=vehicle_number,
                        Date=date,
                    )
                    # Calculate total quantity
                    total_qty = trips.aggregate(total_qty=Sum('qty'))['total_qty'] or 0

                    # Aggregate data based on pay_status
                    statuses = ['ToPay', 'Paid', 'Consigner_AC', 'Consignee_AC']
                    for status in statuses:
                        status_trips = trips.filter(pay_status=status)
                        summary[status]['freight'] = status_trips.aggregate(total=Sum('freight'))['total'] or 0
                        summary[status]['hamali'] = status_trips.aggregate(total=Sum('hamali'))['total'] or 0
                        summary[status]['st_charge'] = status_trips.aggregate(total=Sum('st_charge'))['total'] or 0
                        summary[status]['door_charge'] = status_trips.aggregate(total=Sum('door_charge'))['total'] or 0
                        summary[status]['weightAmt'] = status_trips.aggregate(total=Sum('weightAmt'))['total'] or 0
                        summary[status]['balance'] = status_trips.aggregate(total=Sum('balance'))['total'] or 0
                        summary[status]['total_cost'] = status_trips.aggregate(total=Sum('total_cost'))['total'] or 0

                        # Update grand totals
                        grand_total[status] = summary[status]['total_cost']
                        grand_total['grand_freight'] += summary[status]['freight']
                        grand_total['grand_hamali'] += summary[status]['hamali']
                        grand_total['grand_st_charge'] += summary[status]['st_charge']
                        grand_total['grand_door_charge'] += summary[status]['door_charge']
                        grand_total['grand_weightAmt'] += summary[status]['weightAmt']
                        grand_total['grand_balance'] += summary[status]['balance']
                        grand_total['grand_total'] += summary[status]['total_cost']

                    # Calculate the total value using the first row
                    if trips.exists():
                        first_trip = trips.first()
                        total_ltr_value = float(
                            first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
                        total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                        total_value = total_ltr_value + total_adv_given
                    else:
                        total_value = 0.0

        except ObjectDoesNotExist:
            trips = TripSheetTemp.objects.none()

    return render(request, 'staffTripSheetList.html', {
        'trips': trips,
        'total_value': total_value,
        'total_qty': total_qty,
        'grand_total': grand_total,
        'summary': summary
    })

def staffViewTripSheetList(request):
    grouped_trips = []
    uid = request.session.get('username')

    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch

            if request.method == 'POST':
                date = request.POST.get('t3')

                if date:
                    # Group by VehicalNo and Date, and annotate with count
                    grouped_trips = (
                        TripSheetPrem.objects
                        .filter(Date=date)
                        .values('VehicalNo', 'Date')
                        .annotate(trip_count=Count('id'))
                    )

        except ObjectDoesNotExist:
            grouped_trips = []

    return render(request, 'staffViewTripSheetList.html', {
        'grouped_trips': grouped_trips
    })

from collections import OrderedDict

def staffprintTripSheetList(request):
    trips = []
    total_value = 0
    total_qty = 0
    grand_total = {
        'ToPay': 0,
        'Paid': 0,
        'Consigner_AC': 0,
        'Consignee_AC': 0,
        'grand_freight': 0,
        'grand_hamali': 0,
        'grand_st_charge': 0,
        'grand_door_charge': 0,
        'grand_weightAmt': 0,
        'grand_balance': 0,
        'grand_total': 0
    }
    summary = {status: {'freight': 0, 'hamali': 0, 'st_charge': 0, 'door_charge': 0, 'weightAmt': 0, 'total_cost': 0, 'balance': 0} for status in grand_total.keys() if status not in ['grand_freight', 'grand_hamali', 'grand_st_charge', 'grand_door_charge', 'grand_weightAmt', 'grand_balance', 'grand_total']}

    uid = request.session.get('username')

    if uid:
        try:
            branch = Staff.objects.get(staffPhone=uid)
            user_branch = branch.Branch

            vehical_no = request.POST.get('vehical')
            date = request.POST.get('t3')

            # Fetch trips and order by entry sequence
            trips = TripSheetPrem.objects.filter(
                VehicalNo=vehical_no,
                Date=date,
            ).order_by('id')

            # **Step 1: Capture first appearance order of destinations**
            dest_order = []
            trip_dict = {}

            for trip in trips:
                dest = trip.dest
                if dest not in trip_dict:
                    trip_dict[dest] = []
                    dest_order.append(dest)
                trip_dict[dest].append(trip)

            # **Step 2: Reorder trips based on first-appearance destination order**
            ordered_trips = []
            for dest in dest_order:
                ordered_trips.extend(trip_dict[dest])

            # Calculate total quantity
            total_qty = sum(trip.qty or 0 for trip in ordered_trips)

            for status in summary.keys():
                status_trips = [trip for trip in ordered_trips if trip.pay_status == status]
                summary[status]['freight'] = sum(trip.freight or 0 for trip in status_trips)
                summary[status]['hamali'] = sum(trip.hamali or 0 for trip in status_trips)
                summary[status]['st_charge'] = sum(trip.st_charge or 0 for trip in status_trips)
                summary[status]['door_charge'] = sum(trip.door_charge or 0 for trip in status_trips)
                summary[status]['weightAmt'] = sum(trip.weightAmt or 0 for trip in status_trips)
                summary[status]['balance'] = sum(trip.balance or 0 for trip in status_trips)
                summary[status]['total_cost'] = sum(trip.total_cost or 0 for trip in status_trips)

                grand_total[status] = summary[status]['total_cost']
                grand_total['grand_freight'] += summary[status]['freight']
                grand_total['grand_hamali'] += summary[status]['hamali']
                grand_total['grand_st_charge'] += summary[status]['st_charge']
                grand_total['grand_door_charge'] += summary[status]['door_charge']
                grand_total['grand_weightAmt'] += summary[status]['weightAmt']
                grand_total['grand_balance'] += summary[status]['balance']
                grand_total['grand_total'] += summary[status]['total_cost']

            if ordered_trips:
                first_trip = ordered_trips[0]
                total_ltr_value = float(first_trip.LTRate * first_trip.Ltr) if first_trip.LTRate and first_trip.Ltr else 0.0
                total_adv_given = float(first_trip.AdvGiven) if first_trip.AdvGiven else 0.0
                total_value = total_ltr_value
            else:
                total_value = 0.0

        except Staff.DoesNotExist:
            ordered_trips = []

    return render(request, 'staffprintTripSheetList.html', {
        'trips': trips,
        'total_value': total_value,
        'total_qty': total_qty,
        'grand_total': grand_total,
        'summary': summary
    })


def fetch_consignments(request):
    consignments = AddConsignment.objects.all()
    consignments_data = [
        {
            'id': consignment.id,
            'track_id': consignment.track_id,
            'sender_name': consignment.sender_name,
            'receiver_name': consignment.receiver_name,
        }
        for consignment in consignments
    ]
    return JsonResponse(consignments_data, safe=False)



def fetch_details(request):
    uid = request.session.get('username')

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    pay_status = request.GET.get('pay_status')
    consignor_id = request.GET.get('consignor_id')
    consignee_id = request.GET.get('consignee_id')

    # Initialize an empty queryset
    consignments = AddConsignment.objects.none()
    data = []
    if uid:
        try:
            # Fetch the branch of the logged-in user
            branch = Staff.objects.get(staffPhone=uid).Branch

            # Start with filtering consignments by branch
            consignments = AddConsignment.objects.filter(branch=branch)

            # Further filter consignments based on the provided parameters
            if consignor_id:
                consignments = consignments.filter(sender_name__icontains=consignor_id)
            if consignee_id:
                consignments = consignments.filter(receiver_name__icontains=consignee_id)
            if from_date and to_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                consignments = consignments.filter(date__range=(from_date, to_date))

            # Handle pay_status filtering
            if pay_status and pay_status != 'all':
                consignments = consignments.filter(pay_status__icontains=pay_status)

            # Group consignments by track_id
            grouped_data = defaultdict(lambda: {
                'track_id': '',
                'sender_name': '',
                'receiver_name': '',
                'desc_product': '',
                'pay_status': '',
                'pieces': '',
                'total_cost': 0
            })

            for consignment in consignments:
                track_id = consignment.track_id
                if track_id not in grouped_data:
                    grouped_data[track_id]['track_id'] = track_id
                    grouped_data[track_id]['sender_name'] = consignment.sender_name
                    grouped_data[track_id]['receiver_name'] = consignment.receiver_name
                    grouped_data[track_id]['pay_status'] = consignment.pay_status
                    grouped_data[track_id]['total_cost'] = consignment.total_cost

                # Concatenate pieces and desc_product as strings
                if grouped_data[track_id]['pieces']:
                    grouped_data[track_id]['pieces'] += consignment.pieces
                else:
                    grouped_data[track_id]['pieces'] = consignment.pieces

                if grouped_data[track_id]['desc_product']:
                    grouped_data[track_id]['desc_product'] += ', ' + consignment.desc_product
                else:
                    grouped_data[track_id]['desc_product'] = consignment.desc_product

            # Prepare the data for JSON response
            data = list(grouped_data.values())
        except Staff.DoesNotExist:
            print("Staff does not exist for the provided uid.")  # Handle case where Staff does not exist

    return JsonResponse({'data': data})

def branchfetch_details(request):
    uid = request.session.get('username')

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    pay_status = request.GET.get('pay_status')
    consignor_id = request.GET.get('consignor_id')
    consignee_id = request.GET.get('consignee_id')

    # Initialize data and consignments
    consignments = AddConsignment.objects.none()
    data = []

    if uid:
        try:
            # Fetch the branch of the logged-in user
            branch = Branch.objects.get(email=uid)
            uname = branch.companyname

            # Start with filtering consignments by branch
            consignments = AddConsignment.objects.filter(branch=uname)

            # Further filter consignments based on the provided parameters
            if consignor_id:
                consignments = consignments.filter(sender_name__icontains=consignor_id)
            if consignee_id:
                consignments = consignments.filter(receiver_name__icontains=consignee_id)
            if from_date and to_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                consignments = consignments.filter(date__range=(from_date, to_date))
            if pay_status and pay_status != 'all':
                consignments = consignments.filter(pay_status__icontains=pay_status)

            # Group consignments by track_id
            grouped_data = defaultdict(lambda: {
                'track_id': '',
                'sender_name': '',
                'receiver_name': '',
                'desc_product': '',
                'pay_status': '',
                'pieces': '',
                'total_cost': 0
            })

            for consignment in consignments:
                track_id = consignment.track_id
                if track_id not in grouped_data:
                    grouped_data[track_id]['track_id'] = track_id
                    grouped_data[track_id]['sender_name'] = consignment.sender_name
                    grouped_data[track_id]['receiver_name'] = consignment.receiver_name
                    grouped_data[track_id]['pay_status'] = consignment.pay_status
                    grouped_data[track_id]['total_cost'] = consignment.total_cost

                # Concatenate pieces and desc_product as strings
                if grouped_data[track_id]['pieces']:
                    grouped_data[track_id]['pieces'] += consignment.pieces
                else:
                    grouped_data[track_id]['pieces'] = consignment.pieces

                if grouped_data[track_id]['desc_product']:
                    grouped_data[track_id]['desc_product'] += ', ' + consignment.desc_product
                else:
                    grouped_data[track_id]['desc_product'] = consignment.desc_product

                # Sum up total costs

            # Prepare the data for JSON response
            data = list(grouped_data.values())
        except Branch.DoesNotExist:
            print("Branch does not exist for the provided uid.")  # Handle case where Branch does not exist

    # Include the uid in the response data
    return JsonResponse({'uid': uid, 'data': data})


def payment_history(request):
    return render(request, 'payment_history.html')

def credit(request):
    credit = Account.objects.all()
    return render(request, 'credit.html', {'credit': credit})

@csrf_exempt
def fetch_balance(request):
    uid = request.session.get('username')

    if uid:
        try:
            # Fetch the branch of the logged-in user
            branch = Staff.objects.get(staffPhone=uid).Branch

            if request.method == 'GET':
                sender_name = request.GET.get('sender_name')
                if sender_name:
                    # Filter accounts by sender_name and branch
                    accounts = Account.objects.filter(sender_name=sender_name, Branch=branch)
                    if accounts.exists():
                        latest_account = accounts.latest('Date')  # Get the latest record by date
                        return JsonResponse({'balance': latest_account.Balance})
                    return JsonResponse({'balance': '0'})  # Default if no records found
                return JsonResponse({'status': 'error', 'message': 'Sender name is required'})
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
        except Branch.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Branch does not exist for this user'})


@csrf_exempt
def submit_credit(request):
    if request.method == 'POST':
        uid = request.session.get('username')

        consignor_name = request.POST.get('consignor_name')
        credit_amount = request.POST.get('credit_amount')
        desc = request.POST.get('desc')
        now = datetime.now().replace(microsecond=0)

        if consignor_name and credit_amount:
            try:

                branch = Staff.objects.get(staffPhone=uid)
                username = branch.staffname
                branchname=branch.Branch
                # Fetch all matching records
                accounts = Account.objects.filter(sender_name=consignor_name)

                if accounts.exists():
                    # Get the latest account for calculating the new balance
                    latest_account = accounts.latest('Date')  # Assuming you want to get the latest record

                    # Calculate the new balance
                    new_balance = float(latest_account.Balance) - float(credit_amount)

                    # Create a new record with updated balance
                    new_account = Account(
                        sender_name=consignor_name,
                        credit=credit_amount,
                        debit='0',
                        TrType="ReCap",
                        particulars=desc,# Set debit to zero
                        Balance=str(new_balance),  # Set the new balance
                        Date=now,  # Use the date of the latest record or set to current date
                        headname=username,
                        Branch=branchname
                    )
                    new_account.save()

                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No account found with the given sender name'})

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'error', 'message': 'Invalid data'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



def credit_print(request):
    credit = Account.objects.all()
    return render(request, 'credit_print.html', {'credit': credit})




@csrf_exempt
def branchfetch_balance(request):
    uid = request.session.get('username')

    if uid:
        try:
            # Fetch the branch of the logged-in user
            branch = Branch.objects.get(email=uid).companyname

            if request.method == 'GET':
                sender_name = request.GET.get('sender_name')
                if sender_name:
                    # Filter accounts by sender_name and branch
                    accounts = Account.objects.filter(sender_name=sender_name, Branch=branch)
                    if accounts.exists():
                        latest_account = accounts.latest('Date')  # Get the latest record by date
                        return JsonResponse({'balance': latest_account.Balance})
                    return JsonResponse({'balance': '0'})  # Default if no records found
                return JsonResponse({'status': 'error', 'message': 'Sender name is required'})
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
        except Branch.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Branch does not exist for this user'})

def branchPaymenyHistory(request):
    return render(request,'branchPaymenyHistory.html')

def branchcredit(request):
    credit = Account.objects.all()
    return render(request, 'branchcredit.html', {'credit': credit})

import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def branchsubmit_credit(request):
    if request.method == 'POST':
        uid = request.session.get('username')

        consignor_name = request.POST.get('consignor_name')
        credit_amount = request.POST.get('credit_amount')
        desc = request.POST.get('desc')
        now = datetime.now().replace(microsecond=0)

        if consignor_name and credit_amount:
            try:

                branch = Branch.objects.get(email=uid)
                username = branch.headname
                branchcompany =branch.companyname
                # Fetch all matching records
                accounts = Account.objects.filter(sender_name=consignor_name)

                if accounts.exists():
                    # Get the latest account for calculating the new balance
                    latest_account = accounts.latest('Date')  # Assuming you want to get the latest record

                    # Calculate the new balance
                    new_balance = float(latest_account.Balance) - float(credit_amount)

                    # Create a new record with updated balance
                    new_account = Account(
                        sender_name=consignor_name,
                        credit=credit_amount,
                        debit='0',
                        TrType="ReCap",
                        particulars=desc,# Set debit to zero
                        Balance=str(new_balance),  # Set the new balance
                        Date=now,  # Use the date of the latest record or set to current date
                        headname=username,
                        Branch=branchcompany
                    )
                    new_account.save()

                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'No account found with the given sender name'})

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

        return JsonResponse({'status': 'error', 'message': 'Invalid data'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



def branchcredit_print(request):
    credit = Account.objects.all()
    return render(request, 'branchcredit_print.html', {'credit': credit})

def staffcredit_print(request):
    credit = Account.objects.all()
    return render(request, 'staffcredit_print.html', {'credit': credit})

# Set up logging
import logging

logger = logging.getLogger(__name__)

def branchfetch_account_details(request):
    if request.method == 'POST':
        uid = request.session.get('username')

        sender_name = request.POST.get('sender_name')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')

        logger.info(f"Received request with sender_name: {sender_name}, from_date: {from_date}, to_date: {to_date}")

        # Check if the required parameters are provided
        if sender_name and from_date and to_date:
            try:
                branch = Branch.objects.get(email=uid).companyname

                # Convert from_date and to_date to proper datetime objects
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()

                # Ensure the end date includes the entire day
                to_date_end = to_date + timedelta(days=1)

                # Fetch all accounts based on sender_name, branch, and date range
                accounts = Account.objects.filter(
                    sender_name=sender_name,
                    Branch=branch,
                    Date__gte=from_date,
                    Date__lt=to_date_end
                ).values(
                    'Date', 'track_number', 'TrType', 'particulars', 'debit', 'credit', 'Balance'
                ).order_by('Date')  # Order by date if needed

                logger.info(f"Fetched accounts: {list(accounts)}")

                return render(request, 'branchcredit_print.html', {
                    'accounts': accounts,
                    'sender_name': sender_name,
                    'from_date_str': from_date,
                    'to_date_str': to_date,
                    'branch': branch
                })

            except ValueError:
                logger.error("Invalid date format")
                return render(request, 'branchcredit_print.html', {'error': 'Invalid date format'})

    logger.error("Missing required parameters")
    return render(request, 'branchcredit_print.html', {'error': 'Missing required parameters'})


logger = logging.getLogger(__name__)

@csrf_exempt
def fetch_account_details(request):
    if request.method == 'POST':

        uid = request.session.get('username')

        sender_name = request.POST.get('sender_name')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')

        logger.info(f"Received request with sender_name: {sender_name}, from_date: {from_date}, to_date: {to_date}")

        # Check if the required parameters are provided
        if sender_name and from_date and to_date:
            try:
                branch = Staff.objects.get(staffPhone=uid).Branch

                # Convert from_date and to_date to proper datetime objects
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()

                # Ensure the end date includes the entire day
                to_date_end = to_date + timedelta(days=1)

                # Fetch all accounts based on sender_name, branch, and date range
                accounts = Account.objects.filter(
                    sender_name=sender_name,
                    Branch=branch,
                    Date__gte=from_date,
                    Date__lt=to_date_end
                ).values(
                    'Date', 'track_number', 'TrType', 'particulars', 'debit', 'credit', 'Balance'
                ).order_by('Date')  # Order by date if needed

                logger.info(f"Fetched accounts: {list(accounts)}")

                return render(request, 'staffcredit_print.html', {
                    'accounts': accounts,
                    'sender_name': sender_name,
                    'from_date_str': from_date,
                    'to_date_str': to_date,
                    'branch': branch
                })

            except ValueError:
                logger.error("Invalid date format")
                return render(request, 'staffcredit_print.html', {'error': 'Invalid date format'})

    logger.error("Missing required parameters")
    return render(request, 'staffcredit_print.html', {'error': 'Missing required parameters'})


def branchExpenses(request):
    return render(request, 'branchExpenses.html')
def savebranchExpenses(request):
    if request.method == 'POST':
        uid = request.session.get('username')
        if uid:
            try:
                branch = Branch.objects.get(email=uid)
                branchname = branch.companyname
                username = branch.headname

                # Parse and validate date
                date_str = request.POST.get('date')
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    print("Invalid date format.")  # Debugging statement
                    return redirect('branchExpenses')

                # Parse and validate amount
                amount = request.POST.get('amt')
                reason = request.POST.get('reason')


                Expenses.objects.create(
                    Date=date,
                    Reason=reason,
                    Amount=amount,

                    username=username,
                    branch=branchname
                )
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('branchExpenses')  # Replace with your desired success URL

    return render(request, 'branchExpenses.html')


def branchViewExpenses(request):
    expenses = []
    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        uid = request.session.get('username')
        if uid:
            try:
                branch = Branch.objects.get(email=uid)  # Get the branch for the logged-in user
                branch_name = branch.companyname  # Assuming companyname is used as the branch identifier

                if from_date_str and to_date_str:
                    try:
                        # Parse the date strings into datetime objects
                        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

                        # Fetch expenses within the specified date range and for the logged-in branch
                        expenses = Expenses.objects.filter(
                            Date__range=(from_date, to_date),
                            branch=branch_name
                        )

                    except ValueError:
                        print("Invalid date format.")  # Handle invalid date formats
                else:
                    print("Both from_date and to_date are required.")
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Handle the case where the branch is not found

    return render(request, 'branchViewExpenses.html', {'expenses': expenses})

def adminExpenses(request):
    return render(request, 'adminExpenses.html')
def saveadminExpenses(request):
    if request.method == 'POST':
        uid = request.session.get('username')
        if uid:
            try:
                branch = Login.objects.get(username=uid)
                branchname = branch.utype
                username = branch.name

                # Parse and validate date
                date_str = request.POST.get('date')
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    print("Invalid date format.")  # Debugging statement
                    return redirect('adminExpenses')

                amount = request.POST.get('amt')
                reason = request.POST.get('reason')
                salaryDetails=request.POST.get('salaryDetails')

                Expenses.objects.create(
                    Date=date,
                    Reason=reason,
                    Amount=amount,
                    staffname=salaryDetails,
                    username=username,
                    branch=branchname
                )
            except Branch.DoesNotExist:
                print("Branch does not exist.")  # Debugging statement
        else:
            print("No username found in session.")  # Debugging statement

        return redirect('adminExpenses')  # Replace with your desired success URL

    return render(request, 'adminExpenses.html')

def adminViewExpenses(request):
    expenses = []
    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        if from_date_str and to_date_str:
            try:
                # Parse the date strings into datetime objects
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()


                expenses = Expenses.objects.filter(Date__range=(from_date, to_date))

            except ValueError:
                print("Invalid date format.")  # Handle invalid date formats
        else:
            print("Both from_date and to_date are required.")
    return render(request, 'adminViewExpenses.html', {'expenses': expenses})

def branchConsignorView(request):
    uid = request.session.get('username')
    if uid:
        branch = Branch.objects.get(email=uid)
        branchname = branch.companyname
        consignor=Consignor.objects.filter(branch=branchname)
    return render(request,'branchConsignorView.html',{'consignor':consignor})

def branchConsigneeView(request):
    uid = request.session.get('username')
    if uid:
        branch = Branch.objects.get(email=uid)
        branchname = branch.companyname
        consignee = Consignee.objects.filter(branch=branchname)
    return render(request,'branchConsigneeView.html',{'consignee':consignee})

def adminConsignorView(request):
    consignor = []  # Initialize consignee as an empty list

    if request.method == 'POST':
        branch = request.POST.get('t2')
        print(f"Branch: {branch}")  # Debugging: Print the branch name
        consignor = Consignor.objects.filter(branch=branch)
        print(f"Consignee: {consignor}")  # Debugging: Print the consignee queryset

    return render(request,'adminConsignorView.html',{'consignor':consignor})


def adminConsigneeView(request):
    consignee = []  # Initialize consignee as an empty list

    if request.method == 'POST':
        branch = request.POST.get('t2')
        print(f"Branch: {branch}")  # Debugging: Print the branch name
        consignee = Consignee.objects.filter(branch=branch)
        print(f"Consignee: {consignee}")  # Debugging: Print the consignee queryset

    return render(request, 'adminConsigneeView.html', {'consignee': consignee})

def adminstaff_view(request):
    branch = request.POST.get('branch', '')
    if branch:
        # Filter staff data based on the branch name (case-insensitive search)
        staff_data = Staff.objects.filter(Branch__icontains=branch)
    else:
        # If no branch is provided, fetch all staff data
        staff_data = Staff.objects.all()

    # Render the template with the filtered data
    return render(request, 'adminstaff_view.html', {'data': staff_data, 'branch': branch})


from django.utils.dateparse import parse_date


def adminView_Consignment(request):
    grouped_userdata = {}  # Initialize as an empty dictionary to group data

    # Fetch all consignments initially
    queryset = AddConsignment.objects.all()

    if request.method == 'POST':
        # Get filter criteria from the POST data
        branch = request.POST.get('t2')
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')
        consigner = request.POST.get('consigner')
        consignee = request.POST.get('consignee')
        track_id = request.POST.get('lrno')

        # Parse dates
        from_date = parse_date(from_date_str) if from_date_str else None
        to_date = parse_date(to_date_str) if to_date_str else None

        # Apply filters only if there is a POST request
        if branch:
            queryset = queryset.filter(branch=branch)
        if consigner:
            queryset = queryset.filter(sender_name=consigner)
        if consignee:
            queryset = queryset.filter(receiver_name=consignee)
        if track_id:
            queryset = queryset.filter(track_id=track_id)

        if from_date and to_date:
            queryset = queryset.filter(date__range=(from_date, to_date))
        elif from_date:
            queryset = queryset.filter(date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(date__lte=to_date)

    # Group consignments by track_id and concatenate product details
    for consignment in queryset:
        track_id = consignment.track_id
        if track_id not in grouped_userdata:
            grouped_userdata[track_id] = {
                'branch': consignment.branch,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'sender_name': consignment.sender_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_name': consignment.receiver_name,
                'receiver_mobile': consignment.receiver_mobile,
                'total_cost': consignment.total_cost,
                'pieces': 0,
                'weight': consignment.weight,
                'pay_status': consignment.pay_status,
                'consignment_status': consignment.consignment_status,
                'products': []
            }
        # Aggregate total cost and pieces
        grouped_userdata[track_id]['pieces'] += consignment.pieces

        # Concatenate product details without ID
        product_detail = consignment.desc_product
        grouped_userdata[track_id]['products'].append(product_detail)

    # Convert the list of product details to a single string
    for track_id, details in grouped_userdata.items():
        details['products'] = ', '.join(details['products'])

    return render(request, 'adminView_Consignment.html', {'grouped_userdata': grouped_userdata})


def toggle_consignment_status(request, track_id):
    # Fetch the consignment by track_id
    consignment = get_object_or_404(AddConsignment, track_id=track_id)

    # Toggle the status between 'Completed' and 'Pending'
    if consignment.consignment_status == 'Complete':
        consignment.consignment_status = 'Pending'
    else:
        consignment.consignment_status = 'Complete'

    # Save the updated status
    consignment.save()

    # Redirect back to the consignment status page
    return redirect('adminView_Consignment')

def admininvoiceConsignment(request, track_id):
    grouped_userdata = {}
    copy_types = []
    totalqty = 0  # Initialize total quantity


    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)
        # Get common details from the first consignment
        consignment = consignments.first()

        # Fetch the branch name from the consignment
        branch_name = consignment.branch  # Adjust this field based on your model
        branchemail = consignment.branchemail
        # Fetch branch details using the branch name
        branchdetails = get_object_or_404(Branch, email=branchemail)

        if not consignments.exists():
            return render(request, '404.html')  # Handle case where no consignments are found.

        # Loop over each consignment item to gather details individually
        for consignment in consignments:
            if consignment.track_id not in grouped_userdata:
                # Initialize data structure for each track_id
                grouped_userdata[consignment.track_id] = {
                    field.name: getattr(consignment, field.name) for field in AddConsignment._meta.fields
                }
                grouped_userdata[consignment.track_id]['consignment_list'] = []  # To store individual products

            # Add each consignment's product details as a separate entry
            consignment_details = {
                'pieces': consignment.pieces,
                'desc_product': consignment.desc_product,

            }
            grouped_userdata[consignment.track_id]['consignment_list'].append(consignment_details)

            totalqty += consignment.pieces  # Sum up the pieces for total quantity


            if consignment.copy_type not in copy_types:
                copy_types.append(consignment.copy_type)

    except ObjectDoesNotExist:
        grouped_userdata = {}

    return render(request, 'admininvoiceConsignment.html', {
        'grouped_userdata': grouped_userdata,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types), # Include the aggregated copy types
        'totalqty': totalqty  # Pass total quantity to the template

    })


def staffinvoiceConsignment(request, track_id):
    # Filter consignments by track_id
    consignments = AddConsignment.objects.filter(track_id=track_id)
    uid = request.session.get('username')
    branchname=Staff.objects.get(staffPhone=uid)
    branch=branchname.Branch
    branchdetails = Branch.objects.get(companyname=branch)

    if not consignments.exists():
        return render(request, '404.html')  # Handle the case where no consignments are found.

    # Get common details from the first consignment
    consignment = consignments.first()

    # Collect copy_types from all consignments with the same track_id
    copy_types = consignments.values_list('copy_type', flat=True).distinct()

    # Convert the queryset to a list and join them into a single string for display
    copy_type_list = ', '.join(copy_types)

    # Pass the first consignment, the entire list of items, and the copy types to the template
    return render(request, 'staffinvoiceConsignment.html', {
        'consignment': consignment,
        'items': consignments,
        'branchdetails': branchdetails,
        'copy_types': copy_type_list  # Include the aggregated copy types
    })

def partywise_list(request):
    # Get filter values from the request
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    sender_name = request.GET.get('sender_name')
    receiver_name = request.GET.get('consignee')

    # Start building the query
    queryset = AddConsignment.objects.all()

    # Apply date range filter if both from_date and to_date are provided
    if from_date_str and to_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

            # Filter the queryset by the date range
            queryset = queryset.filter(date__range=(from_date, to_date))
        except ValueError:
            return render(request, 'partywise_report.html', {
                'error': 'Invalid date format.'
            })

    # Apply sender_name filter if provided
    if sender_name:
        queryset = queryset.filter(sender_name__icontains=sender_name)
    if receiver_name:
        queryset = queryset.filter(receiver_name__icontains=receiver_name)

    # Group by sender_name and calculate sum of pieces, total cost, and count of track_id
    consignments_by_sender = queryset.values('sender_name').annotate(
        total_pieces=Sum('pieces'),
        total_cost=Sum('total_cost'),
        track_id_count=Count('track_id', distinct=True)
    ).order_by('sender_name')

    # Pass the aggregated data to the template
    context = {
        'consignments_by_sender': consignments_by_sender,
        'from_date': from_date_str,
        'to_date': to_date_str,
        'sender_name': sender_name,    }

    return render(request, 'partywise_report.html', context)



def partywise_detail(request, sender_name):
    # Get filter values from the request
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    # Start building the query
    consignments = AddConsignment.objects.filter(sender_name=sender_name)

    # Apply date range filter if both from_date and to_date are provided
    if from_date_str and to_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()

            # Filter the queryset by the date range
            consignments = consignments.filter(date__range=(from_date, to_date))
        except ValueError:
            return render(request, 'partywise_detail.html', {
                'error': 'Invalid date format.',
                'sender_name': sender_name,
            })

    if not consignments.exists():
        return render(request, 'partywise_detail.html', {'error': 'No consignments found for this sender.'})

    # Aggregate details based on Consignment_id
    aggregated_data = consignments.values(
        'Consignment_id',
        'track_id',
        'sender_name',
        'sender_mobile',
        'sender_address',
        'receiver_name',
        'receiver_mobile',
        'receiver_address',
        'date',
        'route_from',
        'route_to',
        'prod_invoice',
        'prod_price',
        'branch',
        'name',
        'time',
        'copy_type',
        'delivery',
        'eway_bill'
    ).annotate(
        total_cost=Sum('total_cost'),
        pieces=Sum('pieces'),
        weight=Sum('weight'),
        freight=Sum('freight'),
        hamali=Sum('hamali'),
        door_charge=Sum('door_charge'),
        st_charge=Sum('st_charge'),
        weightAmt=Sum('weightAmt'),
    ).order_by('Consignment_id')

    # Create a list of dictionaries for the final data to be displayed
    detailed_data = []
    for consignment in aggregated_data:
        descriptions = consignments.filter(Consignment_id=consignment['Consignment_id']).values_list('desc_product', flat=True)
        # Append each description with aggregated data
        detailed_data.append({
            **consignment,
            'desc_products': descriptions
        })

    # Calculate total pieces for the sender
    total_pieces = consignments.aggregate(total_pieces=Sum('pieces'))['total_pieces'] or 0

    return render(request, 'partywise_detail.html', {
        'sender_name': sender_name,
        'consignments': detailed_data,
        'total_pieces': total_pieces
    })


def disel_report(request):
    # Retrieve date parameters from the GET request
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    # Convert date strings to datetime objects
    if from_date_str and to_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
        except ValueError:
            # Handle incorrect date format
            return render(request, 'disel_report.html', {
                'data': [],
                'total_litres': 0,
                'total_amount': 0,
                'error_message': 'Invalid date format. Use YYYY-MM-DD.'
            })

        # Filter data based on date range and total > 0
        data = Disel.objects.filter(Date__range=[from_date, to_date], total__gt=0)
    else:
        # If no dates are provided, show all data where total > 0
        data = Disel.objects.filter(total__gt=0)

    # Calculate the total litres and amount
    total_litres = data.aggregate(Sum('liter'))['liter__sum'] or 0
    total_amount = data.aggregate(Sum('total'))['total__sum'] or 0

    # Pass data and totals to the template
    return render(request, 'disel_report.html', {
        'data': data,
        'total_litres': total_litres,
        'total_amount': total_amount,
        'error_message': ''
    })

def account_report(request):
    credit = Account.objects.all()
    return render(request, 'account_report.html', {'credit':credit})

@csrf_exempt
def adminfetch_account_details(request):
    if request.method == 'POST':


        sender_name = request.POST.get('sender_name')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')

        logger.info(f"Received request with sender_name: {sender_name}, from_date: {from_date}, to_date: {to_date}")

        # Check if the required parameters are provided
        if sender_name and from_date and to_date:
            try:

                # Convert from_date and to_date to proper datetime objects
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()

                # Ensure the end date includes the entire day
                to_date_end = to_date + timedelta(days=1)

                # Fetch all accounts based on sender_name, branch, and date range
                accounts = Account.objects.filter(
                    sender_name=sender_name,
                    Date__gte=from_date,
                    Date__lt=to_date_end
                ).values(
                    'Date', 'track_number', 'TrType', 'particulars', 'debit', 'credit', 'Balance'
                ).order_by('Date')  # Order by date if needed

                logger.info(f"Fetched accounts: {list(accounts)}")

                return render(request, 'account_report.html', {
                    'accounts': accounts,
                    'sender_name': sender_name,
                    'from_date_str': from_date,
                    'to_date_str': to_date,
                    'branch': branch
                })

            except ValueError:
                logger.error("Invalid date format")
                return render(request, 'account_report.html', {'error': 'Invalid date format'})

    logger.error("Missing required parameters")
    return render(request, 'account_report.html', {'error': 'Missing required parameters'})


def get_account_details(request):
    branch = request.GET.get('branch', '')
    if branch:
        accounts = Account.objects.filter(Branch__icontains=branch)
        accounts_data = list(accounts.values('track_number', 'sender_name', 'Branch', 'headname', 'TrType', 'debit', 'credit', 'Balance'))
        return JsonResponse(accounts_data, safe=False)
    return JsonResponse([], safe=False)

def unloaded_LR_report(request):
    # Extract query parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    route_to = request.GET.get('dest')  # Get route_to/destination filter

    # Initialize variables for start_date and end_date
    start_date = None
    end_date = None

    # Convert string dates to datetime objects
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            pass  # Handle invalid date format if necessary

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            pass  # Handle invalid date format if necessary

    # If end_date is provided, extend it to the end of the day
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Filter consignments based on date range and route_to
    consignments = AddConsignmentTemp.objects.all()

    if start_date:
        consignments = consignments.filter(date__gte=start_date)

    if end_date:
        consignments = consignments.filter(date__lte=end_date)

    if route_to:  # Apply filter for route_to if provided
        consignments = consignments.filter(route_to__icontains=route_to)

    # Render the template with the filtered consignments
    return render(request, 'unloaded_LR_report.html', {'consignments': consignments})



def advance_report(request):
    driver_name = request.GET.get('driver_name')
    vehicalno = request.GET.get('vehicalno')  # Fixed name to match form
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    # Convert date strings to date objects
    from_date = datetime.strptime(from_date_str, '%Y-%m-%d') if from_date_str else None
    to_date = datetime.strptime(to_date_str, '%Y-%m-%d') if to_date_str else None

    # Initialize the filters dictionary
    filters = {}
    if driver_name:
        filters['DriverName__iexact'] = driver_name  # Case-insensitive driver name filter
    if vehicalno:
        filters['VehicalNo__iexact'] = vehicalno  # Case-insensitive vehicle number filter
    if from_date and to_date:
        filters['Date__range'] = [from_date, to_date]

    # Add the condition for AdvGiven to be more than 0
    filters['AdvGiven__gt'] = 0

    # Fetch the results based on the filters and group by trip_id
    results = TripSheetPrem.objects.filter(**filters).values(
        'trip_id', 'VehicalNo', 'DriverName', 'AdvGiven', 'Date'  # Include the fields you need
    ).annotate(
        total_advances=Count('AdvGiven')
    ).order_by('trip_id')

    if not results:
        print("No results found")

    return render(request, 'advance_report.html', {
        'results': results,
        'vehicalno': vehicalno,
        'driver_name': driver_name,
        'from_date': from_date_str,
        'to_date': to_date_str
    })


def profit_report(request):
    # Get the from_date and to_date from the request (if provided)
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    from_date = parse_date(from_date_str) if from_date_str else None
    to_date = parse_date(to_date_str) if to_date_str else None

    # Query all consignments and expenses
    consignments = AddConsignment.objects.all()
    expenses = Expenses.objects.all()

    # Filter by date range if provided
    if from_date and to_date:
        consignments = consignments.filter(date__range=[from_date, to_date])
        expenses = expenses.filter(Date__range=[from_date, to_date])

    # Track already processed track_ids
    processed_track_ids = set()

    # This list will store the unique consignments
    unique_consignments = []

    # Iterate over all consignments to ensure only unique track_id costs are added
    for consignment in consignments:
        track_id = consignment.track_id
        # If track_id is not already processed, add its total_cost to the unique list
        if track_id not in processed_track_ids:
            processed_track_ids.add(track_id)
            unique_consignments.append(consignment)

    # Now group by date and branch, summing the total_cost of the unique consignments
    consignments_grouped = (
        AddConsignment.objects.filter(id__in=[c.id for c in unique_consignments])
        .values('date', 'branch')
        .annotate(total_cost=Sum('total_cost'))
        .order_by('date', 'branch')
    )

    # Group expenses by date and branch, and calculate total Amount for each group
    expenses_grouped = expenses.values('Date', 'branch').annotate(
        total_amount=Sum('Amount')
    ).order_by('Date', 'branch')

    # Calculate grand totals for consignments and expenses
    grand_total_consignment = sum(item['total_cost'] for item in consignments_grouped)
    grand_total_expenses = sum(item['total_amount'] for item in expenses_grouped)

    # Calculate combined grand total
    combined_grand_total = grand_total_consignment + grand_total_expenses

    # Calculate profit or loss
    total_balance = grand_total_consignment - grand_total_expenses

    # Set profit and loss
    profit = total_balance if total_balance > 0 else 0
    loss = abs(total_balance) if total_balance < 0 else 0

    # Pass the grouped data and totals to the template
    return render(request, 'profit_report.html', {
        'consignments': consignments_grouped,
        'expenses': expenses_grouped,
        'grand_total_consignment': grand_total_consignment,
        'grand_total_expenses': grand_total_expenses,
        'combined_grand_total': combined_grand_total,
        'profit': profit,
        'loss': loss,
        'from_date': from_date_str,
        'to_date': to_date_str,
    })


def get_balance(request):
    cust_id = request.GET.get('cust_id')  # Get cust_id from the query parameters
    if cust_id:
        try:
            # Fetch the most recent balance for the given cust_id
            collections = Collection.objects.filter(cust_id=cust_id,consignment_status='Complete')

            # Sum all balances for the given cust_id
            total_balance = collections.aggregate(Sum('balance'))['balance__sum'] or 0

            return JsonResponse({'balance': str(total_balance)})
        except Exception as e:  # Catch any unexpected exceptions
            return JsonResponse({'balance': None, 'error': str(e)})
    return JsonResponse({'balance': None})  # Return None if cust_id is not provided


def consignmentStatus(request):
    grouped_userdata = {}  # Initialize as an empty dictionary to group data

    # Fetch all 'Pending' consignments by default
    queryset = AddConsignment.objects.filter(consignment_status='Pending')

    # Check if it's a POST request to apply date filtering
    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        # Parse dates
        from_date = parse_date(from_date_str) if from_date_str else None
        to_date = parse_date(to_date_str) if to_date_str else None

        # Apply date range filtering if dates are provided
        if from_date and to_date:
            queryset = queryset.filter(date__range=(from_date, to_date))
        elif from_date:
            queryset = queryset.filter(date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(date__lte=to_date)

    # Group consignments by track_id and concatenate product details
    for consignment in queryset:
        track_id = consignment.track_id
        if track_id not in grouped_userdata:
            grouped_userdata[track_id] = {
                'branch': consignment.branch,
                'route_from': consignment.route_from,
                'route_to': consignment.route_to,
                'sender_name': consignment.sender_name,
                'sender_mobile': consignment.sender_mobile,
                'receiver_name': consignment.receiver_name,
                'receiver_mobile': consignment.receiver_mobile,
                'total_cost': 0,
                'pieces': 0,
                'weight': consignment.weight,
                'pay_status': consignment.pay_status,
                'consignment_status': consignment.consignment_status,
                'products': []
            }
        # Aggregate total cost and pieces
        grouped_userdata[track_id]['total_cost'] += consignment.total_cost
        grouped_userdata[track_id]['pieces'] += consignment.pieces

        # Concatenate product details
        product_detail = consignment.desc_product
        grouped_userdata[track_id]['products'].append(product_detail)

    # Convert the list of product details to a single string
    for track_id, details in grouped_userdata.items():
        details['products'] = ', '.join(details['products'])

    return render(request, 'consignmentStatus.html', {'grouped_userdata': grouped_userdata})


def complete_consignment(request, track_id):
    # Get the consignment object using the track_id
    consignment = get_object_or_404(AddConsignment, track_id=track_id)

    # Update the consignment_status to "Complete"
    consignment.consignment_status = "Complete"
    consignment.save()  # Save the changes to the AddConsignment model

    # Check if the track_id exists in the Collection table
    try:
        collection = Collection.objects.get(lrNo=track_id)
        # If found, update the consignment_status in the Collection table
        collection.consignment_status = "Complete"
        collection.save()  # Save the changes to the Collection model
    except Collection.DoesNotExist:
        # If the Collection entry does not exist, do nothing
        pass

    # Redirect or respond back after completion
    return redirect('consignmentStatus')  # Replace 'consignmentStatus' with the correct URL name

def collection(request):
    grouped_userdata = {}  # Initialize as an empty dictionary to group data

    if request.method == 'POST':
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')

        # Retrieve consignment objects with consignment_status='Complete'
        con = AddConsignment.objects.all()
        track_ids = con.values_list('track_id', flat=True)  # Fetch track_id from consignment queryset

        # Parse dates
        from_date = parse_date(from_date_str) if from_date_str else None
        to_date = parse_date(to_date_str) if to_date_str else None

        print(f"From Date: {from_date}")  # Debugging: Print the from date
        print(f"To Date: {to_date}")  # Debugging: Print the to date

        # Start building the query to fetch from Collection where track_id matches and balance > 0
        queryset = Collection.objects.filter(balance__gt=0, lrNo__in=track_ids)

        if from_date and to_date:
            queryset = queryset.filter(date__range=(from_date, to_date))
        elif from_date:
            queryset = queryset.filter(date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(date__lte=to_date)

        print(f"Filtered Consignments: {queryset}")  # Debugging: Print the filtered queryset

        # Group consignments by track_id and concatenate product details
        for consignment in queryset:
            lrNo = consignment.lrNo
            if lrNo not in grouped_userdata:
                grouped_userdata[lrNo] = {
                    'branch': consignment.branch,
                    'lrNo': consignment.lrNo,
                    'sender_name': consignment.sender_name,
                    'pay_status': consignment.pay_status,
                    'total': consignment.total,
                    'amount': consignment.amount,
                    'balance': consignment.balance,
                    'consignment_status': consignment.consignment_status,
                }

    return render(request, 'collection.html', {'grouped_userdata': grouped_userdata})


def save_payment(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON request body
            data = json.loads(request.body)
            track_id = data.get('track_id')
            amount = data.get('amount')
            desc = data.get('desc')
            prev_amount =data.get('amount')

            # Validate amount
            if amount is None or amount == '':
                return JsonResponse({'success': False, 'error': 'Amount is required'})


            amount = float(amount)  # Convert to float after validation

            # Fetch the existing collection entry by track_id
            collection = Collection.objects.get(lrNo=track_id)
            sendername = collection.sender_name

            # Update the amount and balance for Collection
            collection.amount += amount  # Assuming amount is cumulative
            collection.balance -= amount  # Reduce balance by the paid amount
            collection.desc = desc  # Reduce balance by the paid amount
            collection.save()

            return JsonResponse({'success': True})

        except Collection.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Collection entry not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


def cancel_trip(request, trip_id):
    trip = get_object_or_404(TripSheetPrem, LRno=trip_id)
    con = get_object_or_404(AddConsignment, track_id=trip_id)

    # Copy the trip data to TripSheetTemp
    AddConsignmentTemp.objects.create(
        track_id=con.track_id,
        Consignment_id=con.Consignment_id,
        sender_name=con.sender_name,
        sender_mobile=con.sender_mobile,
        sender_address=con.sender_address,
        sender_GST=con.sender_GST,
        receiver_name=con.receiver_name,
        receiver_mobile=con.receiver_mobile,
        receiver_address=con.receiver_address,
        receiver_GST=con.receiver_GST,
        desc_product=con.desc_product,
        pieces=con.pieces,
        prod_invoice=con.prod_invoice,
        prod_price=con.prod_price,
        weightAmt=con.weightAmt,
        weight=con.weight,
        balance=con.balance,
        freight=con.freight,
        hamali=con.hamali,
        door_charge=con.door_charge,
        st_charge=con.st_charge,
        route_from=con.route_from,
        route_to=con.route_to,
        total_cost=con.total_cost,
        date=con.date,
        pay_status=con.pay_status,
        branch=con.branch,
        name=con.name,
        time=con.time,
        copy_type=con.copy_type,
        delivery=con.delivery,
        eway_bill=con.eway_bill
    )

    # Optionally, mark the trip as cancelled (if needed for other logic)
    trip.is_cancelled = True
    trip.save()

    # Remove the trip record from TripSheetPrem after saving
    trip.delete()

    messages.success(request, f"Trip {trip.LRno} has been cancelled, saved in TripSheetTemp, and removed from TripSheetPrem.")
    return redirect('viewTripSheetList')  # Replace with the actual view name if needed

def customerLogin(request):
    if request.method == 'POST':
        # Get the email from the frontend
        email = request.POST.get('email')

        # Check if the email exists in the UserLogin table
        try:
            user = UserLogin.objects.get(email=email)
            # Save email in session
            request.session['user_email'] = email
            # Redirect to CustomerHome page
            return redirect('customerHome')  # Replace 'customer_home' with your URL name for the CustomerHome page
        except UserLogin.DoesNotExist:
            # Email does not exist, show an error message
            messages.error(request, "Email not found. Please try again.")
            return render(request, 'customerLogin.html')  # Render the login page again

    # Render the login page for GET requests
    return render(request, 'customerLogin.html')


def customerHome(request):
    return render(request,'customerHome.html')

def customerConsignment(request):
    uid = request.session.get('user_email')  # Get email from session
    grouped_userdata = {}

    if uid:
        try:
            # First, check if the email is in the Consignor table
            consignor = Consignor.objects.filter(sender_mobile=uid).first()

            if consignor:
                # If it's in the Consignor table, fetch consignments based on sender_mobile
                user_branch = consignor.sender_mobile
                consignments = AddConsignment.objects.filter(sender_mobile=user_branch, consignment_status='Pending')

                # Loop over consignments and get their track_id
                for consignment in consignments:
                    track_id = consignment.track_id

                    # Fetch the trip details related to the consignment's track_id
                    trips = TripSheetPrem.objects.filter(LRno=track_id)

                    # If it's not already in grouped_userdata, initialize it
                    if track_id not in grouped_userdata:
                        grouped_userdata[track_id] = {
                            'route_from': consignment.route_from,
                            'route_to': consignment.route_to,
                            'sender_name': consignment.sender_name,
                            'sender_mobile': consignment.sender_mobile,
                            'receiver_name': consignment.receiver_name,
                            'receiver_mobile': consignment.receiver_mobile,
                            'total_cost': consignment.total_cost,
                            'pieces': 0,  # Aggregate pieces
                            'weight': consignment.weight,
                            'pay_status': consignment.pay_status,
                            'status': consignment.status,
                            'date': consignment.date,
                            'time': consignment.time,
                            'products': [],  # Aggregate product details
                            'trip_details': []  # Initialize a place to store trip details
                        }

                    # Aggregate total pieces at the consignment level
                    grouped_userdata[track_id]['pieces'] += consignment.pieces
                    # Concatenate product details without ID
                    product_detail = consignment.desc_product
                    grouped_userdata[track_id]['products'].append(product_detail)

                    # Add trip details for this consignment
                    for trip in trips:
                        trip_detail = {
                            'Date': trip.Date,
                            'Time': trip.Time,
                            'VehicalNo': trip.VehicalNo,
                            'DriverName': trip.DriverName,  # Assuming this field exists
                            'DriverNumber': trip.DriverNumber,  # Assuming this field exists
                            'sender_name': consignment.sender_name,
                            'receiver_name': consignment.receiver_name,
                            'route_from': consignment.route_from,
                            'route_to': consignment.route_to,
                            'pieces': consignment.pieces,  # Correctly assign pieces here from the consignment
                            'products': consignment.desc_product,  # Assign product details here
                        }
                        grouped_userdata[track_id]['trip_details'].append(trip_detail)

            else:
                # If not found in Consignor, check the Consignee table
                consignee = Consignee.objects.filter(receiver_mobile=uid).first()

                if consignee:
                    # If it's in the Consignee table, fetch consignments based on receiver_mobile
                    user_branch = consignee.receiver_mobile
                    consignments = AddConsignment.objects.filter(receiver_mobile=user_branch, consignment_status='Pending')

                    # Loop over consignments and get their track_id
                    for consignment in consignments:
                        track_id = consignment.track_id

                        # Fetch the trip details related to the consignment's track_id
                        trips = TripSheetPrem.objects.filter(LRno=track_id)

                        # If it's not already in grouped_userdata, initialize it
                        if track_id not in grouped_userdata:
                            grouped_userdata[track_id] = {
                                'route_from': consignment.route_from,
                                'route_to': consignment.route_to,
                                'sender_name': consignment.sender_name,
                                'sender_mobile': consignment.sender_mobile,
                                'receiver_name': consignment.receiver_name,
                                'receiver_mobile': consignment.receiver_mobile,
                                'total_cost': consignment.total_cost,
                                'pieces': 0,  # Aggregate pieces
                                'weight': consignment.weight,
                                'pay_status': consignment.pay_status,
                                'status': consignment.status,
                                'date': consignment.date,
                                'time': consignment.time,
                                'products': [],  # Aggregate product details
                                'trip_details': []  # Initialize a place to store trip details
                            }

                        # Aggregate total pieces at the consignment level
                        grouped_userdata[track_id]['pieces'] += consignment.pieces
                        # Concatenate product details without ID
                        product_detail = consignment.desc_product
                        grouped_userdata[track_id]['products'].append(product_detail)

                        # Add trip details for this consignment
                        for trip in trips:
                            trip_detail = {
                                'Date': trip.Date,
                                'Time': trip.Time,
                                'VehicalNo': trip.VehicalNo,
                                'DriverName': trip.DriverName,  # Assuming this field exists
                                'DriverNumber': trip.DriverNumber,  # Assuming this field exists
                                'sender_name': consignment.sender_name,
                                'receiver_name': consignment.receiver_name,
                                'route_from': consignment.route_from,
                                'route_to': consignment.route_to,
                                'pieces': consignment.pieces,  # Correctly assign pieces here from the consignment
                                'products': consignment.desc_product,  # Assign product details here
                            }
                            grouped_userdata[track_id]['trip_details'].append(trip_detail)

                else:
                    # If email is not found in either table, return empty
                    consignments = []
                    trips = []

        except ObjectDoesNotExist:
            # Handle case if neither Consignor nor Consignee exists for the uid
            pass

    # Convert the list of product details to a single string
    for track_id, details in grouped_userdata.items():
        details['products'] = ', '.join(details['products'])

    # Render the template with consignment and trip data
    return render(request, 'customerConsignment.html', {'grouped_userdata': grouped_userdata})

from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.core.exceptions import ObjectDoesNotExist
from .models import AddConsignment, Branch  # Adjust the import paths to your project structure

def downloadInvoice(request, track_id):
    grouped_userdata = {}
    copy_types = []
    totalqty = 0  # Initialize total quantity
    branchdetails = None  # Initialize branchdetails as None in case it's not found

    try:
        # Filter consignments by track_id
        consignments = AddConsignment.objects.filter(track_id=track_id)

        # Get the first consignment's branch (assuming all consignments for a track_id have the same branch)
        first_consignment = consignments.first()

        if first_consignment:
            bname = first_consignment.branch  # Access the branch from the first consignment

            if bname:
                try:
                    # Get branch details from the Branch model based on the branch name (as a string)
                    branchdetails = Branch.objects.get(companyname=bname)
                except Branch.DoesNotExist:
                    branchdetails = None  # If branch doesn't exist, set branchdetails to None

        # Loop over each consignment item to gather details individually
        for consignment in consignments:
            if consignment.track_id not in grouped_userdata:
                # Initialize data structure for each track_id
                grouped_userdata[consignment.track_id] = {
                    field.name: getattr(consignment, field.name) for field in AddConsignment._meta.fields
                }
                grouped_userdata[consignment.track_id]['consignment_list'] = []  # To store individual products

            # Add each consignment's product details as a separate entry
            consignment_details = {
                'pieces': consignment.pieces,
                'sender_name': consignment.sender_name,
                'sender_address': consignment.sender_address,
                'sender_GST': consignment.sender_GST,
                'sender_mobile': consignment.sender_mobile,
                'receiver_name': consignment.receiver_name,
                'receiver_address': consignment.receiver_address,
                'receiver_GST': consignment.receiver_GST,
                'receiver_mobile': consignment.receiver_mobile,
                'desc_product': consignment.desc_product,
                'weight': consignment.weight,
                'weightAmt': consignment.weightAmt,
                'prod_invoice': consignment.prod_invoice,
                'prod_price': consignment.prod_price,
                'total_cost': consignment.total_cost,
                'freight': consignment.freight,
                'hamali': consignment.hamali,
                'door_charge': consignment.door_charge,
                'st_charge': consignment.st_charge,
                'balance': consignment.balance,
                'consignment_status': consignment.consignment_status,
                'eway_bill': consignment.eway_bill,
                'delivery': consignment.delivery,
                'date': consignment.date,
                'time': consignment.time,
            }

            # Append consignment details for this track_id
            grouped_userdata[consignment.track_id]['consignment_list'].append(consignment_details)
            totalqty += consignment.pieces  # Sum up the pieces for total quantity

            if consignment.copy_type not in copy_types:
                copy_types.append(consignment.copy_type)

    except ObjectDoesNotExist:
        grouped_userdata = {}

    # Render the HTML content from the template
    html_content = render_to_string('downloadInvoice.html', {
        'grouped_userdata': grouped_userdata,
        'branchdetails': branchdetails,
        'copy_types': ', '.join(copy_types),
        'totalqty': totalqty
    })

    # Create the HTTP response for the PDF download
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{track_id}.pdf"'

    # Convert HTML to PDF using xhtml2pdf
    pisa_status = pisa.CreatePDF(html_content, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response

from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# Endpoint to check if location sharing is active
def check_location_sharing_status(request):
    phone_number = request.GET.get("phone_number", "")
    if not phone_number:
        return JsonResponse({"status": "error", "message": "Phone number is required."})

    try:
        driver = Driver.objects.get(phone_number=phone_number)
        location = DriverLocation.objects.filter(driver=driver, location_sharing_active=True).last()

        if location:
            return JsonResponse({"status": "success", "location_sharing_active": True})
        else:
            return JsonResponse({"status": "success", "location_sharing_active": False})

    except Driver.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Driver not found."})


# Endpoint to start location sharing
@csrf_exempt
def start_location_sharing(request, phone_number):
    try:
        driver = Driver.objects.get(phone_number=phone_number)
    except Driver.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Driver not found."})

    # Activate location sharing
    DriverLocation.objects.create(
        driver=driver,
        latitude=0,  # Placeholder for initial location
        longitude=0,  # Placeholder for initial location
        timestamp=timezone.now(),
        location_sharing_active=True
    )

    return JsonResponse({"status": "success", "message": "Location sharing started."})


# Endpoint to stop location sharing
@csrf_exempt
def stop_location_sharing(request, phone_number):
    try:
        driver = Driver.objects.get(phone_number=phone_number)
    except Driver.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Driver not found."})

    # Deactivate location sharing by updating the latest location entry
    last_location = DriverLocation.objects.filter(driver=driver, location_sharing_active=True).last()
    if last_location:
        last_location.location_sharing_active = False
        last_location.save()

    return JsonResponse({"status": "success", "message": "Location sharing stopped."})


# Endpoint to update the driver's location
@csrf_exempt
def update_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get("phone_number")
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            timestamp = data.get("timestamp")

            # Check if required data is missing
            if not phone_number or not latitude or not longitude or not timestamp:
                return JsonResponse({"status": "error", "message": "Missing required fields."})

            # Validate the latitude and longitude values
            if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
                return JsonResponse({"status": "error", "message": "Invalid latitude or longitude format."})

            if latitude == 0 or longitude == 0:
                return JsonResponse({"status": "error", "message": "Invalid location (latitude or longitude cannot be zero)."})

            # Check if the driver exists
            try:
                driver = Driver.objects.get(phone_number=phone_number)
            except Driver.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Driver not found."})

            # Save or update the driver's location in the DriverLocation table
            location, created = DriverLocation.objects.update_or_create(
                driver=driver,
                defaults={
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": timestamp,
                    "location_sharing_active": True,  # Ensure sharing is active
                }
            )

            return JsonResponse({"status": "success", "message": "Location updated successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format."})

    return JsonResponse({"status": "error", "message": "Invalid request method."})

def location(request):
    uid = request.session.get('username')
    return render(request,'update_location.html',{'uid':uid})

def track_driver(request):
    driver = None
    location = None

    phone_number = request.GET.get('phone_number')  # Get the phone number from the query parameters

    if phone_number:
        # Fetch the driver using the phone number
        driver = get_object_or_404(Driver, phone_number=phone_number)

        # Try to get the latest location or return None if no location exists
        location = DriverLocation.objects.filter(driver=driver).order_by('-timestamp').first()

    # Pass the driver and location to the template
    return render(request, 'track_driver.html', {
        'driver': driver,
        'location': location,
    })

def admintrack_driver(request):
    driver = None
    location = None

    phone_number = request.GET.get('phone_number')  # Get the phone number from the query parameters

    if phone_number:
        # Fetch the driver using the phone number
        driver = get_object_or_404(Driver, phone_number=phone_number)

        # Try to get the latest location or return None if no location exists
        location = DriverLocation.objects.filter(driver=driver).order_by('-timestamp').first()

    # Pass the driver and location to the template
    return render(request, 'admintrack_driver.html', {
        'driver': driver,
        'location': location,
    })

def save_credit_ledger(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        credit = request.POST.get('credit', '')
        credit_desc = request.POST.get('creditDesc', '')
        credit_amt = request.POST.get('creditAmt', 0) or 0
        """Function to save a credit ledger entry"""
        Creditledger.objects.create(
            date=date,
            type='Credit',
            credit=credit,
            creditDesc=credit_desc,
            creditAmt=credit_amt,
        )
        return redirect('cashledger_form')

def save_debit_ledger(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        debit = request.POST.get('debit', '')
        debit_desc = request.POST.get('debitDesc', '')
        debit_amt = request.POST.get('debitAmt', 0) or 0
        """Function to save a debit ledger entry"""
        Debitledger.objects.create(
            date=date,
            debit=debit,
            debitDesc=debit_desc,
            debitAmt=debit_amt,
        )
        return redirect('cashledger_form')

def cashledger_form(request):
    return render(request, 'cashLedger.html')

from django.http import HttpResponse
from itertools import zip_longest

from django.db.models import Sum
def combined_ledger_view(request):
    # Get date filters from the request
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Fetch credit and debit data with filters
    credit_query = Creditledger.objects.all()
    debit_query = Debitledger.objects.all()

    if from_date and to_date:
        credit_query = credit_query.filter(date__range=[from_date, to_date])
        debit_query = debit_query.filter(date__range=[from_date, to_date])

    # Convert to lists to ensure individual rows
    credit_data = list(credit_query.values('date', 'credit', 'creditDesc', 'creditAmt'))
    debit_data = list(debit_query.values('date', 'debit', 'debitDesc', 'debitAmt'))

    # Combine credit and debit data row-wise
    combined_data = []
    for credit, debit in zip_longest(credit_data, debit_data, fillvalue={}):
        combined_data.append({
            'date': credit.get('date') or debit.get('date'),
            'credit': credit.get('credit', ''),
            'creditDesc': credit.get('creditDesc', ''),
            'total_credit': credit.get('creditAmt', 0),
            'debit': debit.get('debit', ''),
            'debitDesc': debit.get('debitDesc', ''),
            'total_debit': debit.get('debitAmt', 0),
            'difference': credit.get('creditAmt', 0) - debit.get('debitAmt', 0),
        })

    # Calculate grand totals
    grand_total_credit = sum(data['total_credit'] for data in combined_data)
    grand_total_debit = sum(data['total_debit'] for data in combined_data)
    grand_total_difference = grand_total_credit - grand_total_debit

    # Handle Excel export
    if request.GET.get('export') == 'excel':
        return export_to_excel_cash(combined_data, grand_total_credit, grand_total_debit, grand_total_difference)

    # Pass data to the template
    context = {
        'combined_data': combined_data,
        'grand_total_credit': grand_total_credit,
        'grand_total_debit': grand_total_debit,
        'grand_total_difference': grand_total_difference,
    }
    return render(request, 'ledger.html', context)
from openpyxl import Workbook


def export_to_excel_cash(combined_data, grand_total_credit, grand_total_debit, grand_total_difference):
    # Create an Excel workbook and sheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Combined Ledger"

    # Add header row
    headers = [
        "Date", "Credit", "Credit Description", "Total Credit",
        "Debit", "Debit Description", "Total Debit", "Difference (Credit - Debit)"
    ]
    sheet.append(headers)

    # Add data rows
    for data in combined_data:
        sheet.append([
            data['date'],
            data['credit'],
            data['creditDesc'],
            data['total_credit'],
            data['debit'],
            data['debitDesc'],
            data['total_debit'],
            data['difference'],
        ])

    # Add grand totals
    sheet.append([])
    sheet.append([
        "Grand Totals", "", "", grand_total_credit, "", "", grand_total_debit, grand_total_difference
    ])

    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Combined_Ledger.xlsx'
    workbook.save(response)
    return response

@csrf_exempt
def delete_consignment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        lr_no = data.get("track_id")  # Assuming 'track_id' is the LRno from TripSheetTemp

        try:
            # Fetch the consignment from TripSheetTemp
            consignment = TripSheetTemp.objects.get(LRno=lr_no)

            # Find all matching records in AddConsignment
            matching_records = AddConsignment.objects.filter(track_id=lr_no)

            if not matching_records.exists():
                return JsonResponse({"success": False, "error": "No matching records found in AddConsignment."})

            # Save each matching record to AddConsignmentTemp
            for record in matching_records:
                AddConsignmentTemp.objects.create(
                    track_id=record.track_id,
                    sender_name=record.sender_name,
                    sender_mobile=record.sender_mobile,
                    sender_address=record.sender_address,
                    sender_GST=record.sender_GST,
                    receiver_name=record.receiver_name,
                    receiver_mobile=record.receiver_mobile,
                    receiver_address=record.receiver_address,
                    receiver_GST=record.receiver_GST,
                    total_cost=record.total_cost,
                    date=record.date,
                    pay_status=record.pay_status,
                    route_from=record.route_from,
                    route_to=record.route_to,
                    desc_product=record.desc_product,
                    pieces=record.pieces,
                    prod_invoice=record.prod_invoice,
                    prod_price=record.prod_price,
                    weight=record.weight,
                    freight=record.freight,
                    hamali=record.hamali,
                    door_charge=record.door_charge,
                    st_charge=record.st_charge,
                    Consignment_id=record.Consignment_id,
                    branch=record.branch,
                    name=record.name,
                    balance=record.balance,
                    time=record.time,
                    copy_type=record.copy_type,
                    weightAmt=record.weightAmt,
                    delivery=record.delivery,
                    eway_bill=record.eway_bill,
                )

            # Delete the consignment from TripSheetTemp
            consignment.delete()

            return JsonResponse({"success": True})
        except TripSheetTemp.DoesNotExist:
            return JsonResponse({"success": False, "error": "Consignment not found in TripSheetTemp."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})

@csrf_exempt
def staffdelete_consignment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        lr_no = data.get("track_id")  # Assuming 'track_id' is the LRno from TripSheetTemp

        try:
            # Fetch the consignment from TripSheetTemp
            consignment = TripSheetTemp.objects.get(LRno=lr_no)

            # Find all matching records in AddConsignment
            matching_records = AddConsignment.objects.filter(track_id=lr_no)

            if not matching_records.exists():
                return JsonResponse({"success": False, "error": "No matching records found in AddConsignment."})

            # Save each matching record to AddConsignmentTemp
            for record in matching_records:
                AddConsignmentTemp.objects.create(
                    track_id=record.track_id,
                    sender_name=record.sender_name,
                    sender_mobile=record.sender_mobile,
                    sender_address=record.sender_address,
                    sender_GST=record.sender_GST,
                    receiver_name=record.receiver_name,
                    receiver_mobile=record.receiver_mobile,
                    receiver_address=record.receiver_address,
                    receiver_GST=record.receiver_GST,
                    total_cost=record.total_cost,
                    date=record.date,
                    pay_status=record.pay_status,
                    route_from=record.route_from,
                    route_to=record.route_to,
                    desc_product=record.desc_product,
                    pieces=record.pieces,
                    prod_invoice=record.prod_invoice,
                    prod_price=record.prod_price,
                    weight=record.weight,
                    freight=record.freight,
                    hamali=record.hamali,
                    door_charge=record.door_charge,
                    st_charge=record.st_charge,
                    Consignment_id=record.Consignment_id,
                    branch=record.branch,
                    name=record.name,
                    balance=record.balance,
                    time=record.time,
                    copy_type=record.copy_type,
                    weightAmt=record.weightAmt,
                    delivery=record.delivery,
                    eway_bill=record.eway_bill,
                )

            # Delete the consignment from TripSheetTemp
            consignment.delete()

            return JsonResponse({"success": True})
        except TripSheetTemp.DoesNotExist:
            return JsonResponse({"success": False, "error": "Consignment not found in TripSheetTemp."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})
