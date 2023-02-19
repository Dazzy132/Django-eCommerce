from django.contrib import admin

from .models import Item, Order, OrderItem, BillingAddress, Payment


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["title", 'price', 'discount_price',
                    'category', 'label', 'slug']
    list_filter = ['category', 'price', 'label']
    list_editable = ['price', 'discount_price', 'category', 'label']
    prepopulated_fields = {"slug": ('title',)}
    save_as = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'start_date', 'ordered_date', 'ordered']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'quantity', 'ordered']


@admin.register(BillingAddress)
class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street_address', 'apartment_address',
                    'country', 'zip']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['stripe_charge_id', 'user', 'amount', 'timestamp', ]
