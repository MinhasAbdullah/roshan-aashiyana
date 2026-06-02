from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.http import JsonResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.conf import settings
from urllib.parse import urlencode
from django.urls import reverse
import re
import resend

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


# ─────────────────────────────────────────
# EMAIL HELPER — uses Resend HTTP API
# No SMTP, no timeouts, works on Railway
# ─────────────────────────────────────────
def send_email(to, subject, message):
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": "Roshan Aashiyana <support@roshanaashiyana.xyz>",
            "to": to,
            "subject": subject,
            "text": message,
        })
    except Exception as e:
        print(f"Email error: {e}")


# ─────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────
def SignUp(request):
    if request.method == "POST":
        uname = request.POST.get("uname", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
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
            params = urlencode({
                "auth_error": error,
                "auth_form": "signup",
                "auth_uname": uname,
                "auth_email": email,
            })
            return redirect(f"{reverse('home')}?{params}")

        user = User.objects.create_user(username=uname, email=email, password=password)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification = request.build_absolute_uri(f"/verify-email/{uid}/{token}/")

        send_email(
            to=user.email,
            subject="Verify Your Account — Roshan Aashiyana",
            message=f"""Hi {user.username},

Thank you for registering on Roshan Aashiyana.

Click the link below to verify your email:

{verification}

If you did not create this account, ignore this email.

Regards,
Roshan Aashiyana Team"""
        )

        messages.success(request, "Account created successfully. Please check your email and verify your account.")
        return redirect("home")

    return redirect("home")


def SignIn(request):
    if request.method == "POST":
        uname = request.POST.get("uname", "").strip()
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

        params = urlencode({
            "auth_error": "Invalid username or password. Please try again",
            "auth_form": "login",
            "auth_uname": uname,
        })
        return redirect(f"{reverse('home')}?{params}")

    return redirect("home")


def logout_user(request):
    logout(request)
    messages.success(request, "You're Logged out successfully")
    return redirect("home")


def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        send_email(
            to=user.email,
            subject="Welcome to Roshan Aashiyana",
            message=f"""Hi {user.username},

Your email has been verified successfully.

You can now login and start exploring properties across Pakistan.

Welcome to Roshan Aashiyana!

Regards,
Roshan Aashiyana Team"""
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
        favourite_ids = list(
            Favorite.objects.filter(user=request.user).values_list("property_id", flat=True)
        )
    else:
        favourite_ids = []

    paginator = Paginator(properties, 12)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(request, "listings.html", {"prop": page_obj, "favourite_ids": favourite_ids})


def autocomplete(request):
    q = request.GET.get('q', '').strip()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    titles = Property.objects.filter(
        title__icontains=q
    ).values_list('title', flat=True)[:5]

    cities = Property.objects.filter(
        city__icontains=q
    ).values_list('city', flat=True).distinct()[:3]

    suggestions = list(dict.fromkeys(
        list(cities) + list(titles)
    ))[:8]

    return JsonResponse(suggestions, safe=False)


def property_detail(request, id, slug):
    property = get_object_or_404(Property, id=id)
    dealer = property.dealer
    reviews = DealerReview.objects.filter(property=property)

    property.views += 1
    property.save()

    if request.method == "POST" and "send_review" in request.POST:
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        DealerReview.objects.create(
            property=property, user=request.user, rating=rating, comment=comment
        )
        return redirect("property_detail", id=property.id, slug=property.slug)

    if request.method == "POST" and "send_inquiry" in request.POST:
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        message = request.POST.get("message")

        Inquiry.objects.create(
            property=property, name=name, email=email, phone=phone, message=message
        )

        send_email(
            to=dealer.user.email,
            subject=f"New Inquiry For {property.title}",
            message=f"""You have received a new inquiry on Roshan Aashiyana.

Property: {property.title}

Name: {name}
Email: {email}
Phone: {phone}

Message:
{message}

Regards,
Roshan Aashiyana Team"""
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
    paginator = Paginator(properties, 9)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)
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


# ─────────────────────────────────────────
# DEALER VIEWS
# ─────────────────────────────────────────
@login_required
def dealer_register(request):
    if Dealer.objects.filter(user=request.user).exists():
        return redirect("dashboard")

    errors = {}
    old = {}

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        cnic = request.POST.get("cnic", "").strip()
        address = request.POST.get("address", "").strip()
        gender = request.POST.get("gender", "")
        phone = request.POST.get("phone", "").strip()
        picture = request.FILES.get("picture")

        old = {"name": name, "cnic": cnic, "phone": phone, "gender": gender, "address": address}

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
            dealer = Dealer.objects.create(
                user=request.user,
                full_name=name,
                cnic=cnic,
                address=address,
                gender=gender,
                phone=phone,
                profile_picture=picture,
            )

            send_email(
                to=request.user.email,
                subject="Dealer Account Created — Roshan Aashiyana",
                message=f"""Hi {dealer.full_name},

Your dealer profile has been created successfully on Roshan Aashiyana.

You can now list and manage properties on the platform.

Regards,
Roshan Aashiyana Team"""
            )

            return redirect("dashboard")

    return render(request, "dealer_register.html", {"errors": errors, "old": old})


@login_required
def dashboard(request):
    try:
        dealer = Dealer.objects.get(user=request.user)
    except Dealer.DoesNotExist:
        return redirect("dealer_register")

    properties = Property.objects.filter(dealer=dealer)
    inquiries = Inquiry.objects.filter(property__in=properties)
    total_inquiries = inquiries.count()
    total_views = properties.aggregate(Sum("views"))["views__sum"] or 0

    return render(request, "dashboard.html", {
        "dealer": dealer,
        "prop": properties,
        "views": total_views,
        "inquiries": inquiries,
        "inquiries_total": total_inquiries,
    })


def add_property(request):
    try:
        dealer = Dealer.objects.get(user=request.user)
    except Dealer.DoesNotExist:
        return redirect('dealer_register')
 
    errors   = {}
    old      = {}
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
 
        if not title:
            errors['title'] = "Property title is required."
        elif len(title) < 5:
            errors['title'] = "Title must be at least 5 characters."
 
        if not property_type_id:
            errors['property_type'] = "Please select a property type."
 
        if not price:
            errors['price'] = "Price is required."
        else:
            try:
                p = float(price)
                if p <= 0:
                    errors['price'] = "Price must be greater than 0."
            except ValueError:
                errors['price'] = "Enter a valid price."
 
        if not city:
            errors['city'] = "Please select a city."
 
        if not area:
            errors['area'] = "Area / locality is required."
 
        if not description:
            errors['description'] = "Description is required."
 
        # ── Featured image is REQUIRED ──
        if not featured_image:
            errors['featured_image'] = "A featured image is required. Please upload a photo."
        else:
            # Check file type
            allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
            if hasattr(featured_image, 'content_type') and featured_image.content_type not in allowed:
                errors['featured_image'] = "Only JPG, PNG or WebP images are allowed."
            # Check file size (5MB)
            elif featured_image.size > 3 * 1024 * 1024:
                errors['featured_image'] = "Image too large. Maximum size is 3MB."
 
        # ── If no errors — save ──
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
                bedrooms=bedrooms   or 0,
                bathrooms=bathrooms or 0,
                kitchens=kitchens   or 0,
                garages=garages     or 0,
                property_size=property_size,
                furnishing=furnishing,
                year_built=year_built or None,
                featured_image=featured_image,
            )
 
            prop.features.set(features_ids)
 
            images = request.FILES.getlist("images")
            for img in images:
                if img:
                    PropertyImage.objects.create(property=prop, image=img)
 
            messages.success(request, "Property added successfully.")
            return redirect("dashboard")
 
    property_types = PropertyType.objects.all()
    features       = Features.objects.all()
    return render(request, "add_property.html", {
        "propertytype":  property_types,
        "features":      features,
        "dealer":        dealer,
        "errors":        errors,
        "old":           old,
        "old_features":  old_features,
    })


@login_required
def my_listings(request):
    dealer = Dealer.objects.get(user=request.user)
    properties = Property.objects.filter(dealer=dealer).order_by("-created_at")
    return render(request, "my_listings.html", {"prop": properties, "dealer": dealer})


@login_required
def edit_property(request, id, slug):
    dealer = Dealer.objects.get(user=request.user)
    property = get_object_or_404(Property, id=id, slug=slug, dealer=dealer)

    if request.method == "POST":
        property.title = request.POST.get("title")
        property.price = request.POST.get("price")
        property.description = request.POST.get("description")
        property_type_id = request.POST.get("property_type")
        property.purpose = request.POST.get("purpose")
        property.city = request.POST.get("city")
        property.area = request.POST.get("area")
        property.address = request.POST.get("address")
        property.bedrooms = request.POST.get("bedrooms")
        property.bathrooms = request.POST.get("bathrooms")
        property.kitchens = request.POST.get("kitchens")
        property.garages = request.POST.get("garages")
        property.property_size = request.POST.get("property_size")
        property.furnishing = request.POST.get("furnishing")
        property.year_built = request.POST.get("year_built")
        property.property_type = PropertyType.objects.get(id=property_type_id)

        if request.FILES.get("featured_image"):
            property.featured_image = request.FILES.get("featured_image")

        property.save()

        features = request.POST.getlist("features")
        property.features.set(features)

        images = request.FILES.getlist("images")
        for img in images:
            PropertyImage.objects.create(property=property, image=img)

        messages.success(request, "Property updated successfully")
        return redirect("my_listings")

    property_type = PropertyType.objects.all()
    features = Features.objects.all()

    return render(request, "edit_property.html", {
        "prop": property,
        "prop_types": property_type,
        "features": features,
        "dealer": dealer,
    })


@login_required
def dealer_inquiries(request):
    dealer = Dealer.objects.get(user=request.user)
    inquiries = Inquiry.objects.filter(property__dealer=dealer).order_by("-created_at")
    return render(request, "dealer_inquiries.html", {"inquiries": inquiries, "dealer": dealer})


@login_required
def dealer_reviews(request):
    dealer = Dealer.objects.get(user=request.user)
    reviews = DealerReview.objects.filter(property__dealer=dealer).order_by("-created_at")
    return render(request, "dealer_reviews.html", {"dealer": dealer, "reviews": reviews})


@login_required
def add_favourite(request, id, slug):
    property = get_object_or_404(Property, id=id, slug=slug)
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
    dealer = Dealer.objects.get(user=request.user)
    property = get_object_or_404(Property, id=id, slug=slug, dealer=dealer)
    property.delete()
    messages.success(request, "Property deleted successfully")
    return redirect("dashboard")


def check_cnic(request):
    cnic = request.GET.get("cnic", "").strip()
    exists = Dealer.objects.filter(cnic=cnic).exists()
    return JsonResponse({"exists": exists})


def dealers(request):
    dealers = Dealer.objects.annotate(
        listing_count=Count('properties'),
        total_views=Sum('properties__views'),
        total_reviews = Sum('properties__reviews')
    ).order_by('full_name')
    return render(request, 'dealers.html', {'dealers': dealers})

def dealer_profile(request, id):
    dealer     = get_object_or_404(Dealer, id=id)
    properties = Property.objects.filter(dealer=dealer).order_by('-created_at')
    reviews    = DealerReview.objects.filter(property__dealer=dealer).order_by('-created_at')
    total_views = properties.aggregate(Sum('views'))['views__sum'] or 0
 
    return render(request, 'dealer_profile.html', {
        'dealer':      dealer,
        'properties':  properties,
        'reviews':     reviews,
        'total_views': total_views,
    })