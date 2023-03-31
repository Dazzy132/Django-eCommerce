from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.urls import reverse
from django_countries.fields import CountryField

User = get_user_model()

LABEL_CHOICES = {
    ("P", "primary"),
    ("S", "secondary"),
    ("D", "danger"),
}

ADDRESS_CHOICES = {
    ("B", "Billing"),  # Адрес для выставления счетов
    ("S", "Shipping"),  # Адрес доставок
}


class Category(models.Model):
    """Модель категорий"""

    name = models.CharField("Название", max_length=50, null=False)
    slug = models.SlugField("slug", unique=True, null=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("core:category", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ("name",)


class Item(models.Model):
    """Модель товаров"""

    title = models.CharField("Название", max_length=100, null=False,
                             db_index=True)
    description = models.TextField("Описание")
    price = models.FloatField(
        "Цена",
        validators=[MinValueValidator(1, "Минимальная цена - 1")],
        help_text="Цена в $",
        null=False,
    )
    discount_price = models.FloatField(
        "Цена-Скидка",
        validators=[MinValueValidator(1, "Минимальная цена - 1")],
        help_text="Цена в $",
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        related_name="items",
        on_delete=models.CASCADE,
    )
    label = models.CharField("Этикетка", choices=LABEL_CHOICES, max_length=1)
    slug = models.SlugField("slug", unique=True)
    image = models.ImageField(
        "Изображение", blank=False, null=False, upload_to="item_photos/"
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Метод для детального просмотра товара"""
        return reverse("core:product", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        """Метод для добавления товара в корзину заказа"""
        return reverse("core:add-to-cart", kwargs={"slug": self.slug})

    def get_remove_from_cart_url(self):
        """Метод для удаления товара из корзины заказа"""
        return reverse("core:remove-from-cart", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ("id",)


class OrderItem(models.Model):
    """Модель для элементов заказа (Способ связи между заказом и товаром)"""

    # Прикрепление к пользователю обязательно (Для различия между другими)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="order_items",
    )
    ordered = models.BooleanField("Заказан", default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE,
                             verbose_name="Товар")
    quantity = models.PositiveSmallIntegerField(
        "Количество",
        default=1,
        validators=[MinValueValidator(1, "Минимальное количество- 1")],
    )

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
        return (
            self.get_total_item_price() - self.get_total_discount_item_price()
        )

    def get_final_price(self):
        """Получить итоговую сумму (Вызывается в order)"""
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказах"


class Order(models.Model):
    """Модель корзины"""

    # Прикрепление к пользователю обязательно (Для различия между другими)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    # Ссылочный код на заказ (для удобного поиска)
    ref_code = models.CharField("Ссылочный код", max_length=25, blank=True,
                                null=True)
    items = models.ManyToManyField(OrderItem, verbose_name="Товары")
    start_date = models.DateTimeField("Дата создания заказа",
                                      auto_now_add=True)
    # Дата оформления заказа (Будет установлено вручную)
    ordered_date = models.DateTimeField("Дата оформления заказа")
    ordered = models.BooleanField("Оплачено", default=False)

    # Платежный адрес (С формы оплаты добавляется)
    billing_address = models.ForeignKey(
        "Address",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="billing_address",
        verbose_name="Платежный адрес",
    )
    shipping_address = models.ForeignKey(
        "Address",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="shipping_address",
        verbose_name="Адрес доставки",
    )

    payment = models.ForeignKey(
        "Payment",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Платёж",
    )

    coupon = models.ForeignKey(
        "Coupon", on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name="Купон"
    )

    being_delivered = models.BooleanField("Передан в доставку", default=False)
    received = models.BooleanField("Заказ получен", default=False)
    refund_requested = models.BooleanField(
        "Зарегистрирован возврат денег", default=False
    )
    refund_granted = models.BooleanField("Возврат оформлен", default=False)

    def __str__(self):
        return f"Корзина - {self.user.username} | ref_code - {self.ref_code}"

    def get_total_sum(self):
        """Итоговая сумма заказа в корзине"""
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        # Если есть купон
        if self.coupon:
            total -= self.coupon.amount
        return total

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"


class Address(models.Model):
    """Платежный адрес пользователя"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    street_address = models.CharField("Адрес доставки", max_length=100)
    apartment_address = models.CharField("Дом|Квартира", max_length=100)
    country = CountryField(multiple=False, verbose_name="Страна")
    zip = models.CharField("Почтовый индекс", max_length=20)

    # Тип адреса на который нужно сделать доставку (торговый/доставка)
    address_type = models.CharField(
        "Куда доставлять",
        max_length=1,
        choices=ADDRESS_CHOICES,
        help_text="Торговый или Доставка",
    )
    # Поле типа адреса по умолчанию
    default = models.BooleanField("Адрес по умолчанию", default=False)

    def __str__(self):
        return f"Адрес {self.street_address} пользователя {self.user.username}"

    class Meta:
        verbose_name = "Адреса доставки"
        verbose_name_plural = "Адресы доставок"
        ordering = ("-id",)


class Payment(models.Model):
    """Модель платежа"""

    # stripe - сервис для обработки карт
    stripe_charge_id = models.CharField("Идентификатор stripe", max_length=50)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Пользователь",
    )
    amount = models.FloatField(
        "Сумма платежа",
        validators=[MinValueValidator(1, "Минимальная цена - 1")]
    )
    timestamp = models.DateTimeField("Дата платежа", auto_now_add=True)

    def __str__(self):
        return (
            f"Пользователь {self.user.username} | Сумма {self.amount} |"
            f" дата {self.timestamp} | ID - {self.stripe_charge_id}"
        )

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ("-id",)


class Coupon(models.Model):
    """Модель купонов"""

    code = models.CharField("Код купона", max_length=15)
    amount = models.FloatField(
        "Скидка",
        validators=[MinValueValidator(1, "Минимальная скидка - 1")],
        help_text="Скидка в $",
    )

    def __str__(self):
        return f"{self.code} - {self.amount}"

    class Meta:
        verbose_name = "Купон"
        verbose_name_plural = "Купоны"
        ordering = ("amount",)


class Refund(models.Model):
    """Возврат средств"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              verbose_name="Заказ")
    reason = models.TextField("Причина возврата")
    accepted = models.BooleanField("Одобрен", default=False)
    email = models.EmailField("Email")

    def __str__(self):
        return f"{self.pk}"

    class Meta:
        verbose_name = "Возврат"
        verbose_name_plural = "Возвраты"
        ordering = ("-id",)


class UserProfile(models.Model):
    """Профиль пользователя с его картой"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    stripe_customer_id = models.CharField(
        "ID клиента Stripe", max_length=50, blank=True, null=True
    )
    one_click_purchasing = models.BooleanField("Покупка в один клик",
                                               default=False)


def userprofile_receiver(sender, instance, created, *args, **kwrags):
    if created:
        userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=User)
