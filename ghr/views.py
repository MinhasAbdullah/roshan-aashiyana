from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Sum, Q, Count, Avg
from django.http import JsonResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.core.files.storage import default_storage
from urllib.parse import urlencode
from django.urls import reverse
import re
import resend
import stripe
import base64
from django.core.files.base import ContentFile

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
    properties = Property.objects.filter(is_featured="True").order_by("-created_at")
    return render(request, "home.html", {"prop": properties})


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


def house(request):
    properties = Property.objects.filter(property_type__name="House").order_by("-created_at")
    paginator  = Paginator(properties, 9)
    page_obj   = paginator.get_page(request.GET.get("page"))
    return render(request, "house.html", {"prop": page_obj})


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


# ─────────────────────────────────────────
# DEALER REGISTRATION + PAYMENT FLOW
#
# Flow:
#   1. dealer_register  → validate form → save to session → redirect to dealer_payment
#   2. dealer_payment   → show payment page with Stripe link
#   3. payment_success  → create Dealer from session → redirect to dashboard
# ─────────────────────────────────────────
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
    dealer = Dealer.objects.filter(user=request.user)

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