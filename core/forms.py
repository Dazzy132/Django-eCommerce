from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('S', 'Карта'),
    ('P', 'Paypal'),
)


class CheckoutForm(forms.Form):
    """Форма оплаты заказа"""
    street_address = forms.CharField(widget=forms.TextInput(
        attrs={"placeholder": "г. Краснодар, ул. Красная 56"}
    ))

    apartment_address = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"placeholder": "Квартира: 205"}
    ))

    # pip install django-countries | formfield - поле с точками
    country = CountryField(blank_label='(Выбери страну)').formfield(
        widget=CountrySelectWidget(
            attrs={'class': 'custom-select d-block w-100'}
        )
    )

    zip = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': '35000'})
    )

    # same_billing_address = forms.BooleanField(widget=forms.CheckboxInput())
    # Тот же адрес доставки?
    same_shipping_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)

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
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    email = forms.EmailField()