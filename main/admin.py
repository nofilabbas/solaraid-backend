from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Seller)
admin.site.register(models.ProductCategory)
admin.site.register(models.CustomerAddress)
admin.site.register(models.ProductRating)
admin.site.register(models.ProductImage)
admin.site.register(models.Message)
admin.site.register(models.Interaction)

class CustomerAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'mobile']
    def get_username(self, obj):
        return obj.user.username

admin.site.register(models.Customer, CustomerAdmin)

class ProductImagesInLine(admin.StackedInline):
    model = models.ProductImage

class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'seller']
    prepopulated_fields = {'slug':('title',)}
    inlines = [
        ProductImagesInLine,
    ]

admin.site.register(models.Product,ProductAdmin)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'order_time', 'order_status']
admin.site.register(models.Order,OrderAdmin)


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'order']
admin.site.register(models.OrderItem,OrderItemAdmin)

class WIshlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'customer']
admin.site.register(models.Wishlist,WIshlistAdmin)
