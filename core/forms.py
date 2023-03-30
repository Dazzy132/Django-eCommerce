from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('S', 'Карта'),
    ('P', 'Paypal'),
)


class CheckoutForm(forms.Form):
    """Форма оплаты заказа"""
    # Часть с адресом доставки
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    # pip install django-countries | formfield - поле с точками
    shipping_country = CountryField(blank_label='(Выбери страну)').formfield(
        required=False,
        widget=CountrySelectWidget(
            attrs={'class': 'custom-select d-block w-100'}
        ))
    shipping_zip = forms.CharField(required=False)
    # ----------------------------

    # Часть с платежным адресом доставки
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label='(Выбери страну)').formfield(
        required=False,
        widget=CountrySelectWidget(
            attrs={'class': 'custom-select d-block w-100'}
        ))
    billing_zip = forms.CharField(required=False)
    # ----------------------------

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect(), choices=PAYMENT_CHOICES
    )


class CouponForm(forms.Form):
    """Форма для купонов"""
    code = forms.CharField(widget=forms.TextInput(attrs={
        "class": 'form-control', 'placeholder': 'Введите промокод',
        'aria-label': "Recipient's username", 'aria-describedby': "basic-addon2"
    }))


class RefundForm(forms.Form):
    """Форма для возврата денег"""
    ref_code = forms.CharField(label='Код покупки')
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}),
                              label='Сообщение')
    email = forms.EmailField(label='Email')


class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)