from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from .models import Train, TrainClass, Booking, Passenger
from django.db import transaction
import json


def get_data(request):
    try:
        return json.loads(request.body.decode())
    except:
        return {}


def get_user(request):
    uid = request.headers.get("X-User-Id") or request.headers.get("x-user-id")
    if not uid:
        return None
    try:
        return User.objects.get(id=uid)
    except:
        return None

@csrf_exempt
def signup(request):
    if request.method != "POST":
        return JsonResponse({"msg": "POST required"}, status=405)

    data = get_data(request)
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if User.objects.filter(username=email).exists():
        return JsonResponse({"msg": "Email already exists"}, status=400)

    user = User.objects.create(
        username=email,
        first_name=name,
        email=email,
        password=make_password(password)
    )

    return JsonResponse({"msg": "Signup success", "user_id": user.id})


@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"msg": "POST required"}, status=405)

    data = get_data(request)
    email = data.get("email")
    password = data.get("password")

    try:
        user = User.objects.get(username=email)
    except:
        return JsonResponse({"msg": "Invalid credentials"}, status=400)

    if not check_password(password, user.password):
        return JsonResponse({"msg": "Invalid credentials"}, status=400)

    return JsonResponse({
        "msg": "Login success",
        "user_id": user.id,
        "name": user.first_name,
        "email": user.email
    })

@csrf_exempt
def add_train(request):
    if request.method != "POST":
        return JsonResponse({"msg": "POST required"}, status=405)

    data = get_data(request)

    try:
        date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    except:
        return JsonResponse({"msg": "Invalid date"}, status=400)

    train = Train.objects.create(
        name=data["name"],
        source=data["source"],
        destination=data["destination"],
        date=date
    )


    TrainClass.objects.create(
        train=train,
        class_name="SL",
        quota="GENERAL",
        total_seats=50,
        booked_seats=0
    )

    return JsonResponse({"msg": "Train added", "train_id": train.id})


def search_trains(request):
    source = request.GET.get("source")
    destination = request.GET.get("destination")
    date = request.GET.get("date")

    qs = Train.objects.all()

    if source:
        qs = qs.filter(source__iexact=source)
    if destination:
        qs = qs.filter(destination__iexact=destination)
    if date:
        qs = qs.filter(date=date)

    data = [
        {
            "id": t.id,
            "name": t.name,
            "source": t.source,
            "destination": t.destination,
            "date": str(t.date)
        }
        for t in qs
    ]

    return JsonResponse(data, safe=False)



def check_availability(request, train_id):
    class_name = request.GET.get("class")
    quota = request.GET.get("quota", "GENERAL")

    try:
        tc = TrainClass.objects.get(train_id=train_id, class_name=class_name, quota=quota)
    except:
        return JsonResponse({"msg": "Class/Quota not found"}, status=404)

    available = tc.total_seats - tc.booked_seats

    return JsonResponse({
        "train_id": train_id,
        "class": tc.class_name,
        "quota": tc.quota,
        "available": available
    })



@csrf_exempt
def pay(request):
    user = get_user(request)
    if not user:
        return JsonResponse({"msg": "Login first"}, status=401)

    return JsonResponse({
        "status": "SUCCESS",
        "txn": f"TXN{datetime.now().timestamp()}"
    })

@csrf_exempt
def book_ticket(request):
    user = get_user(request)
    if not user:
        return JsonResponse({"msg": "Login first"}, status=401)

    if request.method != "POST":
        return JsonResponse({"msg": "POST required"}, status=405)

    data = get_data(request)

    required_keys = ["train_id", "class", "quota", "passengers"]
    for key in required_keys:
        if key not in data:
            return JsonResponse({"msg": f"Missing key: {key}"}, status=400)

    train_id = data["train_id"]
    class_name = data["class"]
    quota = data["quota"]
    passengers = data["passengers"]

    try:
        train = Train.objects.get(id=train_id)
    except:
        return JsonResponse({"msg": "Train not found"}, status=404)


    booking = Booking.objects.create(
        user=user,
        train=train,
        class_name=class_name,
        quota=quota,
        status="CONFIRMED"
    )
    for p in passengers:

        for pk in ["name", "age", "gender", "berth"]:
            if pk not in p:
                return JsonResponse({"msg": f"Missing passenger key: {pk}"}, status=400)

        Passenger.objects.create(
            booking=booking,
            name=p["name"],
            age=p["age"],
            gender=p["gender"],
            berth_pref=p["berth"]
        )

    return JsonResponse({
        "msg": "Booking created",
        "booking_id": booking.id
    })
     




def booking_details(request, id):
    user = get_user(request)
    if not user:
        return JsonResponse({"msg": "Login first"}, status=401)

    try:
        booking = Booking.objects.get(id=id, user=user)
    except:
        return JsonResponse({"msg": "Booking not found"}, status=404)

    data = {
        "id": booking.id,
        "train": booking.train.name,
        "class": booking.class_name,
        "quota": booking.quota,
        "status": booking.status,
        "passengers": [
            {
                "name": p.name,
                "age": p.age,
                "gender": p.gender,
                "berth": p.berth_pref
            }
            for p in booking.passengers.all()
        ]
    }

    return JsonResponse(data)


@csrf_exempt
def cancel_booking(request, id):
    user = get_user(request)
    if not user:
        return JsonResponse({"msg": "Login first"}, status=401)

    try:
        booking = Booking.objects.get(id=id, user=user)
    except:
        return JsonResponse({"msg": "Booking not found"}, status=404)

    if booking.status == "CANCELLED":
        return JsonResponse({"msg": "Already cancelled"}, status=400)

    tc = TrainClass.objects.get(
        train=booking.train,
        class_name=booking.class_name,
        quota=booking.quota
    )

    seats = booking.passengers.count()
    tc.booked_seats -= seats
    tc.save()

    booking.status = "CANCELLED"
    booking.save()

    return JsonResponse({"msg": "Cancelled"})
