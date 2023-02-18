from django.contrib import admin

from .models import Item, Order, OrderItem


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
