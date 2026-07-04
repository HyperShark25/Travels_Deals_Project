# bookings/admin.py
from django.contrib import admin
from .models import TravelCompany, VacationPackage, Booking


class VacationPackageInline(admin.TabularInline):
    model  = VacationPackage
    extra  = 1
    fields = ('title', 'price', 'start_date', 'end_date')


@admin.register(TravelCompany)
class TravelCompanyAdmin(admin.ModelAdmin):
    list_display  = ('name',)
    search_fields = ('name',)
    inlines       = [VacationPackageInline]

    def package_count(self, obj):
        return obj.packages.count()
    package_count.short_description = 'Packages'


@admin.register(VacationPackage)
class VacationPackageAdmin(admin.ModelAdmin):
    list_display  = ('title', 'company', 'price', 'start_date', 'end_date')
    list_filter   = ('company',)
    search_fields = ('title', 'company__name')
    ordering      = ('company', 'start_date')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company__managers=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'company' and not request.user.is_superuser:
            kwargs['queryset'] = TravelCompany.objects.filter(managers=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display    = ('id', 'package', 'user', 'guest_email', 'status', 'created_at')
    list_filter     = ('status', 'package__company')
    search_fields   = ('guest_email', 'user__username', 'package__title')
    readonly_fields = ('session_key', 'paymob_order_id', 'created_at')
    ordering        = ('-created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(package__company__managers=request.user)