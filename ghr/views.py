from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Sum
from .models import Property, Dealer, PropertyImage, Features, PropertyType, DealerReview, Inquiry,Favorite

# Create your views here.


def SignUp(request):
    if request.method == "POST":
        request.session['last_form'] = 'signup'
        uname = request.POST.get("uname", '').strip()
        email = request.POST.get("email", '').strip()
        phone = request.POST.get("phone", '').strip()
        password = request.POST.get("password", '')
        cpassword = request.POST.get("cpassword", '')

        if len(uname) < 6:
            messages.error(request, "Username must be atleast 6 characters")
            return redirect('home')
        
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect('home')

        if password != cpassword:
            messages.error(request, "Password Doesn't match")
            return redirect("home")

        if User.objects.filter(username=uname).exists():
            messages.error(request, "Username already exists")
            return redirect("home")
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('home')

        user = User.objects.create_user(username=uname, email=email, password=password)
        user.save()
        messages.success(request, "Account created succesfully")
        return redirect("home")
    return redirect("home")


def SignIn(request):
    if request.method == "POST":
        request.session['last_form'] = 'login'
        uname = request.POST.get("uname")
        password = request.POST.get("password")

        user = authenticate(request, username=uname, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You're Login Successfully")
            return redirect("home")
        else:
            messages.error(request, "Invalid Username or password")
            return redirect("home")

    return redirect("home")


def logout_user(request):
    logout(request)
    messages.success(request, "You're Logged out")
    return redirect("home")


def home(request):
    # is_dealer = False
    # if request.user.is_authenticated:
    #     is_dealer = request.user.dealer_set.exists()

    properties = Property.objects.filter(is_featured="True").order_by("-created_at")
    return render(request, "home.html", {"prop": properties})


def listings(request):
    properties = Property.objects.filter().order_by("-created_at")

    keyword = request.GET.get("keyword")
    if keyword:
        properties = properties.filter(title__icontains=keyword)

    property_type = request.GET.get("property_type")
    if property_type:
        properties = properties.filter(property_type__name=property_type)

    purpose = request.GET.get("purpose")
    if purpose:
        properties = properties.filter(purpose=purpose)

    sort = request.GET.get("sort")
    if sort == "latest":
        properties = properties.order_by("-created_at")
    if sort == "low":
        properties = properties.order_by("price")
    if sort == "high":
        properties = properties.order_by("-price")

    city = request.GET.get("city")
    if city:
        properties = properties.filter(city__iexact=city)

    bedrooms = request.GET.get("bedrooms")
    if bedrooms:
        properties = properties.filter(bedrooms__gte=bedrooms)

    if request.user.is_authenticated:
        favourite_ids = list(Favorite.objects.filter(user=request.user).values_list('property_id', flat=True))
    else:
        favourite_ids = []

    paginator = Paginator(properties, 12)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(request, "listings.html", {"prop": page_obj,'favourite_ids':favourite_ids})


def property_detail(request, slug):
    property = Property.objects.get(slug=slug)
    dealer = property.dealer

    reviews = DealerReview.objects.filter(property=property)

    property.views += 1
    property.save()

    if request.method == "POST" and "send_review" in request.POST:

        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        DealerReview.objects.create(property=property, user=request.user, rating=rating, comment = comment)
        return redirect('property_detail', slug=slug)
    
    if request.method == "POST" and "send_inquiry" in request.POST:
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        Inquiry.objects.create(property=property, name=name, email=email, phone=phone, message=message)
        messages.success(request,'Inquiry send successfully')
        return redirect('property_detail', slug=slug)
    
    is_favourite = False
    
    if request.user.is_authenticated:
        is_favourite = Favorite.objects.filter(user = request.user, property=property).exists()


    return render(request, "property_detail.html", {"prop": property, 'dealer':dealer, 'reviews': reviews, 'is_favourite':is_favourite})


def house(request):
    properties = Property.objects.filter(property_type__name="House").order_by(
        "-created_at"
    )

    paginator = Paginator(properties, 9)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)
    return render(request, "house.html", {"prop": page_obj})

def about(request):
    return render(request, 'about.html')


@login_required
def dealer_register(request):
    if Dealer.objects.filter(user=request.user).exists():
        return redirect("dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        cnic = request.POST.get("cnic",'').strip()
        address = request.POST.get("address")
        gender = request.POST.get("gender")
        phone = request.POST.get("phone")
        picture = request.FILES.get("picture")

        import re
        cnic_pattern = r'^\d{5}-\d{7}-\d{1}$'
        if not re.match(cnic_pattern, cnic):
            messages.error(request, "Invalid CNIC format. Use: 35202-1234567-1")
            return redirect('dealer_register')

        # ── Unique CNIC ──
        if Dealer.objects.filter(cnic=cnic).exists():
            messages.error(request, "A dealer account with this CNIC already exists.")
            return redirect('dealer_register')

        # ── One dealer per user ──
        if Dealer.objects.filter(user=request.user).exists():
            messages.error(request, "You already have a dealer account.")
            return redirect('dashboard')

        Dealer.objects.create(
            user=request.user,
            full_name=name,
            cnic=cnic,
            address=address,
            gender=gender,
            phone=phone,
            profile_picture=picture,
        )
        return redirect("dashboard")
    return render(request, "dealer_register.html")


@login_required
def dashboard(request):
    dealer = Dealer.objects.get(user=request.user)
    properties = Property.objects.filter(dealer=dealer)
    inquiries = Inquiry.objects.filter(property__in=properties)

    total_inquiries = inquiries.count()
    total_views = properties.aggregate(Sum('views'))['views__sum'] or 0

    return render(request, "dashboard.html", {"dealer": dealer, "prop": properties, 'views': total_views, 'inquiries': inquiries, 'inquiries_total':total_inquiries,})


@login_required
def add_property(request):
    dealer = Dealer.objects.get(user=request.user)
    if request.method == "POST":
        title = request.POST.get("title")
        price = request.POST.get("price")
        description = request.POST.get("description")
        property_type_id = request.POST.get("property_type")
        purpose = request.POST.get("purpose")
        city = request.POST.get("city")
        area = request.POST.get("area")
        address = request.POST.get("address")
        bedrooms = request.POST.get("bedrooms")
        bathrooms = request.POST.get("bathrooms")
        kitchens = request.POST.get("kitchens")
        garages = request.POST.get("garages")
        property_size = request.POST.get("property_size")
        furnishing = request.POST.get("furnishing")
        year_built = request.POST.get("year_built")
        featured_image = request.FILES.get("featured_image")
        property_type = PropertyType.objects.get(id=property_type_id)

        property = Property.objects.create(
            dealer=dealer,
            title=title,
            price=price,
            property_type=property_type,
            purpose=purpose,
            city=city,
            area=area,
            description=description,
            address=address,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            kitchens=kitchens,
            garages=garages,
            property_size=property_size,
            furnishing=furnishing,
            year_built=year_built,
            featured_image=featured_image,
        )

        features_id = request.POST.getlist("features")
        property.features.set(features_id)

        images = request.FILES.getlist("images")
        for img in images:
            PropertyImage.objects.create(property=property, image=img)

        messages.success(request, "Property added successfully")
        return redirect("dashboard")

    property_types = PropertyType.objects.all()
    features = Features.objects.all()

    return render(
        request,
        "add_property.html",
        {
            "propertytype": property_types,
            "features": features,
            "dealer": dealer,
        },
    )


@login_required
def my_listings(request):

    dealer = Dealer.objects.get(user=request.user)
    properties = Property.objects.filter(dealer=dealer).order_by("-created_at")

    return render(request, "my_listings.html", {"prop": properties, "dealer": dealer})


@login_required
def edit_property(request, slug):

    dealer = Dealer.objects.get(user=request.user)
    property = Property.objects.get(slug=slug, dealer=dealer)

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

        messages.success(request, "Property updated Soccesfully")
        return redirect("my_listings")

    property_type = PropertyType.objects.all()
    features = Features.objects.all()

    return render(
        request,
        "edit_property.html",
        {
            "prop": property,
            "prop_types": property_type,
            "features": features,
            "dealer": dealer,
        },
    )


@login_required
def dealer_inquiries(request):
    dealer = Dealer.objects.get(user =request.user)
    inquiries = Inquiry.objects.filter(property__dealer = dealer).order_by('-created_at')

    return render(request, 'dealer_inquiries.html', {'inquiries':inquiries, 'dealer':dealer})


@login_required
def dealer_reviews(request):
    dealer = Dealer.objects.get(user = request.user)
    reviews = DealerReview.objects.filter(property__dealer=dealer).order_by('-created_at')

    return render(request, 'dealer_reviews.html', {'dealer':dealer, 'reviews':reviews})

@login_required
def add_favourite(request, slug):
    property = Property.objects.get(slug=slug)
    favourite = Favorite.objects.filter(user=request.user, property=property)

    if favourite.exists():
        favourite.delete()
    else:
        Favorite.objects.create(user=request.user, property=property)
    
    return redirect('property_detail', slug=slug)

@login_required
def favourites(request):
    
    favourite = Favorite.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'favourites.html', {'favourite':favourite})


@login_required
def delete_property(request, slug):
    dealer = Dealer.objects.get(user=request.user)
    property = Property.objects.get(slug=slug, dealer = dealer)
    property.delete()
    messages.success(request, 'deleted succesfully')
    return redirect('dashboard')