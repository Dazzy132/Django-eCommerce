import random
import string

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from .forms import CheckoutForm, CouponForm, PaymentForm, RefundForm
from .models import (Address, Coupon, Item, Order, OrderItem, Payment, Refund,
                     UserProfile)

User = get_user_model()
# Настройка работы с банковскими картами
stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(ListView):
    """Домашняя страница (Отображение товаров)
    context_object_name по умолчанию object_list
    """
    model = Item
    template_name = 'home.html'
    paginate_by = 8
    context_object_name = 'items'


class ItemByCategory(ListView):
    model = Item
    template_name = 'home.html'
    paginate_by = 10
    context_object_name = 'items'

    def get_queryset(self):
        return Item.objects.filter(category__slug=self.kwargs.get('slug'))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cat_selected_slug'] = self.kwargs.get('slug')
        return context


class Search(ListView):
    template_name = 'home.html'
    paginate_by = 10
    context_object_name = 'items'

    def get_queryset(self):
        """Фильтруем товары, по полученному запросу, где название содержит
         запрос полученный из поля ввода в home.html с названием q"""
        return Item.objects.filter(title__icontains=self.request.GET.get('q'))

    def get_context_data(self, *args, **kwargs):
        """Добавляем в словарь значение, которое пришло. Это нужно для того,
        чтобы работала пагинация. Чтобы она работала, необходимо передать
        контекст как строку, где q будет равно запросу."""
        context = super().get_context_data(*args, **kwargs)
        context['q'] = f'q={self.request.GET.get("q")}&'
        return context


class ItemDetailView(DetailView):
    """Просмотр определенного товара
    context_object_name по умолчанию object. Тут не переопределён
    """
    model = Item
    template_name = 'product.html'


@login_required
def add_to_cart(request, slug):
    """Метод добавления в корзину товара по его slug"""
    item = get_object_or_404(Item, slug=slug)
    item_quantity = request.POST.get('amount', 1)

    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False,
    )

    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += int(item_quantity)
            order_item.save()
            messages.info(request, f'Количество товара было обновлено')
            return redirect("core:order-summary")
        else:
            order_item.quantity = item_quantity
            order.items.add(order_item)
            order_item.save()
            messages.info(request, 'Товар добавлен в вашу корзину')
            return redirect("core:order-summary")
    # Если заказа нет, то создать его вручную и добавить товар в корзину
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date
        )
        order.items.add(order_item)
        messages.info(request, 'Товар добавлен в вашу корзину')
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    """Метод удаления товара из корзины (полностью)"""
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # Если товар в корзине существует, то получить этот товар по его slug,
        # а затем удалить его в 2‑х моделях (В корзине и промежуточной модели)
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "Этот товар был убран из вашей корзины")
            return redirect("core:order-summary")
        # Если этого товара нет в корзине
        else:
            messages.info(request, "Этого предмета нет в вашей корзине")
            return redirect("core:product", slug=slug)
    # Если не создан заказ
    else:
        messages.info(request, "У вас нет активного заказа")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    """Метод удаления одного товара из корзины"""
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # Если товар существует в корзине, то уменьшить его количество на 1.
        # Если количество равно 0, то удалить его из заказа.
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
                # order.items.remove(order_item)
            messages.info(request, "Количество этого товара было обновлено")
            return redirect("core:order-summary")
        # Если этого товара нет в корзине
        else:
            messages.info(request, "Этого предмета нет в вашей корзине")
            return redirect("core:product", slug=slug)
    # Если не создан заказ
    else:
        messages.info(request, "У вас нет активного заказа")
        return redirect("core:product", slug=slug)


class OrderSummaryView(LoginRequiredMixin, View):
    """Просмотреть корзину товаров"""

    def get(self, *args, **kwargs):
        """Передать объект заказа для отрисовки"""
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {"object": order}
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'У вас нет активного заказа')
            return redirect('core:home')


class CheckoutView(LoginRequiredMixin, View):
    """Форма для платежа"""

    def get(self, *args, **kwargs):
        """Показать форму при GET запросе + вывод формы для купонов по знач."""
        try:
            form = CheckoutForm()
            order = Order.objects.get(user=self.request.user, ordered=False)
            print('fds')
            context = {
                'form': form,
                'order': order,
                'coupon_form': CouponForm(),
                'DISPLAY_COUPON_FORM': True,
            }

            # Если у пользователя используется адрес доставки по умолчанию
            shipping_address_qs = Address.objects.filter(
                user=self.request.user, address_type='S', default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {"default_shipping_address": shipping_address_qs[0]}
                )

            # Если у пользователя используется платежный адрес по умолчанию
            billing_address_qs = Address.objects.filter(
                user=self.request.user, address_type='B', default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {"default_billing_address": billing_address_qs[0]}
                )

            return render(self.request, 'checkout.html', context)

        except ObjectDoesNotExist:
            messages.info(self.request, 'У вас нет активного заказа')
            return redirect('core:home')

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping'
                )
                # Если адрес доставки по умолчанию есть, то проверить его
                if use_default_shipping:
                    address_qs = Address.objects.filter(
                        user=self.request.user, address_type='S', default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "Нет адреса доставки по умолчанию"
                        )
                        return redirect('core:checkout')
                # Если нет по умолчанию, то просто обработать форму
                else:
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form(
                            [shipping_address1, shipping_country,
                             shipping_zip, shipping_country]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        # Прикрепить адрес доставки к платежу
                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        # Если поставил галочку сохранить
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Пожалуйста, заполните все поля"
                        )

                # Использовать платежный адрес по умолчанию
                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                # Адрес доставки совпадает с платежным
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                # Если совпадает, то скопировать его
                if same_billing_address:
                    billing_address = shipping_address
                    # pk = None для удачного копирования
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                # Если по умолчанию, то получить его
                elif use_default_billing:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "Нет платежного адреса по умолчанию")
                        return redirect('core:checkout')
                # Простая обработка формы если не указаны никакие галочки
                else:
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Пожалуйста, заполните все поля")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Выбран неверный вариант оплаты")
                    return redirect('core:checkout')

            messages.warning(self.request, 'Не удалось оформить заказ')
            return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "У вас нет активного заказа")
            return redirect("core:order-summary")


class PaymentView(View):
    """Платёжная система (Карта/Paypal)"""

    def get(self, *args, **kwargs):
        """Отображение страницы платежа"""
        try:

            order = Order.objects.get(user=self.request.user, ordered=False)
            # Нельзя перейти на страницу оплаты если не указал платежный адрес
            if order.billing_address:
                context = {
                    'order': order,
                    'DISPLAY_COUPON_FORM': False,
                    'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
                }
                return render(self.request, "payment.html", context)
            else:
                messages.warning(
                    self.request, 'Вы не добавили адрес для выставления счетов'
                )
                return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(
                self.request,
                'У вас нет активного заказа, чтобы перейти к оплате'
            )
            return redirect('/')

    def post(self, *args, **kwargs):
        """Обработка платежа"""
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            # Получить токен с формы
            token = self.request.POST.get('stripeToken')
            # Цена идет в центах, по этому нужно умножить на 100
            amount = int(order.get_total_sum() * 100)
            # Создать платёж stripe
            charge = stripe.Charge.create(
                amount=amount,  # cents
                currency="usd",
                source=token
            )

            # Создание платежа Django
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total_sum()
            payment.save()

            # Получить все товары в заказе и обновить у них значения ordered.
            # Для того чтобы после заказа если человек добавит еще предметы, то
            # у него добавлялись новые
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            # Прикрепление платежа к заказу
            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()

            messages.success(self.request, f"Ваш заказ был успешно оплачен!")
            messages.warning(self.request, f'Код покупки {order.ref_code}')
            return redirect("/")

        except Order.DoesNotExist:
            messages.warning(self.request, 'У вас нет активного заказа')
            return redirect('core:home')

        # https://stripe.com/docs/api/errors/handling?lang=python
        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network error")
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request,
                "Something went wrong. You were not charged. Please try again."
            )
            return redirect("/")

        except Exception as e:
            # send an email to ourselves
            messages.warning(
                self.request, "A serious error occurred. We have been notifed."
            )
            return redirect("/")


def get_coupon(request, code):
    """Получить купон по коду"""
    try:
        return Coupon.objects.get(code=code)
    except ObjectDoesNotExist:
        messages.warning(request, 'Этого купона не существует')


def create_ref_code():
    """Создания реферального кода (Для поиска заказа) """
    return ''.join(
        random.choices(string.ascii_lowercase + string.digits, k=20)
    )


def is_valid_form(values):
    valid = True

    for field in values:
        if field == '':
            valid = False
    return valid


class AddCoupon(View):
    """Добавление купона"""
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                if order.coupon:
                    order.save()
                    messages.success(self.request, 'Купон успешно активирован')
                    return redirect('core:checkout')
                return redirect('core:checkout')

            except ObjectDoesNotExist:
                messages.info(self.request, 'У вас нет активного заказа')
                return redirect('/')


class RequestRefundView(View):
    """Представление для возврата средств за товар"""
    def get(self, *args, **kwargs):
        """Показать форму"""
        ref_code = self.request.GET.get('ref_code')
        email = self.request.GET.get('email')
        form = RefundForm(initial={'ref_code': ref_code, 'email': email})
        context = {'form': form}
        return render(self.request, 'request_refund.html', context=context)

    def post(self, *args, **kwargs):
        """Обработать форму"""
        ref_c = self.request.POST.get('ref_code')
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                # Получить заказ по реферальному коду и указать что возврат
                # средств поступил на обработку
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # Зарегистрировать в БД запрос и заполнить его поля
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, 'Ваш запрос на возврат получен')
                return redirect('core:request-refund')

            except ObjectDoesNotExist:
                messages.info(self.request, 'По такому коду заказа не найдено')
                return redirect('core:request-refund')
        messages.warning(self.request, 'Произошла ошибка')
        return redirect('/')


class UserProfileView(LoginRequiredMixin, ListView):
    template_name = 'profile.html'
    context_object_name = 'order'

    def get_queryset(self):
        return (
            self.request.user.order_set
            .select_related('user', 'billing_address', 'payment')
            .prefetch_related('items')
        )


class OrderDetailView(LoginRequiredMixin, ListView):
    template_name = 'order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        order = Order.objects.filter(
            ref_code=self.kwargs.get('ref_code'), user=self.request.user
        )
        if order.exists():
            return (
                order
                .select_related('payment', 'billing_address')
                .prefetch_related('items')
                .first()
            )
        messages.warning(self.request, 'Такого заказа нет')
        return redirect('core:profile')