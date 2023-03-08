# from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django_countries.fields import CountryField

User = get_user_model()

CATEGORY_CHOICES = {
    ("S", "Shirt"),
    ("Sw", "Sport Wear"),
    ("OW", "Outwear"),
}

LABEL_CHOICES = {
    ("P", "primary"),
    ("S", "secondary"),
    ("D", "danger"),
}


class Item(models.Model):
    """Модель товаров"""
    title = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    price = models.FloatField('Цена')  # Цена - поле с плавающей точкой
    discount_price = models.FloatField('Цена-Скидка', blank=True, null=True)
    category = models.CharField(
        'Категория', choices=CATEGORY_CHOICES, max_length=2
    )
    label = models.CharField(
        'Этикетка', choices=LABEL_CHOICES, max_length=1
    )
    slug = models.SlugField(unique=True)
    image = models.ImageField(
        'Изображение', blank=True, null=True,
        upload_to='media/item_photos/%Y/%m/%d/'
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Метод для детального просмотра товара"""
        return reverse('core:product', kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        """Метод для добавления товара в корзину заказа"""
        return reverse("core:add-to-cart", kwargs={"slug": self.slug})

    def get_remove_from_cart_url(self):
        """Метод для удаления товара из корзины заказа"""
        return reverse("core:remove-from-cart", kwargs={"slug": self.slug})


class OrderItem(models.Model):
    """Модель для элементов заказа (Способ связи между заказом и товаром)"""
    # Прикрепление к пользователю обязательно (Для различия между другими)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, verbose_name='Товар'
    )
    quantity = models.PositiveSmallIntegerField('Количество', default=1)

    def __str__(self):
        return f"Предмет: {self.item.title} | Кол-во: {self.quantity}"

    def get_total_item_price(self):
        """Получить итоговую сумму за товар"""
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        """Получить итоговую сумму за товар если есть скидка"""
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        """Сколько денег было сэкономленно из-за скидки"""
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        """Получить итоговую сумму (Вызывается в order)"""
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    """Модель корзины"""
    # Прикрепление к пользователю обязательно (Для различия между другими)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    # Ссылочный код на заказ (для удобного поиска)
    ref_code = models.CharField(max_length=25)
    items = models.ManyToManyField(OrderItem, verbose_name='Товары')
    start_date = models.DateTimeField(
        'Дата создания заказа', auto_now_add=True
    )
    # Дата оформления заказа (Будет установлено вручную)
    ordered_date = models.DateTimeField('Дата оформления заказа')
    ordered = models.BooleanField('Оплачено', default=False)

    # Платежный адрес (С формы оплаты добавляется)
    billing_address = models.ForeignKey(
        'BillingAddress', on_delete=models.SET_NULL, blank=True, null=True
    )

    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True
    )

    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True
    )

    # 1. Товар добавлен в корзину
    # 2. Добавить платежный адрес. Неудачная транзакция (Ошибка в Checkout)
    # 3. Оплата (Обработка, упаковка товара)
    # 4. Доставка заказа
    # 5. Дата получения заказа (Процесс подписки получения товара)
    # 6. Отслеживания количества возврата

    # Заказ передан в доставку
    being_delivered = models.BooleanField(default=False)
    # Заказ получен
    received = models.BooleanField(default=False)
    # Зарегистрирован запрос на возврат денег
    refund_requested = models.BooleanField(default=False)
    # Возврат денег одобрен
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_total_sum(self):
        """Итоговая сумма заказа в корзине"""
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        # Если есть купон
        if self.coupon:
            total -= self.coupon.amount
        return total


class BillingAddress(models.Model):
    """Платежный адрес пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    """Модель платежа"""
    # stripe - сервис для обработки карт
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    """Модель купонов"""
    code = models.CharField('Код купона', max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code


class Refund(models.Model):
    """Возврат средств"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f'{self.pk}'
