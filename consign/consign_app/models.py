from django.db import models
from django.contrib.auth.models import User

class Login(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    name = models.CharField(max_length=50,null=True)
    utype = models.CharField(max_length=50)

class AddTrack(models.Model):
    track_id = models.CharField(max_length=50, null=True)
    date = models.CharField(max_length=30, null=True)
    description = models.CharField(max_length=30, null=True)
    branch=models.CharField(max_length=100,null=True)

class Branch(models.Model):
    headname = models.CharField(max_length=150, null=True)
    companyname = models.CharField(max_length=50, null=True)
    phonenumber = models.CharField(max_length=50, null=True)
    email = models.CharField(max_length=50, null=True)
    gst = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=50, null=True)
    password = models.CharField(max_length=50, null=True)
    services = models.CharField(max_length=500, null=True)
    agency = models.CharField(max_length=500, null=True)

class Location(models.Model):
    location = models.CharField(max_length=200,null=True)

class AddConsignment(models.Model):
    track_id = models.CharField(max_length=50, null=True)
    sender_name = models.CharField(max_length=50, null=True)
    sender_mobile = models.CharField(max_length=50, null=True)
    sender_address = models.CharField(max_length=50, null=True)
    sender_GST=models.CharField(max_length=50,null=True)
    receiver_name = models.CharField(max_length=50, null=True)
    receiver_mobile = models.CharField(max_length=50, null=True)
    receiver_address = models.CharField(max_length=50, null=True)
    receiver_GST = models.CharField(max_length=50, null=True)
    total_cost = models.FloatField(null=True)
    date = models.CharField(max_length=30, null=True)
    pay_status = models.CharField(max_length=30, null=True)
    route_from = models.CharField(max_length=30, null=True)
    route_to = models.CharField(max_length=30, null=True)
    desc_product = models.CharField(max_length=150,null=True)
    pieces = models.IntegerField(null=True)
    prod_invoice = models.CharField(max_length=50,null=True)
    prod_price = models.CharField(max_length=50,null=True)
    weight = models.FloatField(null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    st_charge = models.FloatField(null=True)
    Consignment_id=models.IntegerField(null=True)
    branch = models.CharField(max_length=150, null=True)
    name = models.CharField(max_length=150, null=True)
    balance = models.FloatField(null=True)
    time=models.CharField(max_length=50,null=True)
    copy_type = models.CharField(max_length=150, null=True)
    weightAmt=models.FloatField(null=True)
    delivery = models.CharField(max_length=150, null=True)
    eway_bill =models.CharField(max_length=150, null=True)
    branchemail = models.CharField(max_length=150, null=True)
    consignment_status = models.CharField(max_length=250, null=True)
    status = models.CharField(max_length=250, null=True)


    def __str__(self):
        return self.track_id

class AddConsignmentTemp(models.Model):
    track_id = models.CharField(max_length=50, null=True)
    sender_name = models.CharField(max_length=50, null=True)
    sender_mobile = models.CharField(max_length=50, null=True)
    sender_address = models.CharField(max_length=50, null=True)
    sender_GST=models.CharField(max_length=50,null=True)
    receiver_name = models.CharField(max_length=50, null=True)
    receiver_mobile = models.CharField(max_length=50, null=True)
    receiver_address = models.CharField(max_length=50, null=True)
    receiver_GST = models.CharField(max_length=50, null=True)
    total_cost = models.FloatField(null=True)
    date = models.DateField( null=True)
    pay_status = models.CharField(max_length=30, null=True)
    route_from = models.CharField(max_length=30, null=True)
    route_to = models.CharField(max_length=30, null=True)
    desc_product = models.CharField(max_length=150,null=True)
    pieces = models.IntegerField(null=True)
    prod_invoice = models.CharField(max_length=50,null=True)
    prod_price = models.CharField(max_length=50,null=True)
    weight = models.FloatField(null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    st_charge = models.FloatField(null=True)
    Consignment_id=models.IntegerField(null=True)
    branch = models.CharField(max_length=150, null=True)
    name = models.CharField(max_length=150, null=True)
    balance = models.FloatField(null=True)
    time = models.CharField(max_length=50,null=True)
    copy_type = models.CharField(max_length=150,null=True)
    weightAmt = models.FloatField(null=True)
    delivery = models.CharField(max_length=150, null=True)
    eway_bill =models.CharField(max_length=150, null=True)




class Consignor(models.Model):
    sender_name = models.CharField(max_length=50, null=True)
    sender_mobile = models.CharField(max_length=50, null=True)
    sender_email = models.CharField(max_length=50, null=True)
    sender_address = models.CharField(max_length=50, null=True)
    sender_company=models.CharField(max_length=50,null=True)
    sender_GST=models.CharField(max_length=50,null=True)
    cust_id = models.IntegerField(null=True)
    branch=models.CharField(max_length=50,null=True)



class Consignee(models.Model):
    receiver_name = models.CharField(max_length=50, null=True)
    receiver_mobile = models.CharField(max_length=50, null=True)
    receiver_email = models.CharField(max_length=50, null=True)
    receiver_address = models.CharField(max_length=50, null=True)
    receiver_company = models.CharField(max_length=50, null=True)
    receiver_GST = models.CharField(max_length=50, null=True)
    cust_id = models.IntegerField(null=True)
    branch=models.CharField(max_length=50,null=True)



class FeedBack(models.Model):
    username=models.CharField(max_length=50,null=True)
    feedback=models.CharField(max_length=200,null=True)
    def __str__(self):
        return self.username


class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=50, null=True)
    rccard = models.ImageField(max_length=50, null=True)
    rccardate = models.DateField(null=True)
    incurence = models.ImageField(max_length=50, null=True)
    incurencedate = models.DateField(null=True)
    permit = models.ImageField(max_length=50, null=True)
    permitdate = models.DateField(null=True)
    tax = models.ImageField(max_length=50, null=True)
    taxdate = models.DateField(null=True)
    emission = models.ImageField(max_length=50, null=True)
    emissiondate = models.DateField(null=True)


class Driver(models.Model):
    driver_name = models.CharField(max_length=50, null=True)
    phone_number = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=50, null=True)
    passport = models.ImageField(max_length=50, null=True)
    license = models.ImageField(max_length=50, null=True)
    aadhar = models.ImageField(max_length=50, null=True)
    location_sharing_active = models.CharField(max_length=100, null=True)


class Staff(models.Model):
    staffname = models.CharField(max_length=150, null=True)
    staffPhone = models.CharField(max_length=150, null=True)
    staffaddress = models.CharField(max_length=150, null=True)
    aadhar = models.CharField(max_length=150, null=True)
    staffid = models.CharField(max_length=150, null=True)
    Branch = models.CharField(max_length=150, null=True)
    passbook = models.CharField(max_length=150, null=True)
    passbookphoto = models.CharField(max_length=150, null=True)
    passport = models.CharField(max_length=150, null=True)
    branchemail = models.CharField(max_length=150, null=True)

class TripSheetPrem(models.Model):
    DriverName=models.CharField(max_length=150,null=True)
    DriverNumber=models.CharField(max_length=150,null=True)
    VehicalNo=models.CharField(max_length=150,null=True)
    VehicalNo=models.CharField(max_length=150,null=True)
    AdvGiven=models.CharField(max_length=150,null=True)
    Time=models.TimeField(null=True)
    Date=models.DateField(null=True)
    LTRate=models.FloatField(null=True)
    Ltr=models.FloatField(null=True)
    LRno=models.IntegerField(null=True)
    qty=models.IntegerField(null=True)
    desc=models.CharField(max_length=150,null=True)
    dest=models.CharField(max_length=150,null=True)
    consignee=models.CharField(max_length=150,null=True)
    username=models.CharField(max_length=150,null=True)
    pay_status = models.CharField(max_length=150, null=True)
    branch=models.CharField(max_length=150,null=True)
    total_cost = models.FloatField(null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    st_charge = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    trip_id =models.CharField(max_length=150,null=True)
    status =models.CharField(max_length=150,null=True)
    weightAmt = models.FloatField(null=True)
    balance = models.FloatField(null=True)



class TripSheetTemp(models.Model):
    Date=models.DateField(null=True)
    LRno=models.IntegerField(null=True)
    qty=models.IntegerField(null=True)
    desc=models.CharField(max_length=150,null=True)
    dest=models.CharField(max_length=150,null=True)
    consignee=models.CharField(max_length=150,null=True)
    username=models.CharField(max_length=150,null=True)
    pay_status = models.CharField(max_length=150, null=True)
    branch = models.CharField(max_length=150, null=True)
    total_cost=models.FloatField( null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    st_charge = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    weightAmt = models.FloatField(null=True)
    balance = models.FloatField(null=True)


class Account(models.Model):
    Date = models.CharField(max_length=50, null=True)
    track_number = models.CharField(max_length=50)
    debit = models.CharField(max_length=50, null=True)
    credit = models.CharField(max_length=50, null=True)
    Balance = models.CharField(max_length=50, null=True)
    sender_name = models.CharField(max_length=255)
    TrType = models.CharField(max_length=50, null=True)
    particulars = models.CharField(max_length=50, null=True)
    headname = models.CharField(max_length=50, null=True)
    Branch=models.CharField(max_length=150,null=True)


class Expenses(models.Model):
    Date=models.DateField(null=True)
    Reason=models.CharField(max_length=150,null=True)
    Amount=models.CharField(max_length=150,null=True)
    branch=models.CharField(max_length=150,null=True)
    username=models.CharField(max_length=150,null=True)
    staffname = models.CharField(max_length=150, null=True)

class Disel(models.Model):
    Date = models.CharField(max_length=50, null=True)
    vehicalno = models.CharField(max_length=50, null=True)
    drivername = models.CharField(max_length=50, null=True)
    ltrate = models.FloatField(max_length=50, null=True)
    liter = models.FloatField(max_length=50, null=True)
    total = models.FloatField(max_length=50, null=True)
    trip_id = models.FloatField(max_length=50, null=True)


class CollectionBalance(models.Model):
    sender_name = models.CharField(max_length=250,null=True)
    pay_status = models.CharField(max_length=250,null=True)
    total = models.FloatField(null=True)
    amount = models.FloatField(null=True)
    balance = models.FloatField(null=True)
    name = models.CharField(max_length=250,null=True)
    branch = models.CharField(max_length=250,null=True)
    date = models.CharField(max_length=250,null=True)
    consignment_status = models.CharField(max_length=250, null=True)
    cust_id= models.IntegerField(null=True)

class Collection(models.Model):
    lrNo = models.IntegerField(null=True)
    sender_name = models.CharField(max_length=250,null=True)
    sender_GST = models.CharField(max_length=250,null=True)
    sender_address = models.CharField(max_length=250,null=True)
    receiver_name = models.CharField(max_length=250,null=True)
    receiver_GST = models.CharField(max_length=250,null=True)
    receiver_address = models.CharField(max_length=250,null=True)
    pay_status = models.CharField(max_length=250,null=True)
    total = models.FloatField(null=True)
    freight = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    st_charge = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    weight = models.FloatField(null=True)
    weightRate = models.FloatField(null=True)
    route_from = models.CharField(max_length=250,null=True)
    route_to = models.CharField(max_length=250,null=True)
    amount = models.FloatField(null=True)
    balance = models.FloatField(null=True)
    name = models.CharField(max_length=250,null=True)
    branch = models.CharField(max_length=250,null=True)
    date = models.CharField(max_length=250,null=True)
    consignment_status = models.CharField(max_length=250, null=True)
    desc = models.CharField(max_length=250, null=True)

    cust_id = models.IntegerField(null=True)

class UserLogin(models.Model):
    username = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)


class DriverLocation(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='locations',null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    timestamp = models.DateTimeField(auto_now=True,null=True)
    location_sharing_active = models.BooleanField(default=False,null=True)

    def __str__(self):
        return f"Location for {self.driver.name} at {self.timestamp}"

class DeleteConsignment(models.Model):
    track_id = models.IntegerField(null=True)
    sender_name = models.CharField(max_length=50, null=True)
    sender_mobile = models.CharField(max_length=50, null=True)
    sender_address = models.CharField(max_length=50, null=True)
    sender_GST=models.CharField(max_length=50,null=True)
    receiver_name = models.CharField(max_length=50, null=True)
    receiver_mobile = models.CharField(max_length=50, null=True)
    receiver_address = models.CharField(max_length=50, null=True)
    receiver_GST = models.CharField(max_length=50, null=True)
    total_cost = models.FloatField(null=True)
    date = models.DateField(max_length=30, null=True)
    pay_status = models.CharField(max_length=30, null=True)
    route_from = models.CharField(max_length=30, null=True)
    route_to = models.CharField(max_length=30, null=True)
    desc_product = models.CharField(max_length=150,null=True)
    pieces = models.IntegerField(null=True)
    prod_invoice = models.CharField(max_length=50,null=True)
    prod_price = models.CharField(max_length=50,null=True)
    weight = models.FloatField(null=True)
    freight = models.FloatField(null=True)
    hamali = models.FloatField(null=True)
    door_charge = models.FloatField(null=True)
    st_charge = models.FloatField(null=True)
    Consignment_id=models.IntegerField(null=True)
    branch = models.CharField(max_length=150, null=True)
    name = models.CharField(max_length=150, null=True)
    balance = models.FloatField(null=True)
    time=models.CharField(max_length=50,null=True)
    copy_type = models.CharField(max_length=150, null=True)
    weightAmt=models.FloatField(null=True)
    delivery = models.CharField(max_length=150, null=True)
    eway_bill =models.CharField(max_length=150, null=True)
    consignment_status = models.CharField(max_length=150, null=True)

    def __str__(self):
        return f"Consignment {self.track_id}: {self.sender_name}"

class Creditledger(models.Model):
    date = models.DateField(null=True)
    type = models.CharField(max_length=500,null=True)
    credit = models.CharField(max_length=500,null=True)
    creditDesc = models.CharField(max_length=500,null=True)
    creditAmt = models.FloatField(null=True)


class Debitledger(models.Model):
    date = models.DateField(null=True)
    type = models.CharField(max_length=500,null=True)
    debit = models.CharField(max_length=500,null=True)
    debitDesc = models.CharField(max_length=500,null=True)
    debitAmt = models.FloatField(null=True)