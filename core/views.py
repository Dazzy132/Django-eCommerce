import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from .forms import CheckoutForm
from .models import Item, Order, OrderItem, BillingAddress, Payment

# Настройка работы с банковскими картами
stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(ListView):
    """Домашняя страница (Отображение товаров)
    context_object_name по умолчанию object_list
    """
    model = Item
    template_name = 'home.html'
    paginate_by = 10
    context_object_name = 'items'


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
    # Метод get_or_create возвращает 2 переменных. Она нужна тут для того,
    # чтобы не создавать новый заказ, а обновлять существующий, и если текущего
    # заказа нет, то создать его
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    # Получаем заказ по пользователю, который не завершён
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    # Если заказ есть, то проверяем на наличие этого товара в корзине. Если он
    # есть, то обновить количество, если нет, то добавить его в корзину и
    # перенаправить на страницу заказа
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(
                request,
                f'Количество товара было обновлено на: {order_item.quantity}',
            )
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
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
        return redirect("core:product", slug=slug)


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
                item=item,
                user=request.user,
                ordered=False
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
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
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
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {"object": order}
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, 'У вас нет активного заказа')
            return redirect('core:home')


class CheckoutView(View):
    """Форма для платежа"""

    def get(self, *args, **kwargs):
        """Показать форму при GET запросе"""
        form = CheckoutForm()
        context = {'form': form}
        return render(self.request, 'checkout.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            # Если форма валидная - получить из неё данные. Далее создать
            # платежный способ и привязать его к заказу.
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # TODO: Добавить функциональность для этих полей
                # same_shipping_address = form.cleaned_data.get(
                #     'same_shipping_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                # Определение способа платежа по радио кнопке
                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_optio='paypal')
                else:
                    messages.warning(
                        self.request, 'Выбран неверный вариант оплаты'
                    )
                    return redirect('core:checkout')

            messages.warning(self.request, 'Не удалось оформить заказ')
            return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.error(self.request, 'У вас нет активного заказа')
            return redirect('core:home')


class PaymentView(View):
    """Платёжная система (Карта/Paypal)"""

    def get(self, *args, **kwargs):
        """Отображение страницы платежа"""
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'order': order}
            return render(self.request, "payment.html", context)
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

            # Прикрепление платежа к заказу
            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Ваш заказ был успешно оплачен!")
            return redirect("/")

        except Order.DoesNotExist:
            messages.error(self.request, 'У вас нет активного заказа')
            return redirect('core:home')

        # https://stripe.com/docs/api/errors/handling?lang=python
        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Not authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Network error")
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(
                self.request,
                "Something went wrong. You were not charged. Please try again."
            )
            return redirect("/")

        except Exception as e:
            # send an email to ourselves
            messages.error(
                self.request, "A serious error occurred. We have been notifed."
            )
            return redirect("/")
