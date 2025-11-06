from django.test import TestCase

# Create your tests here.
from django.db import models

# Create your models here.
image = models.ImageField(upload_to='produits/')
