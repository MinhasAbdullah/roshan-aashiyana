from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Sum, Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.core.files.storage import default_storage
from urllib.parse import urlencode
from django.urls import reverse
import re
import resend
import stripe
import base64
from django.core.files.base import ContentFile
import json
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate

from .models import (
    Property,
    Dealer,
    PropertyImage,
    Features,
    PropertyType,
    DealerReview,
    Inquiry,
    Favorite,
    ContactMessage,
)


def send_email(to, subject, html_message):
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": "Roshan Aashiyana <support@roshanaashiyana.xyz>",
            "to": to,
            "subject": subject,
            "html": html_message,
        })
    except Exception as e:
        print(f"Email error: {e}")


# ─────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────
def SignUp(request):
    if request.method == "POST":
        uname     = request.POST.get("uname", "").strip()
        email     = request.POST.get("email", "").strip()
        password  = request.POST.get("password", "")
        cpassword = request.POST.get("cpassword", "")

        error = None
        if len(uname) < 6:
            error = "Username must be at least 6 characters."
        elif not re.match(r"^[a-zA-Z0-9_]+$", uname):
            error = "Username can only contain letters, numbers and underscores."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != cpassword:
            error = "Passwords do not match."
        elif User.objects.filter(username=uname).exists():
            error = "Username already taken. Please choose another."
        elif User.objects.filter(email=email).exists():
            error = "An account with this email already exists."

        if error:
            params = urlencode({"auth_error": error, "auth_form": "signup", "auth_uname": uname, "auth_email": email})
            return redirect(f"{reverse('home')}?{params}")

        user = User.objects.create_user(username=uname, email=email, password=password)
        user.is_active = False
        user.save()

        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification = request.build_absolute_uri(f"/verify-email/{uid}/{token}/")

        send_email(
            to=user.email,
            subject="Verify Your Email — Roshan Aashiyana",
            html_message=f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;background:#f7f8fa;padding:32px;border-radius:12px;">
                <div style="background:#071a34;padding:24px 32px;border-radius:12px 12px 0 0;text-align:center;">
                    <img src="https://roshanaashiyana.xyz/static/images/RA3.png" alt="Roshan Aashiyana" style="height:68px;">
                </div>
                <div style="background:#ffffff;padding:32px;border-radius:0 0 12px 12px;border:1px solid #e4e8ee;">
                    <h2 style="color:#071a34;margin-bottom:8px;">Verify your email address</h2>
                    <p style="color:#6b7a90;line-height:1.6;">Hi <strong style="color:#1a2535;">{user.username}</strong>,</p>
                    <p style="color:#6b7a90;line-height:1.6;">Thanks for signing up on <strong style="color:#1a2535;">Roshan Aashiyana</strong>. Click the button below to verify your email and activate your account.</p>
                    <div style="text-align:center;margin:32px 0;">
                        <a href="{verification}" style="display:inline-block;padding:14px 32px;background:#3cb648;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;font-size:15px;">Verify My Email</a>
                    </div>
                    <div style="background:#edf8f0;border-left:4px solid #3cb648;padding:12px 16px;border-radius:8px;">
                        <p style="color:#6b7a90;font-size:13px;margin:0;">Or copy this link into your browser:<br>
                        <a href="{verification}" style="color:#3cb648;word-break:break-all;">{verification}</a></p>
                    </div>
                    <hr style="border:none;border-top:1px solid #e4e8ee;margin:24px 0;">
                    <p style="color:#6b7a90;font-size:12px;">If you did not create this account, you can safely ignore this email.</p>
                    <p style="color:#6b7a90;font-size:12px;margin:0;">© Roshan Aashiyana · Pakistan's Trusted Property Platform</p>
                </div>
            </div>
            """
            )

        messages.success(request, "Account created successfully. Please check your email and verify your account.")
        return redirect("home")

    return redirect("home")


def SignIn(request):
    if request.method == "POST":
        uname    = request.POST.get("uname", "").strip()
        password = request.POST.get("password", "")

        user_obj = User.objects.filter(username=uname).first()
        if user_obj and user_obj.check_password(password) and not user_obj.is_active:
            messages.error(request, "Please verify your email first.")
            return redirect("home")

        user = authenticate(request, username=uname, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login Successfully")
            return redirect("home")

        params = urlencode({"auth_error": "Invalid username or password. Please try again", "auth_form": "login", "auth_uname": uname})
        return redirect(f"{reverse('home')}?{params}")

    return redirect("home")


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        user = User.objects.filter(email__iexact=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(reverse('reset_password', args=[uid, token]))
            send_email(
                to=user.email,
                subject="Reset Your Password — Roshan Aashiyana",
                html_message=f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;background:#f7f8fa;padding:32px;border-radius:12px;">
                    <div style="background:#071a34;padding:24px 32px;border-radius:12px 12px 0 0;text-align:center;">
                        <img src="https://roshanaashiyana.xyz/static/images/RA3.png" alt="Roshan Aashiyana" style="height:68px;">
                    </div>
                    <div style="background:#ffffff;padding:32px;border-radius:0 0 12px 12px;border:1px solid #e4e8ee;">
                        <h2 style="color:#071a34;margin-bottom:8px;">Reset your password</h2>
                        <p style="color:#6b7a90;line-height:1.6;">Hi <strong style="color:#1a2535;">{user.username}</strong>,</p>
                        <p style="color:#6b7a90;line-height:1.6;">We received a request to reset your password for Roshan Aashiyana. Click the button below to continue.</p>
                        <div style="text-align:center;margin:32px 0;">
                            <a href="{reset_url}" style="display:inline-block;padding:14px 32px;background:#3cb648;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;font-size:15px;">Reset Password</a>
                        </div>
                        <div style="background:#edf8f0;border-left:4px solid #3cb648;padding:12px 16px;border-radius:8px;">
                            <p style="color:#6b7a90;font-size:13px;margin:0;">If you did not request this, you can safely ignore this email.</p>
                        </div>
                    </div>
                </div>
                """
            )

        params = urlencode({"auth_form": "forgot", "auth_success": "If an account exists for that email, we’ve sent reset instructions. Please check your inbox and spam/junk folder."})
        return redirect(f"{reverse('home')}?{params}")

    return redirect("home")


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if not user or not default_token_generator.check_token(user, token):
        messages.error(request, "This password reset link is invalid or has expired.")
        return redirect("home")

    if request.method == "POST":
        password = request.POST.get("password", "")
        cpassword = request.POST.get("cpassword", "")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, "reset_password.html", {"user": user, "valid": True})
        if password != cpassword:
            messages.error(request, "Passwords do not match.")
            return render(request, "reset_password.html", {"user": user, "valid": True})

        user.set_password(password)
        user.save()
        messages.success(request, "Password updated successfully. You can now login with your new password.")
        return redirect("home")

    return render(request, "reset_password.html", {"user": user, "valid": True})


def logout_user(request):
    logout(request)
    messages.success(request, "You're Logged out successfully")
    return redirect("home")


def verify_email(request, uidb64, token):
    try:
        uid  = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        send_email(
            to=user.email,
            subject="Welcome to Roshan Aashiyana 🎉",
            html_message=f"""
                    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;background:#f7f8fa;padding:32px;border-radius:12px;">
                        <div style="background:#071a34;padding:24px 32px;border-radius:12px 12px 0 0;text-align:center;">
                            <img src="https://roshanaashiyana.xyz/static/images/RA3.png" alt="Roshan Aashiyana" style="height:68px;">
                        </div>
                        <div style="background:#ffffff;padding:32px;border-radius:0 0 12px 12px;border:1px solid #e4e8ee;">
                            <h2 style="color:#071a34;">Welcome aboard, {user.username}! 👋</h2>
                            <p style="color:#6b7a90;line-height:1.6;">Your email has been verified successfully. You're now part of <strong style="color:#1a2535;">Roshan Aashiyana</strong> — Pakistan's trusted property platform.</p>
                            <p style="color:#6b7a90;line-height:1.6;">Start exploring thousands of properties across Islamabad, Lahore, Rawalpindi and more.</p>
                            <div style="text-align:center;margin:32px 0;">
                                <a href="https://roshanaashiyana.xyz" style="display:inline-block;padding:14px 32px;background:#3cb648;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;font-size:15px;">Browse Properties</a>
                            </div>
                            <hr style="border:none;border-top:1px solid #e4e8ee;margin:24px 0;">
                            <p style="color:#6b7a90;font-size:12px;margin:0;">© Roshan Aashiyana · Pakistan's Trusted Property Platform</p>
                        </div>
                    </div>
                    """
                    )
        messages.success(request, "Email verified successfully. You can now login.")
    else:
        messages.error(request, "Invalid or expired verification link.")

    return redirect("home")


# ─────────────────────────────────────────
# PUBLIC VIEWS
# ─────────────────────────────────────────
def home(request):
    properties = Property.objects.filter(is_featured=True).order_by("-created_at")
    return render(request, "home.html", {"prop": properties})

@login_required
def change_username(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data     = json.loads(request.body)
        username = data.get('username', '').strip()

        if len(username) < 6:
            return JsonResponse({'error': 'Username must be at least 6 characters.'})
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return JsonResponse({'error': 'Only letters, numbers and underscores allowed.'})
        if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
            return JsonResponse({'error': 'Username already taken.'})

        request.user.username = username
        request.user.save()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def change_password(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data             = json.loads(request.body)
        current_password = data.get('current_password', '')
        new_password     = data.get('new_password', '')

        if not request.user.check_password(current_password):
            return JsonResponse({'error': 'Current password is incorrect.'})
        if len(new_password) < 6:
            return JsonResponse({'error': 'New password must be at least 6 characters.'})

        request.user.set_password(new_password)
        request.user.save()
        login(request, request.user)   # keep session alive
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def listings(request):
    properties = Property.objects.filter().order_by("-created_at")

    keyword = request.GET.get("keyword")
    if keyword:
        properties = properties.filter(
            Q(title__icontains=keyword)
            | Q(city__icontains=keyword)
            | Q(area__icontains=keyword)
            | Q(address__icontains=keyword)
        )

    property_type = request.GET.get("property_type")
    if property_type:
        properties = properties.filter(property_type__name=property_type)

    purpose = request.GET.get("purpose")
    if purpose:
        properties = properties.filter(purpose=purpose)

    sort = request.GET.get("sort")
    if sort == "latest":
        properties = properties.order_by("-created_at")
    elif sort == "low":
        properties = properties.order_by("price")
    elif sort == "high":
        properties = properties.order_by("-price")

    city = request.GET.get("city")
    if city:
        properties = properties.filter(city__iexact=city)

    bedrooms = request.GET.get("bedrooms")
    if bedrooms:
        properties = properties.filter(bedrooms__gte=bedrooms)

    if request.user.is_authenticated:
        favourite_ids = list(Favorite.objects.filter(user=request.user).values_list("property_id", flat=True))
    else:
        favourite_ids = []

    paginator = Paginator(properties, 12)
    page_obj  = paginator.get_page(request.GET.get("page"))

    return render(request, "listings.html", {"prop": page_obj, "favourite_ids": favourite_ids})


def autocomplete(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)

    titles = Property.objects.filter(title__icontains=q).values_list('title', flat=True)[:5]
    cities = Property.objects.filter(city__icontains=q).values_list('city', flat=True).distinct()[:3]
    suggestions = list(dict.fromkeys(list(cities) + list(titles)))[:8]
    return JsonResponse(suggestions, safe=False)


def property_detail(request, id, slug):
    property = get_object_or_404(Property, id=id)
    dealer   = property.dealer
    reviews  = DealerReview.objects.filter(property=property)

    property.views += 1
    property.save()

    if request.method == "POST" and "send_review" in request.POST:
        DealerReview.objects.create(
            property=property,
            user=request.user,
            rating=request.POST.get("rating"),
            comment=request.POST.get("comment"),
        )
        return redirect("property_detail", id=property.id, slug=property.slug)

    if request.method == "POST" and "send_inquiry" in request.POST:
        name    = request.POST.get("name")
        email   = request.POST.get("email")
        phone   = request.POST.get("phone")
        message = request.POST.get("message")

        Inquiry.objects.create(property=property, name=name, email=email, phone=phone, message=message)

        send_email(
            to=dealer.user.email,
            subject=f"New Inquiry — {property.title}",
            html_message=f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;background:#f7f8fa;padding:32px;border-radius:12px;">
                    <div style="background:#071a34;padding:24px 32px;border-radius:12px 12px 0 0;text-align:center;">
                        <img src="https://roshanaashiyana.xyz/static/images/RA3.png" alt="Roshan Aashiyana" style="height:68px;">
                    </div>
                    <div style="background:#ffffff;padding:32px;border-radius:0 0 12px 12px;border:1px solid #e4e8ee;">
                        <h2 style="color:#071a34;">You have a new inquiry</h2>
                        <p style="color:#6b7a90;">Someone is interested in your property:</p>
                        <div style="background:#edf8f0;border-left:4px solid #3cb648;padding:12px 16px;margin:16px 0;border-radius:8px;">
                            <strong style="color:#071a34;">{property.title}</strong>
                        </div>
                        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                            <tr style="border-bottom:1px solid #e4e8ee;">
                                <td style="padding:10px 0;color:#6b7a90;width:80px;">Name</td>
                                <td style="color:#1a2535;"><strong>{name}</strong></td>
                            </tr>
                            <tr style="border-bottom:1px solid #e4e8ee;">
                                <td style="padding:10px 0;color:#6b7a90;">Email</td>
                                <td><a href="mailto:{email}" style="color:#3cb648;">{email}</a></td>
                            </tr>
                            <tr>
                                <td style="padding:10px 0;color:#6b7a90;">Phone</td>
                                <td><a href="tel:{phone}" style="color:#3cb648;">{phone}</a></td>
                            </tr>
                        </table>
                        <p style="color:#6b7a90;font-size:13px;margin-bottom:6px;">Message:</p>
                        <div style="background:#f7f8fa;padding:16px;border-radius:8px;border:1px solid #e4e8ee;color:#1a2535;line-height:1.6;">{message}</div>
                        <div style="text-align:center;margin:32px 0;">
                            <a href="https://roshanaashiyana.xyz/dealer_inquiries" style="display:inline-block;padding:14px 32px;background:#3cb648;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;font-size:15px;">View Inquiries</a>
                        </div>
                        <hr style="border:none;border-top:1px solid #e4e8ee;margin:24px 0;">
                        <p style="color:#6b7a90;font-size:12px;margin:0;">© Roshan Aashiyana · Pakistan's Trusted Property Platform</p>
                    </div>
                </div>
                """
                        )

        messages.success(request, "Inquiry sent successfully")
        return redirect("property_detail", slug=property.slug, id=property.id)

    is_favourite = False
    if request.user.is_authenticated:
        is_favourite = Favorite.objects.filter(user=request.user, property=property).exists()

    return render(request, "property_detail.html", {
        "prop": property,
        "dealer": dealer,
        "reviews": reviews,
        "is_favourite": is_favourite,
    })


def about(request):
    if request.method == "POST":
        ContactMessage.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            subject=request.POST.get("subject"),
            message=request.POST.get("message"),
        )
        messages.success(request, "Your message has been sent successfully.")
        return redirect("about")
    return render(request, "about.html")


def dealers(request):
    all_dealers = Dealer.objects.annotate(
        listing_count=Count('properties'),
        total_views=Sum('properties__views'),
    ).order_by('full_name')
    return render(request, 'dealers.html', {'dealers': all_dealers})


def dealer_profile(request, id):
    dealer      = get_object_or_404(Dealer, id=id)
    properties  = Property.objects.filter(dealer=dealer).order_by('-created_at')
    reviews     = DealerReview.objects.filter(property__dealer=dealer).order_by('-created_at')
    total_views = properties.aggregate(Sum('views'))['views__sum'] or 0
    avg_rating  = reviews.aggregate(Avg('rating'))['rating__avg']

    return render(request, 'dealer_profile.html', {
        'dealer':      dealer,
        'properties':  properties,
        'reviews':     reviews,
        'total_views': total_views,
        'avg_rating':  round(avg_rating, 1) if avg_rating else None,
    })


def check_cnic(request):
    cnic   = request.GET.get("cnic", "").strip()
    exists = Dealer.objects.filter(cnic=cnic).exists()
    return JsonResponse({"exists": exists})



@login_required
def dealer_register(request):
    # Already a dealer — go to dashboard
    if Dealer.objects.filter(user=request.user).exists():
        return redirect("dashboard")

    errors = {}
    old    = {}

    if request.method == "POST":
        name    = request.POST.get("name", "").strip()
        cnic    = request.POST.get("cnic", "").strip()
        address = request.POST.get("address", "").strip()
        gender  = request.POST.get("gender", "")
        phone   = request.POST.get("phone", "").strip()
        picture = request.FILES.get("picture")

        old = {"name": name, "cnic": cnic, "phone": phone, "gender": gender, "address": address}

        # ── Validations ──
        if len(name) < 3:
            errors["name"] = "Full name must be at least 3 characters."

        cnic_pattern = r"^\d{5}-\d{7}-\d{1}$"
        if not cnic:
            errors["cnic"] = "CNIC is required."
        elif not re.match(cnic_pattern, cnic):
            errors["cnic"] = "Invalid format. Use: 35202-1234567-1"
        elif Dealer.objects.filter(cnic=cnic).exists():
            errors["cnic"] = "A dealer with this CNIC already exists."

        phone_pattern = r"^\+92[0-9]{10}$"
        if not phone:
            errors["phone"] = "Phone number is required."
        elif not re.match(phone_pattern, phone):
            errors["phone"] = "Enter phone in +92XXXXXXXXXX format (e.g. +923001234567)"

        if not address:
            errors["address"] = "Address is required."

        if not picture:
            errors["picture"] = "Please upload a profile picture."

        if not errors:
            pic_data = base64.b64encode(picture.read()).decode('utf-8')

            # Save all form data in session
            request.session['dealer_form'] = {
                'name':     name,
                'cnic':     cnic,
                'address':  address,
                'gender':   gender,
                'phone':    phone,
                'pic_base64': pic_data,
                'pic_name': picture.name,
                'pic_type': picture.content_type,
            }
            # Go to payment
            return redirect('dealer_payment')

    return render(request, "dealer_register.html", {"errors": errors, "old": old})


@login_required
def dealer_payment(request):
    # Already a dealer
    if Dealer.objects.filter(user=request.user).exists():
        return redirect('dashboard')

    # No form data in session — send back to register
    if not request.session.get('dealer_form'):
        messages.error(request, 'Please fill the registration form first.')
        return redirect('dealer_register')

    return render(request, 'dealer_payment.html')


@login_required
def payment_success(request):
    dealer_data = request.session.get('dealer_form')

    # Session expired or missing
    if not dealer_data:
        messages.error(request, 'Session expired. Please fill the form again.')
        return redirect('dealer_register')

    # Already a dealer (e.g. user hit back and paid again)
    if Dealer.objects.filter(user=request.user).exists():
        return redirect('dashboard')
    
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Invalid payment. Please try again.')
        return redirect('dealer_payment')


    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        # Verify payment was actually paid
        if checkout_session.payment_status != 'paid':
            messages.error(request, 'Payment not completed. Please try again.')
            return redirect('dealer_payment')

        # Verify the user id matches
        if str(checkout_session.client_reference_id) != str(request.user.id):
            messages.error(request, 'Payment verification failed.')
            return redirect('dealer_payment')

    except stripe.error.StripeError:
        messages.error(request, 'Could not verify payment. Please contact support.')
        return redirect('dealer_payment')
    
    pic_bytes = base64.b64decode(dealer_data['pic_base64'])
    pic_file  = ContentFile(pic_bytes, name=dealer_data['pic_name'])
    pic_path  = default_storage.save(f'dealers/{dealer_data["pic_name"]}', pic_file)




    # Create dealer account from session data
    Dealer.objects.create(
        user=request.user,
        full_name=dealer_data['name'],
        cnic=dealer_data['cnic'],
        address=dealer_data['address'],
        gender=dealer_data['gender'],
        phone=dealer_data['phone'],
        profile_picture=pic_path,
    )

    # Clear session
    del request.session['dealer_form']
    dealer = Dealer.objects.get(user=request.user)

    # Send welcome email
    send_email(
        to=request.user.email,
        subject="Dealer Account Created — Roshan Aashiyana",
        html_message=f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;background:#f7f8fa;padding:32px;border-radius:12px;">
                    <div style="background:#071a34;padding:24px 32px;border-radius:12px 12px 0 0;text-align:center;">
                        <img src="https://roshanaashiyana.xyz/static/images/RA3.png" alt="Roshan Aashiyana" style="height:68px;">
                    </div>
                    <div style="background:#ffffff;padding:32px;border-radius:0 0 12px 12px;border:1px solid #e4e8ee;">
                        <h2 style="color:#071a34;">Dealer Account Created 🎉</h2>
                        <p style="color:#6b7a90;line-height:1.6;">Hi <strong style="color:#1a2535;">{dealer.full_name}</strong>,</p>
                        <p style="color:#6b7a90;line-height:1.6;">Your dealer account has been created successfully on <strong style="color:#1a2535;">Roshan Aashiyana</strong>. You can now list and manage properties on the platform.</p>
                        <div style="text-align:center;margin:32px 0;">
                            <a href="https://roshanaashiyana.xyz/dashboard" style="display:inline-block;padding:14px 32px;background:#3cb648;color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;font-size:15px;">Go to Dashboard</a>
                        </div>
                        <hr style="border:none;border-top:1px solid #e4e8ee;margin:24px 0;">
                        <p style="color:#6b7a90;font-size:12px;margin:0;">© Roshan Aashiyana · Pakistan's Trusted Property Platform</p>
                    </div>
                </div>
                """
                )

    messages.success(request, 'Payment successful! Your dealer account is now active.')
    return redirect('dashboard')


# ─────────────────────────────────────────
# DEALER DASHBOARD VIEWS
# ─────────────────────────────────────────
@login_required
def dashboard(request):
    try:
        dealer = Dealer.objects.get(user=request.user)
    except Dealer.DoesNotExist:
        return redirect("dealer_register")

    properties      = Property.objects.filter(dealer=dealer)
    inquiries       = Inquiry.objects.filter(property__in=properties)
    total_inquiries = inquiries.count()
    total_views     = properties.aggregate(Sum("views"))["views__sum"] or 0

    return render(request, "dashboard.html", {
        "dealer":          dealer,
        "prop":            properties,
        "views":           total_views,
        "inquiries":       inquiries,
        "inquiries_total": total_inquiries,
    })


@login_required
def add_property(request):
    try:
        dealer = Dealer.objects.get(user=request.user)
    except Dealer.DoesNotExist:
        return redirect('dealer_register')

    errors       = {}
    old          = {}
    old_features = []

    if request.method == "POST":
        title            = request.POST.get("title", "").strip()
        price            = request.POST.get("price", "").strip()
        description      = request.POST.get("description", "").strip()
        property_type_id = request.POST.get("property_type", "").strip()
        purpose          = request.POST.get("purpose", "sale")
        city             = request.POST.get("city", "").strip()
        area             = request.POST.get("area", "").strip()
        address          = request.POST.get("address", "").strip()
        bedrooms         = request.POST.get("bedrooms", "0")
        bathrooms        = request.POST.get("bathrooms", "0")
        kitchens         = request.POST.get("kitchens", "0")
        garages          = request.POST.get("garages", "0")
        property_size    = request.POST.get("property_size", "").strip()
        furnishing       = request.POST.get("furnishing", "semi_furnished")
        year_built       = request.POST.get("year_built", "").strip()
        featured_image   = request.FILES.get("featured_image")
        features_ids     = request.POST.getlist("features")

        old = {
            'title': title, 'price': price, 'description': description,
            'property_type': property_type_id, 'purpose': purpose,
            'city': city, 'area': area, 'address': address,
            'bedrooms': bedrooms, 'bathrooms': bathrooms,
            'kitchens': kitchens, 'garages': garages,
            'property_size': property_size, 'furnishing': furnishing,
            'year_built': year_built,
        }
        old_features = features_ids

        if not title or len(title) < 5:
            errors['title'] = "Title must be at least 5 characters."
        if not property_type_id:
            errors['property_type'] = "Please select a property type."
        if not price:
            errors['price'] = "Price is required."
        else:
            try:
                if float(price) <= 0:
                    errors['price'] = "Price must be greater than 0."
            except ValueError:
                errors['price'] = "Enter a valid price."
        if not city:
            errors['city'] = "City is required."
        if not area:
            errors['area'] = "Area / locality is required."
        if not description:
            errors['description'] = "Description is required."
        if not featured_image:
            errors['featured_image'] = "A featured image is required."
        elif hasattr(featured_image, 'content_type') and featured_image.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
            errors['featured_image'] = "Only JPG, PNG or WebP images are allowed."
        elif featured_image.size > 3 * 1024 * 1024:
            errors['featured_image'] = "Image too large. Maximum size is 3MB."

        if not errors:
            property_type = PropertyType.objects.get(id=property_type_id)
            prop = Property.objects.create(
                dealer=dealer,
                title=title,
                price=price,
                property_type=property_type,
                purpose=purpose,
                city=city,
                area=area,
                description=description,
                address=address,
                bedrooms=bedrooms or 0,
                bathrooms=bathrooms or 0,
                kitchens=kitchens or 0,
                garages=garages or 0,
                property_size=property_size,
                furnishing=furnishing,
                year_built=year_built or None,
                featured_image=featured_image,
            )
            prop.features.set(features_ids)

            for img in request.FILES.getlist("images"):
                if img:
                    PropertyImage.objects.create(property=prop, image=img)

            messages.success(request, "Property added successfully.")
            return redirect("dashboard")

    property_types = PropertyType.objects.all()
    features       = Features.objects.all()
    return render(request, "add_property.html", {
        "propertytype": property_types,
        "features":     features,
        "dealer":       dealer,
        "errors":       errors,
        "old":          old,
        "old_features": old_features,
    })


@login_required
def my_listings(request):
    dealer     = Dealer.objects.get(user=request.user)
    properties = Property.objects.filter(dealer=dealer).order_by("-created_at")
    return render(request, "my_listings.html", {"prop": properties, "dealer": dealer})


@login_required
def edit_property(request, id, slug):
    dealer   = Dealer.objects.get(user=request.user)
    property = get_object_or_404(Property, id=id, slug=slug, dealer=dealer)

    if request.method == "POST":
        property.title         = request.POST.get("title")
        property.price         = request.POST.get("price")
        property.description   = request.POST.get("description")
        property.purpose       = request.POST.get("purpose")
        property.city          = request.POST.get("city")
        property.area          = request.POST.get("area")
        property.address       = request.POST.get("address")
        property.bedrooms      = request.POST.get("bedrooms")
        property.bathrooms     = request.POST.get("bathrooms")
        property.kitchens      = request.POST.get("kitchens")
        property.garages       = request.POST.get("garages")
        property.property_size = request.POST.get("property_size")
        property.furnishing    = request.POST.get("furnishing")
        property.year_built    = request.POST.get("year_built")
        property.property_type = PropertyType.objects.get(id=request.POST.get("property_type"))

        if request.FILES.get("featured_image"):
            property.featured_image = request.FILES.get("featured_image")

        property.save()
        property.features.set(request.POST.getlist("features"))

        for img in request.FILES.getlist("images"):
            PropertyImage.objects.create(property=property, image=img)

        messages.success(request, "Property updated successfully")
        return redirect("my_listings")

    return render(request, "edit_property.html", {
        "prop":       property,
        "prop_types": PropertyType.objects.all(),
        "features":   Features.objects.all(),
        "dealer":     dealer,
    })


@login_required
def dealer_inquiries(request):
    dealer    = Dealer.objects.get(user=request.user)
    inquiries = Inquiry.objects.filter(property__dealer=dealer).order_by("-created_at")
    return render(request, "dealer_inquiries.html", {"inquiries": inquiries, "dealer": dealer})


@login_required
def dealer_reviews(request):
    dealer  = Dealer.objects.get(user=request.user)
    reviews = DealerReview.objects.filter(property__dealer=dealer).order_by("-created_at")
    return render(request, "dealer_reviews.html", {"dealer": dealer, "reviews": reviews})


@login_required
def add_favourite(request, id, slug):
    property  = get_object_or_404(Property, id=id, slug=slug)
    favourite = Favorite.objects.filter(user=request.user, property=property)

    if favourite.exists():
        favourite.delete()
    else:
        Favorite.objects.create(user=request.user, property=property)

    return redirect("property_detail", id=property.id, slug=property.slug)


@login_required
def favourites(request):
    favourite = Favorite.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "favourites.html", {"favourite": favourite})


@login_required
def delete_property(request, id, slug):
    dealer   = Dealer.objects.get(user=request.user)
    property = get_object_or_404(Property, id=id, slug=slug, dealer=dealer)
    property.delete()
    messages.success(request, "Property deleted successfully")
    return redirect("dashboard")

@login_required
def dealer_settings(request):
    try:
        dealer = Dealer.objects.get(user=request.user)
    except Dealer.DoesNotExist:
        return redirect('dealer_register')
 
    errors  = {}
    success = None
 
    CITIES = [
        'Islamabad', 'Rawalpindi', 'Lahore', 'Karachi', 'Faisalabad',
        'Multan', 'Peshawar', 'Quetta', 'Sialkot', 'Gujranwala',
        'Hyderabad', 'Abbottabad', 'Bahawalpur', 'Sargodha', 'Sukkur',
    ]
 
    properties_count = dealer.properties.count()
    reviews_count    = DealerReview.objects.filter(property__dealer=dealer).count()
 
    # ── Profile completion % ──
    fields = [
        dealer.description,
        dealer.phone,
        dealer.city,
        dealer.social_facebook or dealer.social_instagram or dealer.social_linkedin,
        dealer.profile_picture,
    ]
    completion_pct = int((sum(1 for f in fields if f) / len(fields)) * 100)
 
    if request.method == 'POST':
 
        # ══ SAVE PROFILE ══
        if 'save_profile' in request.POST:
            full_name   = request.POST.get('full_name', '').strip()
            gender      = request.POST.get('gender', '')
            description = request.POST.get('description', '').strip()
            picture_url = request.POST.get('profile_picture_url', '').strip()
 
            if len(full_name) < 3:
                errors['full_name'] = 'Full name must be at least 3 characters.'
 
            if not errors:
                dealer.full_name   = full_name
                dealer.gender      = gender
                dealer.description = description
                if picture_url:
                    dealer.profile_picture = picture_url
                dealer.save()
                success = 'Profile updated successfully.'
 
        # ══ SAVE CONTACT ══
        elif 'save_contact' in request.POST:
            phone    = request.POST.get('phone', '').strip()
            whatsapp = request.POST.get('whatsapp', '').strip()
            city     = request.POST.get('city', '').strip()
            address  = request.POST.get('address', '').strip()
 
            phone_pattern = r'^\+92[0-9]{10}$'
            if phone and not re.match(phone_pattern, phone):
                errors['phone'] = 'Enter phone in +92XXXXXXXXXX format.'
 
            if not errors:
                dealer.phone    = phone
                dealer.whatsapp = whatsapp
                dealer.city     = city
                dealer.address  = address
                dealer.save()
        
                success = 'Contact info updated successfully.'
 
        # ══ SAVE SOCIAL ══
        elif 'save_social' in request.POST:
            dealer.social_facebook  = request.POST.get('social_facebook', '').strip()
            dealer.social_instagram = request.POST.get('social_instagram', '').strip()
            dealer.social_linkedin  = request.POST.get('social_linkedin', '').strip()
            dealer.save()
        
            success = 'Social links updated successfully.'
 
        # ══ SAVE PASSWORD ══
        elif 'save_password' in request.POST:
            current_password = request.POST.get('current_password', '')
            new_password     = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
 
            if not request.user.check_password(current_password):
                errors['current_password'] = 'Current password is incorrect.'
            elif len(new_password) < 6:
                errors['new_password'] = 'New password must be at least 6 characters.'
            elif new_password != confirm_password:
                errors['confirm_password'] = 'Passwords do not match.'
 
            if not errors:
                request.user.set_password(new_password)
                request.user.save()
                login(request, request.user)
                success = 'Password updated successfully.'
 
    return render(request, 'dealer_settings.html', {
        'dealer':           dealer,
        'errors':           errors,
        'success':          success,
        'cities':           CITIES,
        'properties_count': properties_count,
        'reviews_count':    reviews_count,
        'completion_pct':   completion_pct,
    })

@login_required
def delete_dealer_account(request):
    try:
        dealer = Dealer.objects.get(user=request.user)
        dealer.delete()
        messages.success(request, 'Your dealer account has been deleted.')
    except Dealer.DoesNotExist:
        pass
    return redirect('home')


@login_required
def generate_description_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    data = json.loads(request.body)

    llm = ChatMistralAI(
        api_key=settings.MISTRAL_API_KEY,
        model='mistral-small-latest',
        temperature=0
    )

    prompt = ChatPromptTemplate.from_template("""
You are a professional real estate listing writer.
Convert structured property data into a clean, realistic description.
RULES:
- Use ONLY provided data
- Do NOT invent anything
- Do NOT exaggerate or add fake features
- 80 - 120 words
- Clear professional tone
- Combine features naturally
- If Extra Notes are provided, use them exactly
PROPERTY INFO:
Title: {title}
Purpose: {purpose}
Type: {property_type}
Price: {price}
LOCATION:
City: {city}
Area: {area}
Address: {address}
DETAILS:
Bedrooms: {bedrooms}
Bathrooms: {bathrooms}
Kitchens: {kitchens}
Garage: {garage}
Size: {property_size}
Year Built: {year_built}
Furnished: {furnished}
FEATURES: {features}
Extra Notes: {extra_description}
OUTPUT:
Return only the final property description.
""")

    chain = prompt | llm

    response = chain.invoke({
        "title":             data.get("title", ""),
        "purpose":           data.get("purpose", ""),
        "property_type":     data.get("property_type", ""),
        "price":             data.get("price", ""),
        "city":              data.get("city", ""),
        "area":              data.get("area", ""),
        "address":           data.get("address", ""),
        "bedrooms":          data.get("bedrooms", ""),
        "bathrooms":         data.get("bathrooms", ""),
        "kitchens":          data.get("kitchens", ""),
        "garage":            data.get("garage", ""),
        "property_size":     data.get("property_size", ""),
        "year_built":        data.get("year_built", ""),
        "furnished":         data.get("furnished", ""),
        "features":          data.get("features", ""),
        "extra_description": data.get("description", ""),
    })

    description = response.content.replace("**", "").strip()
    return JsonResponse({'description': description})


def terms(request):
    sections = [
        {
            'icon': 'fa-circle-check',
            'title': '1. Acceptance of Terms',
            'content': 'By accessing or using Roshan Aashiyana, you confirm that you are at least 18 years old and agree to comply with these Terms & Conditions. If you do not agree with any part of these terms, you must not use our platform.',
        },
        {
            'icon': 'fa-house',
            'title': '2. Platform Use',
            'content': 'Roshan Aashiyana is an online real estate marketplace that connects property buyers, renters, and verified dealers across Pakistan. We provide a platform for listing and discovering properties — we are not a real estate agency and do not own, sell, or rent any properties ourselves. All listings are posted by independent dealers.',
        },
        {
            'icon': 'fa-user-shield',
            'title': '3. User Accounts',
            'content': 'You are responsible for maintaining the confidentiality of your account credentials. You must not share your account with anyone or use another user\'s account. Any activity that occurs under your account is your responsibility. Roshan Aashiyana reserves the right to suspend or terminate accounts that violate these terms.',
        },
        {
            'icon': 'fa-id-card',
            'title': '4. Dealer Registration',
            'content': 'To become a verified dealer on Roshan Aashiyana, you must provide accurate personal information including your CNIC, phone number, and profile picture. A one-time registration fee is required, payable via Stripe. Providing false information during registration may result in permanent account termination without refund.',
        },
        {
            'icon': 'fa-list-check',
            'title': '5. Property Listings',
            'content': 'Dealers are solely responsible for the accuracy and legality of their property listings. Listings must not contain false, misleading, or fraudulent information. Roshan Aashiyana reserves the right to remove any listing that violates our policies without prior notice. We do not verify the legal ownership of listed properties.',
        },
        {
            'icon': 'fa-credit-card',
            'title': '6. Payments & Refunds',
            'content': 'All payments on Roshan Aashiyana are processed securely through Stripe. The dealer registration fee is non-refundable once your account has been successfully created. If payment was charged but the account was not created due to a technical error, please contact our support team within 7 days for assistance.',
        },
        {
            'icon': 'fa-ban',
            'title': '7. Prohibited Activities',
            'content': 'You must not use Roshan Aashiyana to post spam, fraudulent listings, or misleading content. You must not attempt to hack, reverse-engineer, or disrupt the platform. You must not collect user data without consent, post duplicate listings, or engage in any activity that violates Pakistani law.',
        },
        {
            'icon': 'fa-copyright',
            'title': '8. Intellectual Property',
            'content': 'All content on Roshan Aashiyana — including the logo, design, code, and platform features — is the intellectual property of Roshan Aashiyana. You may not copy, reproduce, or distribute any part of the platform without written permission. Property images uploaded by dealers remain the property of their respective owners.',
        },
        {
            'icon': 'fa-triangle-exclamation',
            'title': '9. Limitation of Liability',
            'content': 'Roshan Aashiyana is not liable for any disputes between buyers and dealers, inaccurate property information, financial losses resulting from property transactions, or any indirect, incidental, or consequential damages arising from the use of our platform. Users engage in property transactions at their own risk.',
        },
        {
            'icon': 'fa-pen',
            'title': '10. Changes to Terms',
            'content': 'Roshan Aashiyana reserves the right to update these Terms & Conditions at any time. Continued use of the platform after changes are posted constitutes your acceptance of the updated terms. We will notify registered users of significant changes via email.',
        },
    ]
    return render(request, 'terms.html', {'sections': sections})


def privacy(request):
    sections = [
        {
            'icon': 'fa-database',
            'title': '1. Information We Collect',
            'content': 'We collect information you provide directly: name, email address, username, phone number, CNIC (for dealers), profile picture, and property listing details. We also automatically collect usage data such as pages visited, search queries, and device information to improve our platform.',
        },
        {
            'icon': 'fa-gear',
            'title': '2. How We Use Your Information',
            'content': 'We use your information to create and manage your account, process dealer registrations and payments, send email notifications (verification, inquiries, welcome emails), display property listings, match buyers with relevant properties, and improve our platform features and performance.',
        },
        {
            'icon': 'fa-share-nodes',
            'title': '3. Information Sharing',
            'content': 'We do not sell your personal information to third parties. We share your information only with trusted service providers that help us operate the platform: Neon (database hosting), Cloudinary (image storage), Stripe (payment processing), and Resend (email delivery). These providers are contractually obligated to protect your data.',
        },
        {
            'icon': 'fa-image',
            'title': '4. Images & Media',
            'content': 'Property images and dealer profile pictures are uploaded to and stored on Cloudinary, a secure cloud storage service. These images may be publicly visible on the platform as part of property listings and dealer profiles. Please do not upload images containing sensitive personal information.',
        },
        {
            'icon': 'fa-cookie',
            'title': '5. Cookies & Sessions',
            'content': 'Roshan Aashiyana uses session cookies to keep you logged in during your visit. We do not use tracking cookies or third-party advertising cookies. You can disable cookies in your browser settings, but this may affect your ability to log in and use certain features of the platform.',
        },
        {
            'icon': 'fa-lock',
            'title': '6. Data Security',
            'content': 'We implement industry-standard security measures including HTTPS encryption, hashed passwords, secure session management, and CSRF protection. However, no method of transmission over the internet is 100% secure. We recommend using a strong, unique password for your account.',
        },
        {
            'icon': 'fa-child',
            'title': '7. Children\'s Privacy',
            'content': 'Roshan Aashiyana is not intended for use by anyone under the age of 18. We do not knowingly collect personal information from minors. If you believe a minor has created an account on our platform, please contact us and we will delete the account immediately.',
        },
        {
            'icon': 'fa-user-pen',
            'title': '8. Your Rights',
            'content': 'You have the right to access, update, or delete your personal information at any time through your account settings. You may request a copy of your data or ask us to delete your account by contacting support@roshanaashiyana.xyz. We will respond to all requests within 48 hours.',
        },
        {
            'icon': 'fa-pen',
            'title': '9. Changes to This Policy',
            'content': 'We may update this Privacy Policy from time to time. When we make significant changes, we will notify you via email and update the "Last updated" date at the top of this page. Continued use of the platform after changes are posted means you accept the updated policy.',
        },
    ]
    return render(request, 'privacy.html', {'sections': sections})


def faq(request):
    categories = [
        {
            'icon': 'fa-user',
            'title': 'General & Accounts',
            'faqs': [
                {
                    'q': 'What is Roshan Aashiyana?',
                    'a': 'Roshan Aashiyana is Pakistan\'s trusted online real estate marketplace connecting property buyers, renters, and verified dealers across major cities including Islamabad, Lahore, Rawalpindi, Karachi, and Multan.',
                },
                {
                    'q': 'Is Roshan Aashiyana free to use?',
                    'a': 'Yes! Browsing properties, searching listings, saving favourites, and contacting dealers is completely free for regular users. A one-time registration fee is required only to become a verified dealer and list properties.',
                },
                {
                    'q': 'How do I create an account?',
                    'a': 'Click the "Sign Up" button on the homepage, enter your username, email, and password, then verify your email address via the link we send you. Once verified, your account is active and ready to use.',
                },
                {
                    'q': 'I didn\'t receive my verification email. What should I do?',
                    'a': 'Check your spam or junk mail folder first. If it\'s not there, make sure you entered the correct email address during registration. You can contact our support team at support@roshanaashiyana.xyz for further assistance.',
                },
                {
                    'q': 'How do I reset my password?',
                    'a': 'Click "Forgot password?" on the login form, enter your registered email address, and we\'ll send you a password reset link instantly. The link expires after 1 hour for security purposes.',
                },
            ]
        },
        {
            'icon': 'fa-id-card',
            'title': 'Becoming a Dealer',
            'faqs': [
                {
                    'q': 'How do I become a verified dealer?',
                    'a': 'Click "Become a Dealer" in the navigation menu, fill in your personal details including your CNIC and phone number, upload a profile picture, and complete the one-time registration payment via Stripe. Your dealer account will be activated immediately after successful payment.',
                },
                {
                    'q': 'What is the dealer registration fee?',
                    'a': 'There is a one-time dealer registration fee to verify your identity and activate your dealer account. This fee is non-refundable. Please check the dealer registration page for the current fee amount.',
                },
                {
                    'q': 'Can I become a dealer if I\'m an individual, not an agency?',
                    'a': 'Absolutely. Both individual property owners and real estate agencies can register as dealers on Roshan Aashiyana. All dealers go through the same verification process.',
                },
                {
                    'q': 'How many properties can I list as a dealer?',
                    'a': 'There is currently no limit on the number of properties a verified dealer can list. You can add, edit, and manage as many listings as you need from your dealer dashboard.',
                },
            ]
        },
        {
            'icon': 'fa-building',
            'title': 'Property Listings',
            'faqs': [
                {
                    'q': 'How do I search for properties?',
                    'a': 'Use the search bar on the homepage or listings page to search by keyword, city, or area. You can filter results by property type (house, apartment, plot, etc.), purpose (sale or rent), number of bedrooms, and price range.',
                },
                {
                    'q': 'How do I contact a dealer about a property?',
                    'a': 'Open any property listing and scroll down to the inquiry form. Fill in your name, email, phone, and message, then click "Send Inquiry". The dealer will receive an email notification and can contact you directly.',
                },
                {
                    'q': 'Can I save properties to view later?',
                    'a': 'Yes! Click the heart icon on any property listing to add it to your favourites. You must be logged in to use this feature. Access all your saved properties from the "My Favourites" section in your account menu.',
                },
                {
                    'q': 'Are the property prices negotiable?',
                    'a': 'Prices are set by individual dealers. You can discuss pricing directly with the dealer through the inquiry system or by calling them using the contact details on their profile page.',
                },
                {
                    'q': 'How do I know if a property is still available?',
                    'a': 'Each listing shows an availability badge — "Available" or "Sold". Dealers can update their listing status at any time. We recommend confirming availability directly with the dealer before visiting a property.',
                },
            ]
        },
        {
            'icon': 'fa-credit-card',
            'title': 'Payments & Security',
            'faqs': [
                {
                    'q': 'Is my payment information secure?',
                    'a': 'Yes. All payments are processed through Stripe, a globally trusted payment processor used by millions of businesses. We never store your credit card details on our servers. All transactions are encrypted with industry-standard SSL.',
                },
                {
                    'q': 'Can I get a refund on the dealer registration fee?',
                    'a': 'The dealer registration fee is non-refundable once your account has been successfully created. If you were charged but your account was not created due to a technical error, please contact support@roshanaashiyana.xyz within 7 days.',
                },
                {
                    'q': 'Does Roshan Aashiyana handle property transactions?',
                    'a': 'No. Roshan Aashiyana is purely a listing and discovery platform. All property transactions, negotiations, and payments happen directly between buyers and dealers. We do not mediate or take any commission on property sales or rentals.',
                },
            ]
        },
    ]
    return render(request, 'faq.html', {'categories': categories})


def robots_txt(request):
    content = """User-agent: *
Disallow: /dashboard/
Disallow: /add-property/
Disallow: /edit-property/
Disallow: /my-listings/
Disallow: /dealer-register/
Disallow: /dealer-reviews/
Disallow: /dealer-inquiries/
Disallow: /dealer-settings/
Disallow: /favourites/
Disallow: /check-cnic/
Disallow: /logout/
Disallow: /delete-property/
Disallow: /delete-dealer-account/
Disallow: /admin/

Allow: /
Allow: /listings/
Allow: /property/
Allow: /about/
Allow: /dealers/

Sitemap: https://roshanaashiyana.xyz/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")