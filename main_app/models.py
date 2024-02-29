from django.contrib.auth.models import User
from django.db import models


class Product(models.Model):
    author = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    starts_at = models.DateTimeField()
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    allowed_users = models.ManyToManyField(User, related_name='allowed_products', blank=True)
    max_group_capacity = models.IntegerField(default=10)

    def __str__(self):
        return self.name


class Lesson(models.Model):
    product = models.ForeignKey(Product, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField()

    def __str__(self):
        return self.title


class Group(models.Model):
    product = models.ForeignKey(Product, related_name='groups', on_delete=models.CASCADE)
    students = models.ManyToManyField(User, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name
