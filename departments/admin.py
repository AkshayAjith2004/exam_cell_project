from django.contrib import admin
from .models import Department, Branch, AcademicYear

admin.site.register(Department)
admin.site.register(Branch)
admin.site.register(AcademicYear)
