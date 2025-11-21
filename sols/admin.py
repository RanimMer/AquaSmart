from django.contrib import admin
from .models import AnalyseSol

@admin.register(AnalyseSol)
class AnalyseSolAdmin(admin.ModelAdmin):
    list_display = ('ph', 'azote', 'phosphore', 'potassium', 'farm')
    search_fields = ('localisation',)
    list_filter = ('farm',)
