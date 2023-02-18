from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Item, OrderItem, Order


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
            return redirect("core:product", slug=slug)
        else:
            order.items.add(order_item)
            messages.info(request, 'Товар добавлен в вашу корзину')
            return redirect("core:product", slug=slug)
    # Если заказа нет, то создать его вручную и добавить товар в корзину
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date
        )
        order.items.add(order_item)
        messages.info(request, 'Товар добавлен в вашу корзину')
        return redirect("core:product", slug=slug)


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
            return redirect("core:product", slug=slug)
        # Если этого товара нет в корзине
        else:
            messages.info(request, "Этого предмета нет в вашей корзине")
            return redirect("core:product", slug=slug)
    # Если не создан заказ
    else:
        messages.info(request, "У вас нет активного заказа")
        return redirect("core:product", slug=slug)


def checkout(request):
    return render(request, "checkout.html")
