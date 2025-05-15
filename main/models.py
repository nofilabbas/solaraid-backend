from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Avg
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from PIL import Image
import datetime
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

# Seller model
class Seller(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mobile = models.PositiveBigIntegerField(unique=True, null=True)
    profile_img = models.ImageField(upload_to='seller_imgs/', null=True)
    address = models.TextField(null=True)
    location = models.CharField(max_length=255, null=True, blank=True)  # Add this field
    cnic_number = models.PositiveBigIntegerField(unique=True, null=True)
    cnic_front = models.ImageField(upload_to='seller_imgs/', null=True)
    cnic_back = models.ImageField(upload_to='seller_imgs/', null=True)
    business_doc = models.ImageField(upload_to='seller_imgs/', null=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_img:
            img = Image.open(self.profile_img.path)
            if img.height > 300 or img.width > 300:  # Resize condition
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_img.path)
                
    def __str__(self):
        return self.user.username
    
    #fetch_daily_orders
    @property
    def show_daily_orders_chart(self):
        orders = OrderItem.objects.filter(product__seller=self).values('order__order_time__date').annotate(Count('id'))
        dateList=[]
        countList=[]
        dataSet={}
        if orders:
            for order in orders:
                dateList.append(order['order__order_time__date'])
                countList.append(order['id__count'])
        dataSet={'Dates': dateList,
                 'Data': countList}
        return dataSet
    
    #fetch_monthly_orders
    @property
    def show_monthly_orders_chart(self):
        orders = OrderItem.objects.filter(product__seller=self).values('order__order_time__month').annotate(Count('id'))
        dateList=[]
        countList=[]
        dataSet={}
        if orders:
            for order in orders:
                monthinteger = order['order__order_time__month']
                month = datetime.date(1900, monthinteger, 1).strftime('%B')
                dateList.append(month)
                countList.append(order['id__count'])
        dataSet={'Dates': dateList,
                 'Data': countList}
        return dataSet
    
    #fetch_yearly_orders
    @property
    def show_yearly_orders_chart(self):
        orders = OrderItem.objects.filter(product__seller=self).values('order__order_time__year').annotate(Count('id'))
        dateList=[]
        countList=[]
        dataSet={}
        if orders:
            for order in orders:
                dateList.append(order['order__order_time__year'])
                countList.append(order['id__count'])
        dataSet={'Dates': dateList,
                 'Data': countList}
        return dataSet

# Product Category model
class ProductCategory(models.Model):
    title = models.CharField(max_length=200)
    detail = models.TextField(null=True)
    cat_img = models.ImageField(upload_to='category_imgs/', null=True)

    def __str__(self): 
        return self.title
     
# Product model
class Product(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='category_products')
    seller = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    detail = models.TextField(null=True)
    price = models.FloatField()
    slug = models.SlugField(unique=True, null=True)
    tags = models.TextField( null=True)
    image = models.ImageField(upload_to='product_imgs/', null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path) 
            if img.height > 500 or img.width > 500:  # Resize condition
                output_size = (500, 500)
                img.thumbnail(output_size)
                img.save(self.image.path)
                
    def __str__(self):
        return self.title   
    
    def tag_list(self):
        tagList = self.tags.split(',')
        return tagList
    
    def average_rating(self):
        return self.product_ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    

# Customer model
class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mobile = models.PositiveBigIntegerField(unique=True)
    profile_img = models.ImageField(upload_to='customer_imgs/', null=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_img:
            img = Image.open(self.profile_img.path)
            if img.height > 300 or img.width > 300:  # Resize condition
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_img.path)
                
    def __str__(self):
        return self.user.username
    

# Order model
class Order(models.Model):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'

    ORDER_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_orders')
    order_time = models.DateTimeField(auto_now_add=True)
    order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    received_status = models.BooleanField(default=False)
    order_status = models.CharField(
        max_length=10,  
        choices=ORDER_STATUS_CHOICES,
        default=PENDING,  # Default status can be 'Pending'
    )

    def __str__(self):
        return f"Order {self.id} by {self.customer.user.username}"

    class Meta:
        ordering = ['-order_time']

# Order Item model
class OrderItem(models.Model):
    # Delivery status choices
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivered_at = models.DateTimeField(null=True, blank=True)
    # Delivery status of the item
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='pending'
    )
    
    def __str__(self) -> str:
        return self.product.title


# Customer Address model
class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_addresses')
    address = models.TextField()
    default_address = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.address


# Product Rating and Reviews model
class ProductRating(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='rating_customers')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField()
    add_time = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.rating} - {self.review}'
    
    class Meta:
        ordering = ['-add_time']

# Product Images model
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_imgs')
    image = models.ImageField(upload_to='product_imgs/', null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 500 or img.width > 500:  # Resize condition
                output_size = (500, 500)
                img.thumbnail(output_size)
                img.save(self.image.path)
                
    def __str__(self):
        return self.image.url
    

# Wishlist model
class Wishlist(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.product.title} - {self.customer.user.first_name}'
    
    
    
class Message(models.Model):
    # Sender and receiver will both be dynamic, linking to either Seller or Customer
    sender_type = models.ForeignKey(ContentType,null=True, on_delete=models.CASCADE, related_name='sender_messages')
    sender_id = models.PositiveIntegerField(null=True)
    sender = GenericForeignKey('sender_type', 'sender_id')

    receiver_type = models.ForeignKey(ContentType,null=True, on_delete=models.CASCADE, related_name='receiver_messages')
    receiver_id = models.PositiveIntegerField(null=True)
    receiver = GenericForeignKey('receiver_type', 'receiver_id')

    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} on {self.timestamp}"
    
    

class Interaction(models.Model):
    INTERACTION_CHOICES = [
        ('view', 'View'),
        ('order', 'Order'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.customer.user.username} - {self.interaction_type} - {self.product.title}'
    


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)