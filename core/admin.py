from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (Address, Category, Coupon, Item, Order, OrderItem,
                     Payment, Refund, UserProfile)


def make_refund_accepted(modeladmin, request, queryset):
    """Собственный action для одобрения возврата на рефанд"""
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Обновить статус возврата на возврат'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        "title", 'get_image', 'price', 'discount_price', 'category', 'label',
        'slug'
    ]
    list_filter = ['category', 'price', 'label']
    list_editable = ['price', 'discount_price', 'category', 'label']
    search_fields = ('title',)
    prepopulated_fields = {"slug": ('title',)}
    readonly_fields = ['get_image']
    save_as = True

    fieldsets = (
        (None, {
            "fields": ("title", "slug", 'category', 'label')
        }),
        ('Информация', {
            "fields": ("description", ("image", "get_image"))
        }),
        (None, {
            "fields": ("price", "discount_price")
        }),
    )

    def get_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="50px" height="50px"'
            )
        return '---'

    get_image.short_description = 'Фотография товара'


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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {"slug": ('name',)}


admin.site.register(UserProfile)