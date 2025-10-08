from django import forms
from django.forms import ModelForm
from .models import Room, User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2']

class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']

class UserForm(ModelForm):
    # تغییر ویجت avatar برای حذف متن "Currently"
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label=""  # label خالی
    )

    class Meta:
        model = User
        fields = ['avatar', 'name', 'email', 'bio']



class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'myfake@gmail.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError("User with this email does not exist.")

            # Authenticate correctly
            user = authenticate(username=user.email, password=password)  # اگر email یوزرنیم است
            if not user:
                raise forms.ValidationError("Incorrect email or password.")
        return cleaned_data


from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomPasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")

        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match")

        # Optional: add Django’s password validators
        from django.contrib.auth.password_validation import validate_password
        validate_password(p1, self.user)

        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
