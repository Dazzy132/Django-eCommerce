from django.contrib import admin

from .models import (Address, Coupon, Item, Order, OrderItem, Payment,
                     Refund)


def make_refund_accepted(modeladmin, request, queryset):
    """Собственный action"""
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Обновить статус возврата на возврат'


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
    list_display = ['id', 'user', 'ordered', 'being_delivered', 'received',
                    'refund_requested', 'refund_granted', 'billing_address',
                    'shipping_address', 'payment', 'coupon']
    list_filter = ['ordered', 'being_delivered', 'received',
                   'refund_requested', 'refund_granted']
    list_display_links = [
        'user', 'billing_address', 'payment', 'coupon', 'shipping_address'
    ]
    search_fields = ['user__username', 'ref_code']
    actions = [make_refund_accepted]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'quantity', 'ordered']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street_address', 'apartment_address',
                    'country', 'zip', 'address_type', 'default']
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['stripe_charge_id', 'user', 'amount', 'timestamp', ]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['order', 'reason', 'email', 'accepted']