# from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Item(models.Model):
    """Модель товаров"""
    title = models.CharField(max_length=100)
    # Цена - поле с плавающей точкой
    price = models.FloatField()

    def __str__(self):
        return self.title


class OrderItem(models.Model):
    """Модель для элементов заказа (Способ связи между заказом и товаром)"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return self.item


class Order(models.Model):
    """Модель корзины"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # user = models.ForeignKey(
    # settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    # )

    items = models.ManyToManyField(OrderItem)
    # Дата создания заказа
    start_date = models.DateTimeField(auto_now_add=True)
    # Дата оформления заказа (Будет установлено вручную)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
