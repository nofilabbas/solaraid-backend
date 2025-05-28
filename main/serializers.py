from rest_framework import serializers
from . import models
from django.contrib.auth.models import User

# Seller serializer
class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Seller
        fields = ['id', 'user', 'address', 'profile_img', 'location', 'cnic_number', 'cnic_front', 'cnic_back', 'business_doc']

    def __init__(self, *args, **kwargs):
        super(SellerSerializer, self). __init__(self, *args, **kwargs)
        
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user'] = UserSerializer(instance.user).data
        return response
        

class SellerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Seller
        fields = ['id', 'user', 'mobile', 'profile_img', 'address', 'location', 'show_daily_orders_chart',
                  'show_monthly_orders_chart', 'show_yearly_orders_chart']
        depth = 1  # Define depth directly in Meta

    def __init__(self, *args, **kwargs):
        print("Args:", args)
        print("Kwargs:", kwargs)
        super(SellerDetailSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user'] = UserSerializer(instance.user).data
        return response

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductCategory
        fields = ['id', 'title', 'detail', 'cat_img']

# Product serializer
class ProductListSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=models.ProductCategory.objects.all())
    prod_category = ProductCategorySerializer(source='category', read_only=True)
    seller_loc = SellerSerializer(source='seller', read_only=True)

    seller = serializers.PrimaryKeyRelatedField(queryset=models.Seller.objects.all())
    class Meta:
        model = models.Product
        fields = ['id', 'category', 'prod_category', 'seller_loc', 'seller', 'inventory', 'title', 'slug', 'tag_list', 'detail', 'price', 'product_ratings', 'image', 'tags', 'average_rating']
        depth = 1  # Define depth directly in Meta

    def __init__(self, *args, **kwargs):
        print("Args:", args)
        print("Kwargs:", kwargs)
        super(ProductListSerializer, self).__init__(*args, **kwargs)

    
# New simple serializer for recommended products
class RecommendedProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = models.Product
        fields = ['id', 'title', 'price', 'image', 'average_rating']

    def get_image(self, obj):
        request = self.context.get('request')
        if request:
            absolute_url = request.build_absolute_uri(obj.image.url)
            return absolute_url
        return obj.image.url



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductImage
        fields = ['id', 'product', 'image']


class ProductDetailSerializer(serializers.ModelSerializer):
    product_ratings = serializers.StringRelatedField(many=True, read_only=True)
    product_imgs = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = models.Product
        fields = [
            'id', 'category', 'seller', 'title', 'inventory', 'slug', 'tag_list', 'detail', 'price', 
            'product_ratings', 'product_imgs', 'image', 
            'tags', 'average_rating'
        ]

    def __init__(self, *args, **kwargs):
        print("Args:", args)
        print("Kwargs:", kwargs)
        super(ProductDetailSerializer, self).__init__(*args, **kwargs)

    def get_average_rating(self, obj):
        return round(obj.average_rating(), 1)  # Round to 1 decimal place


# User serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email']
        
        
# Customer serializer
class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Serialize user data but limit the fields
    class Meta:
        model = models.Customer
        fields = ['id', 'user', 'mobile', 'profile_img']

    # def __init__(self, *args, **kwargs):
    #     super(). __init__(self, *args, **kwargs)
    #     self.Meta.depth = 1
    def to_representation(self, instance):
        print(instance)  # Debug the instance
        return super().to_representation(instance)
        

class ProductRatingSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)  # Return full customer details in response
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Customer.objects.all(), write_only=True, source='customer'
    )  # Accept customer ID in requests
    class Meta:
        model = models.ProductRating
        fields = ['id', 'customer', 'customer_id', 'product', 'rating', 'review', 'add_time']
        #depth = 1  # Define depth directly in Meta

    def __init__(self, *args, **kwargs):
        print("Args:", args)
        print("Kwargs:", kwargs)
        super(ProductRatingSerializer, self).__init__(*args, **kwargs)
        
        
class CustomerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = ['id', 'user', 'mobile', 'profile_img', 'customer_orders']
        #depth = 1  # Define depth directly in Meta

    # def __init__(self, *args, **kwargs):
    #     print("Args:", args)
    #     print("Kwargs:", kwargs)
    #     super(CustomerDetailSerializer, self).__init__(*args, **kwargs)
        
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user'] = UserSerializer(instance.user).data
        
        return response



class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomerAddress
        fields = ['id', 'customer', 'address', 'default_address']

    def validate_customer(self, value):
        # Ensure customer exists and is valid
        if not models.Customer.objects.filter(id=value.id).exists():
            raise serializers.ValidationError('Invalid customer ID.')
        return value

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderItem
        fields = ['id', 'order', 'product', 'qty', 'price', 'delivery_status', 'delivered_at']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        
        # Include only necessary fields from the order
        response['order'] = {
            'id': instance.order.id,
            'order_status': instance.order.order_status,
            'order_time': instance.order.order_time,
            'order_amount': instance.order.order_amount,
        }
        
        # Include customer and user details
        response['customer'] = {
            'id': instance.order.customer.id,
            'user': {
                'id': instance.order.customer.user.id,
                'username': instance.order.customer.user.username,
                'email': instance.order.customer.user.email,
            },
            'mobile': instance.order.customer.mobile,
        }
        
        # Include product details
        response['product'] = {
            'id': instance.product.id,
            'title': instance.product.title,
            'price': instance.product.price,
        }
        
        return response
        
# Order serializer
class OrderSerializer(serializers.ModelSerializer):
    order_items = serializers.SerializerMethodField()  # Use a custom method to avoid recursion

    class Meta:
        model = models.Order
        fields = ['id', 'customer', 'order_status', 'order_time', 'order_amount', 'order_items', 'received_status']
        depth = 1

    def get_order_items(self, obj):
        # Return a simplified representation of order items
        return [
            {
                'id': item.id,
                'product': item.product.title,
                'qty': item.qty,
                'price': item.price,
                'delivery_status': item.delivery_status,
                'delivered_at': item.delivered_at,
            }
            for item in obj.order_items.all()
        ]

    def validate_order_status(self, value):
        """Ensure that the order status is valid."""
        if value not in dict(models.Order.ORDER_STATUS_CHOICES):
            raise serializers.ValidationError("Invalid order status.")
        return value

    def create(self, validated_data):
        # Ensure that the customer field is set
        customer_id = self.context['request'].data.get('customer')
        if customer_id:
            customer = models.Customer.objects.get(id=customer_id)
            validated_data['customer'] = customer
        else:
            raise serializers.ValidationError("Customer is required.")
        
        # Use the order_amount provided in the request
        validated_data['order_amount'] = self.context['request'].data.get('totalAmount', 0)
        
        # Log the validated data
        print("Validated data:", validated_data)
        
        return super().create(validated_data)

class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderItem
        fields = ['id', 'order', 'product']
        depth = 1  # Define depth directly in Meta

    def __init__(self, *args, **kwargs):
        print("Args:", args)
        print("Kwargs:", kwargs)
        super(OrderDetailSerializer, self).__init__(*args, **kwargs)


# Category serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductCategory
        fields = ['id', 'title', 'detail', 'cat_img']

    # def __init__(self, *args, **kwargs):
    #     super(CategorySerializer, self). __init__(self, *args, **kwargs)
    #     self.Meta.depth = 1
    def to_representation(self, instance):
        print(instance)  # Debug the instance
        return super().to_representation(instance)
        

class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductCategory
        fields = ['id', 'title', 'detail']
        depth = 1  # Define depth directly in Meta

    def __init__(self, *args, **kwargs):
        print("Args:", args)
        print("Kwargs:", kwargs)
        super(CategoryDetailSerializer, self).__init__(*args, **kwargs)
        
        
# Wishlist serializer
class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Wishlist
        fields = ['id', 'product', 'customer']
        depth = 1  # Set depth directly in the Meta class

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['customer'] = CustomerSerializer(instance.customer).data
        response['product'] = ProductDetailSerializer(instance.product).data
        return response
    
    
    
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Message
        fields = ['sender', 'receiver', 'content', 'timestamp']

    def validate(self, data):
        # Add any custom validation logic here if necessary
        return data