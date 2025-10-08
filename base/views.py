from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Room, Topic, Message, User
from .forms import RoomForm , UserForm , MyUserCreationForm
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from .forms import MyUserCreationForm
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

def loginPage(request):
    page = "login"
    field_errors = {}  # store errors per field

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
            # check password
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                field_errors['password'] = "Password is incorrect"
        except User.DoesNotExist:
            field_errors['email'] = "User does not exist"

    context = {
        'page': page,
        'field_errors': field_errors,
        'email_value': request.POST.get('email', '')
    }
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)     
    return redirect('home')




from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from .forms import MyUserCreationForm

User = get_user_model()
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings

from .forms import MyUserCreationForm
from .models import User


# 🔹 Register View
def registerPage(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # حذف کاربران غیرفعال با همین ایمیل
        User.objects.filter(email=email, is_active=False).delete()

        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.name = user.name.lower()
            user.is_active = False  # تا قبل از فعال‌سازی ایمیل، غیرفعال بماند
            user.save()

            # 📩 ارسال ایمیل فعال‌سازی
            current_site = get_current_site(request)
            subject = 'Activate Your Account'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]

            # ساخت لینک فعال‌سازی
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activate_url = f"http://{current_site.domain}{reverse('activate', kwargs={'uidb64': uid, 'token': token})}"

            # HTML ایمیل
            html_content = render_to_string('base/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
                'activate_url': activate_url,
            })

            # متن ساده (fallback)
            text_content = f"Hi {user.name or user.email},\nPlease activate your account:\n{activate_url}"

            # ارسال ایمیل
            email_message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            return render(request, 'base/registration_pending.html', {'email': user.email})

        else:
            print(form.errors)
            messages.error(request, "Something went wrong. Please check the form.")
    else:
        form = MyUserCreationForm()

    return render(request, 'base/login_register.html', {'form': form})


# 🔹 Account Activation View (با لاگین خودکار)
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save()

        # ✅ لاگین خودکار بعد از فعال‌سازی
        login(request, user)

        messages.success(request, "Your account has been activated and you are now logged in.")
        return redirect('complete_profile')  # یا هر صفحه‌ای مثل 'home'
    else:
        messages.error(request, "Activation link is invalid or expired.")
        return render(request, 'base/activation_invalid.html')



def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter (
        Q(topic__name__icontains =q) |
        Q(name__icontains =q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:4]   
    room_count = rooms.count()  
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    context = {'rooms': rooms, 'topics': topics,
     'room_count': room_count, 'room_messages':room_messages}
    
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        messages = Message.objects.create(
            user= request.user,
            room=room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)


    context = {'room': room, 'room_messages': room_messages,'participants':participants}
    return render(request, 'base/room.html', context)

def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user':user, 'rooms':rooms,
                'room_messages':room_messages, 'topics':topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),

        )
        

        return redirect('home')    
    context = {'form':form, 'topics':topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    topics = Topic.objects.all()
    form = RoomForm(instance=room)
    
    if request.user != room.host:
        return HttpResponse("you are not host!")

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    
    context = {'form':form,'topics':topics, 'room':room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.user != room.host:
        return HttpResponse("you are not host!")
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj':room})

@login_required(login_url='login')


def deleteMessage(request, pk):
    message = get_object_or_404(Message, id=pk)

    if request.user != message.user:
        return HttpResponse("You are not host!")

    if request.method == 'POST':
        message.delete()
        # برگرداندن کاربر به صفحه قبلی، در صورت نبود URL صفحه قبل به home برمیگردد
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')   
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    return render(request, 'base/update-user.html', {'form':form} )

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''                          
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics':topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages':room_messages})

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone

User = get_user_model()

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')

            html_content = render_to_string('base/reset_password_email.html', {
                'user': user,
                'reset_link': reset_link,
                'current_year': timezone.now().year,
            })
            text_content = strip_tags(html_content)

            subject = 'Reset Your Password'
            from_email = settings.DEFAULT_FROM_EMAIL
            to = [user.email]

            msg = EmailMultiAlternatives(subject, text_content, from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, "We sent you a password reset link to your email.")
            return redirect('forgot_password')
        except User.DoesNotExist:
            messages.error(request, "No user found with that email.")

    return render(request, 'base/forgot_password.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from .forms import CustomPasswordResetForm

User = get_user_model()

def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_object_or_404(User, pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = CustomPasswordResetForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('login')
        else:
            form = CustomPasswordResetForm(user)
    else:
        validlink = False
        form = None

    return render(request, 'base/reset_password.html', {
        'form': form,
        'validlink': validlink
    })
