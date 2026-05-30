from django.contrib import admin
from .models import Property, Dealer, PropertyType, Favorite, Features , Inquiry , DealerReview , PropertyImage
# Register your models here.

admin.site.register(Dealer)
admin.site.register(Property)
admin.site.register(PropertyType)
admin.site.register(Favorite)
admin.site.register(Features)
admin.site.register(Inquiry)
admin.site.register(DealerReview)
admin.site.register(PropertyImage)