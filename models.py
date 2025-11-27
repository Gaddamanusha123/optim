from django.db import models
from django.contrib.auth.models import User


class Train(models.Model):
    name = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    date = models.DateField()

    def __str__(self):
        return self.name


class TrainClass(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='classes')
    class_name = models.CharField(max_length=10)   
    quota = models.CharField(max_length=20, default='GENERAL')
    total_seats = models.IntegerField(default=50)
    booked_seats = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.train.name} - {self.class_name} - {self.quota}"


class Booking(models.Model):
    STATUS = (
        ('CONFIRMED', 'CONFIRMED'),
        ('CANCELLED', 'CANCELLED')
    )
    PAYMENT = (
        ('PAID', 'PAID'),
        ('FAILED', 'FAILED')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=10)
    quota = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS, default='CONFIRMED')
    payment_status = models.CharField(max_length=20, choices=PAYMENT, default='PAID')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id}"


class Passenger(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    berth_pref = models.CharField(max_length=10)

    def __str__(self):
        return self.name
