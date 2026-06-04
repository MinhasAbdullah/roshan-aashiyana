from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# Create your models here.
class Dealer(models.Model):
    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
        ("prefer not to say", "Prefer not to say"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="dealer")
    full_name = models.CharField(max_length=200)
    cnic = models.CharField(max_length=15, unique=True)
    address = models.TextField(blank=True, default='')
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20, blank=True, default='')
    profile_picture = models.ImageField(max_length=500, blank=True, default='')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # New fields
    description = models.TextField(blank=True, default='')
    whatsapp = models.CharField(max_length=20, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    social_facebook = models.CharField(max_length=200, blank=True, default='')
    social_instagram = models.CharField(max_length=200, blank=True, default='')
    social_linkedin = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return self.full_name


class PropertyType(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Features(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Property(models.Model):

    PURPOSE_CHOICES = (
        ("sale", "For Sale"),
        ("rent", "For Rent"),
    )

    FURNISHING_CHOICES = (
        ("furnished", "Furnished"),
        ("semi_furnished", "Semi Furnished"),
        ("unfurnished", "Unfurnished"),
    )

    dealer = models.ForeignKey(
        Dealer, on_delete=models.CASCADE, related_name="properties"
    )

    property_type = models.ForeignKey(
        PropertyType, on_delete=models.SET_NULL, null=True
    )

    title = models.CharField(max_length=255)

    slug = models.SlugField(unique=True, blank=True)

    description = models.TextField()

    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)

    price = models.PositiveBigIntegerField()

    city = models.CharField(max_length=100)

    area = models.CharField(max_length=100)

    address = models.TextField()

    bedrooms = models.PositiveIntegerField(default=0)

    bathrooms = models.PositiveIntegerField(default=0)

    kitchens = models.PositiveIntegerField(default=1)

    garages = models.PositiveIntegerField(default=0)

    property_size = models.CharField(
        max_length=100, help_text="Example: 10 Marla, 5 Kanal, 1200 sqft"
    )

    furnishing = models.CharField(
        max_length=20, choices=FURNISHING_CHOICES, blank=True, null=True
    )

    year_built = models.PositiveIntegerField(blank=True, null=True)

    featured_image = models.ImageField(upload_to="properties/")

    features = models.ManyToManyField(Features, blank=True)

    is_featured = models.BooleanField(default=False)

    is_available = models.BooleanField(default=True)

    views = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Property.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
    
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PropertyImage(models.Model):

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="images"
    )

    image = models.ImageField(upload_to="property_images/")

    def __str__(self):

        return self.property.title


class Favorite(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    property = models.ForeignKey(Property, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "property")

    def __str__(self):

        return f"{self.user.username} - {self.property.title}"


class DealerReview(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)

    user = models.ForeignKey(User, models.CASCADE)

    rating = models.PositiveIntegerField(default=5)

    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return f"{self.user.username} review"


class Inquiry(models.Model):

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')

    name = models.CharField(max_length=200)

    email = models.EmailField()

    phone = models.CharField(max_length=20)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return self.name
    

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=100)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
