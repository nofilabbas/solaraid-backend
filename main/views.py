from django.utils import timezone
from django.http import JsonResponse
from rest_framework import generics,permissions, viewsets
from . import serializers
from . import models
from django.db import IntegrityError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view , action
from rest_framework.response import Response
from rest_framework import status
import google.generativeai as genai
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import stripe, math, json, joblib, os
from django.db import IntegrityError, transaction
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, When
from .models import PasswordResetToken
import numpy as np
import pandas as pd

# Create your views here.

#Seller
class SellerList(generics.ListCreateAPIView):
    queryset = models.Seller.objects.all()
    serializer_class = serializers.SellerSerializer

    def get_queryset(self):
        queryset = models.Seller.objects.all().order_by('id')
        
        # Apply fetch_limit if provided in request
        fetch_limit = self.request.query_params.get('fetch_limit')
        if fetch_limit is not None:
            try:
                limit = int(fetch_limit)
                queryset = queryset[:limit]
            except ValueError:
                pass  # Ignore invalid values
        
        return queryset


class SellerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Seller.objects.all()
    serializer_class = serializers.SellerDetailSerializer
    
    
class SellerProductList(generics.ListAPIView):
    serializer_class = serializers.ProductListSerializer
    
    def get_queryset(self):
        seller_id = self.kwargs['seller_id']
        return models.Product.objects.filter(seller_id=seller_id).order_by('id')  # ✅ Use correct field name

    
class SellerOrderItemList(generics.ListAPIView):
    queryset = models.OrderItem.objects.all()
    serializer_class = serializers.OrderItemSerializer
    
    def get_queryset(self):
       qs = super().get_queryset()
       seller_id = self.kwargs['pk']
       qs = qs.filter(product__seller__id=seller_id)
       return qs
   
class SellerCustomerList(generics.ListAPIView):
    serializer_class = serializers.CustomerSerializer

    def get_queryset(self):
        seller_id = self.kwargs['pk']
        return models.Customer.objects.filter(
            customer_orders__order_items__product__seller__id=seller_id
        ).distinct()
   
class SellerCustomerOrderItemList(generics.ListAPIView):
    queryset = models.OrderItem.objects.all()
    serializer_class = serializers.OrderItemSerializer
    
    def get_queryset(self):
       qs = super().get_queryset()
       seller_id = self.kwargs['seller_id']
       customer_id = self.kwargs['customer_id']
       qs = qs.filter(order__customer__id=customer_id, product__seller__id=seller_id)
       return qs

@csrf_exempt
def seller_register(request):
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    username = request.POST.get('username')
    email = request.POST.get('email')
    mobile = request.POST.get('mobile')
    address = request.POST.get('address')
    password = request.POST.get('password')
    location = request.POST.get('location')
    cnic_number = request.POST.get('cnic_number')
    cnic_front = request.FILES.get('cnic_front')
    cnic_back = request.FILES.get('cnic_back')
    business_doc = request.FILES.get('business_doc')

    # Validate password
    try:
        validate_password(password)
    except ValidationError as e:
        return JsonResponse({
            'bool': False,
            'msg': ' '.join(e.messages)  # Combine all error messages into a single string
        })

    try:
        with transaction.atomic():
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email
            )
            user.set_password(password)  # Properly hash the password
            user.save()
            try:
                # Create seller
                seller = models.Seller.objects.create(
                    user=user,
                    mobile=mobile,
                    address=address,
                    location=location,
                    cnic_number=cnic_number,
                    cnic_front=cnic_front,
                    cnic_back=cnic_back,
                    business_doc=business_doc,
                )
                msg = {
                    'bool': True,
                    'user': user.id,
                    'seller': seller.id,
                    'msg': 'Thank you for registering. You can login now.'
                }
            except IntegrityError:
                msg = {
                    'bool': False,
                    'msg': 'Mobile already exists!'
                }
    except IntegrityError:
        msg = {
            'bool': False,
            'msg': 'Username already exists!'
        }
    return JsonResponse(msg)

@csrf_exempt
def seller_login(request):
    username = request.POST.get('username')    
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user:
        seller = models.Seller.objects.get(user=user)
        msg={
            'bool': True,
            'user': user.username,
            'id': seller.id,
        }
    else:
        msg={
            'bool': False,
            'msg': 'Invalid usesrname or password'
        }
    return JsonResponse(msg)


@csrf_exempt
def seller_change_password (request, seller_id):
    password = request.POST.get('password')
    seller = models.Seller.objects.get(id=seller_id) 
    user = seller.user
    user.password = make_password(password)
    user.save()
    msg={'bool': True, 'msg': 'Password has been changed'}
    return JsonResponse(msg)


#Products
class ProductList(generics.ListCreateAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductListSerializer

    def get_queryset(self):
        category_id = self.request.query_params.get('category')  # Use .get() instead of calling the QueryDict
        page = self.request.query_params.get('page', 1)  # Default page to 1 if not provided
        queryset = models.Product.objects.all().order_by('id')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if 'fetch_limit' in self.request.GET:
            limit = int(self.request.GET['fetch_limit'])
            queryset=queryset[:limit]
        return queryset
    
class ProductImgList(generics.ListCreateAPIView):
    queryset = models.ProductImage.objects.all()
    serializer_class = serializers.ProductImageSerializer
    
class ProductImgsDetail(generics.ListCreateAPIView):
    queryset = models.ProductImage.objects.all()
    serializer_class = serializers.ProductImageSerializer
    
    def get_queryset(self):
       qs = super().get_queryset()
       product_id = self.kwargs['product_id']
       qs = qs.filter(product__id=product_id)
       return qs

#for deleting one image from product images
class ProductImgDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.ProductImage.objects.all()
    serializer_class = serializers.ProductImageSerializer
    
class TagProductList(generics.ListCreateAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductListSerializer

    def get_queryset(self):
       qs = super().get_queryset()
       tag = self.kwargs['tag']
       qs = qs.filter(tags__icontains=tag)
       return qs
    
class RelatedProductList(generics.ListCreateAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductListSerializer

    def get_queryset(self):
       qs = super().get_queryset()
       product_id = self.kwargs['pk']
       product = models.Product.objects.get(id=product_id)
       qs = qs.filter(category=product.category).exclude(id=product_id)
       return qs


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductDetailSerializer

class ProductRatingViewSet(viewsets.ModelViewSet):
    queryset = models.ProductRating.objects.all().select_related('customer') 
    serializer_class = serializers.ProductRatingSerializer
    
    
    def create(self, request, *args, **kwargs):
        print("Received Data:", request.data)  # Log the request data
        return super().create(request, *args, **kwargs)
    
    # Custom action to get reviews for a specific product
    @action(detail=True, methods=['get'])
    def product_reviews(self, request, product_id=None):
        product = get_object_or_404(models.Product, id=product_id)
        reviews = models.ProductRating.objects.filter(product=product).order_by('-add_time')
        serializer = self.get_serializer(reviews, many=True)

        # Calculate average rating
        total_reviews = reviews.count()
        avg_rating = round(sum([r.rating for r in reviews]) / total_reviews, 1) if total_reviews > 0 else 0

        return Response({
            "average_rating": avg_rating,
            "total_reviews": total_reviews,
            "reviews": serializer.data
        })

class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer

#Customers
class CustomerList(generics.ListCreateAPIView):
    queryset = models.Customer.objects.all()
    serializer_class = serializers.CustomerSerializer

class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Customer.objects.all()
    serializer_class = serializers.CustomerDetailSerializer

@csrf_exempt
def customer_login(request):
    username = request.POST.get('username')    
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user:
        customer = models.Customer.objects.get(user=user)
        msg={
            'bool': True,
            'user': user.username,
            'id': customer.id,
        }
    else:
        msg={
            'bool': False,
            'msg': 'Invalid usesrname or password'
        }
    return JsonResponse(msg)

@csrf_exempt
def customer_register(request):
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    username = request.POST.get('username')
    email = request.POST.get('email')
    mobile = request.POST.get('mobile')
    password = request.POST.get('password')

    # Validate password
    try:
        validate_password(password)
    except ValidationError as e:
        return JsonResponse({
            'bool': False,
            'msg': ' '.join(e.messages)  # Combine all error messages into a single string
        })

    try:
        with transaction.atomic():
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email
            )
            user.set_password(password)  # Properly hash the password
            user.save()
            try:
                # Create customer
                customer = models.Customer.objects.create(
                    user=user,
                    mobile=mobile
                )
                msg = {
                    'bool': True,
                    'user': user.id,
                    'customer': customer.id,
                    'msg': 'Thank you for registering. You can login now.'
                }
            except IntegrityError:
                msg = {
                    'bool': False,
                    'msg': 'Mobile already exists!'
                }
    except IntegrityError:
        msg = {
            'bool': False,
            'msg': 'Username already exists!'
        }
    return JsonResponse(msg)


@csrf_exempt
def customer_change_password (request, customer_id):
    password = request.POST.get('password')
    customer = models.Customer.objects.get(id=customer_id) 
    user = customer.user
    user.password = make_password(password)
    user.save()
    msg={'bool': True, 'msg': 'Password has been changed'}
    return JsonResponse(msg)


stripe.api_key = settings.STRIPE_SECRET_KEY
class StripeCheckoutView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            cart_data = request.data.get('cartData')
            order_id = request.data.get('order_id')

            # Log incoming request data
            print(f"Received cart_data: {cart_data}")
            print(f"Received order_id: {order_id}")

            if not cart_data:
                return Response({'error': 'Cart data is empty or missing'}, status=status.HTTP_400_BAD_REQUEST)

            # Convert cart data to line items for Stripe
            line_items = [
            {
                'price_data': {
                    'currency': 'pkr',
                    'product_data': {
                        'name': item['product']['title'],
                        'images': [item['product']['image']],
                    },
                    'unit_amount': int(item['product']['price'] * 100),  # Convert to cents
                },
                'quantity': 1,
            }
            for item in cart_data
        ]
            
            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=settings.SITE_URL + '/payment/success?success=true&session_id={CHECKOUT_SESSION_ID}',
                #success_url=settings.SITE_URL + '/payment/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_URL + '/payment/cancel',
                 metadata={
                    'order_id': str(order_id),  # Pass the related order ID
                },
            )

            return Response({'url': checkout_session.url}, status=status.HTTP_200_OK)


           
        except Exception as e:
            print(f"Error in StripeCheckoutView: {str(e)}")  # Logs the error
            return Response(
                {'error': 'Something went wrong when creating Stripe checkout session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])  # Ensure it's a GET request
def verify_payment_session(request, session_id):
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            return Response({'status': 'success', 'session': session}, status=200)
        else:
            return Response({'status': 'failed', 'session': session}, status=400)
    except stripe.error.StripeError as e:
        return Response({'error': str(e)}, status=500)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
    

@api_view(['POST'])
def update_order_status(request):
    """
    Update the order status to 'completed' after payment is successful or 'processing' for COD.
    """
    session_id = request.data.get('session_id')
    order_id = request.data.get('order_id')  # For COD, you will pass the order_id directly
    payment_method = request.data.get('payment_method')  # Either 'stripe' or 'cod'

    try:
        from .models import Order
        
        # If the payment method is Stripe, check the payment status
        if payment_method == 'stripe':
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == 'paid':
                # Update the order status to completed
                try:
                    order = Order.objects.get(id=order_id)
                    order.order_status = "completed"  # Update to completed after payment
                    order.save()
                    return Response({'message': 'Order status updated to completed'}, status=status.HTTP_200_OK)
                except Order.DoesNotExist:
                    return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'error': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # If the payment method is COD, update the status to processing
        elif payment_method == 'cod':
            try:
                order = Order.objects.get(id=order_id)
                order.order_status = "processing"  # Update to processing for COD
                order.save()
                return Response({'message': 'Order status updated to processing'}, status=status.HTTP_200_OK)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        else:
            return Response({'error': 'Invalid payment method'}, status=status.HTTP_400_BAD_REQUEST)
    
    except stripe.error.StripeError as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class CustomerAddressViewSet(viewsets.ModelViewSet):
    queryset = models.CustomerAddress.objects.all()
    serializer_class = serializers.CustomerAddressSerializer

    def create(self, request, *args, **kwargs):
        customer_id = request.data.get('customer')
        if not customer_id:
            return Response({'error': 'Customer ID is required'}, status=400)
        return super().create(request, *args, **kwargs)

#Order
class OrderList(generics.ListCreateAPIView):
    queryset = models.Order.objects.all()
    serializer_class = serializers.OrderSerializer


class OrderItemList(generics.ListCreateAPIView):
    queryset = models.OrderItem.objects.all()
    serializer_class = serializers.OrderItemSerializer
    
class MarkAsDeliveredView(APIView):
    def post(self, request, order_item_id):
        try:
            order_item = models.OrderItem.objects.get(id=order_item_id)
            order_item.delivery_status = 'delivered'
            order_item.delivered_at = timezone.now()
            order_item.save()
            return Response({"message": "Item marked as delivered"}, status=status.HTTP_200_OK)
        except models.OrderItem.DoesNotExist:
            return Response({"error": "Order item not found"}, status=status.HTTP_404_NOT_FOUND)
     
class MarkAsReceivedView(APIView):
    def post(self, request, order_id):
        try:
            order = models.Order.objects.get(id=order_id)
            
            # Check if all items are delivered
            undelivered_items = models.OrderItem.objects.filter(order=order, delivery_status='pending')
            if undelivered_items.exists():
                return Response({"error": "All items must be delivered before marking as received"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark the order as received
            order.received_status = True
            order.save()
            
            # If all items are delivered, allow the buyer to mark the order as received
            return Response({"message": "Order marked as received"}, status=status.HTTP_200_OK)
        except models.Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
class OrderDelete(generics.RetrieveDestroyAPIView):
    queryset = models.Order.objects.all()
    serializer_class = serializers.OrderDetailSerializer
    

class OrderModify(generics.RetrieveUpdateAPIView):
    queryset = models.Order.objects.all()
    serializer_class = serializers.OrderSerializer
    
class CustomerOrderList(generics.ListAPIView):
    queryset = models.Order.objects.all()
    serializer_class = serializers.OrderSerializer
    
    def get_queryset(self):
       qs = super().get_queryset()
       customer_id = self.kwargs['pk']
       qs = qs.filter(customer__id=customer_id)
       
       ordering = self.request.query_params.get('ordering', None)
       if ordering:
            qs = qs.order_by(ordering)
       return qs
   
   
class CustomerOrderItemList(generics.ListAPIView):
    serializer_class = serializers.OrderItemSerializer

    def get_queryset(self):
        customer_id = self.kwargs['pk']
        order_id = self.request.query_params.get('order', None)
        
        # Filter by customer and order
        qs = models.OrderItem.objects.filter(order__customer_id=customer_id)
        if order_id:
            qs = qs.filter(order__id=order_id)
        
        # Add sorting based on query parameter
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            qs = qs.order_by(ordering)
        
        return qs
    
class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.OrderItem.objects.all()
    serializer_class = serializers.OrderDetailSerializer
    
    def get_queryset(self):
        order_id = self.kwargs['pk']
        order = models.Order.objects.get(id=order_id)
        order_items = models.OrderItem.objects.filter(order=order)
        return order_items


#Category
class CategoryList(generics.ListCreateAPIView):
    queryset = models.ProductCategory.objects.all()
    serializer_class = serializers.CategorySerializer

class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.ProductCategory.objects.all()
    serializer_class = serializers.CategoryDetailSerializer
    
#Wishlist
class WishList(generics.ListCreateAPIView):
    queryset = models.Wishlist.objects.all()
    serializer_class = serializers.WishlistSerializer

    def perform_create(self, serializer):
        # Get the customer and product from the request data
        customer_id = self.request.data.get('customer')
        product_id = self.request.data.get('product')

        if not customer_id or not product_id:
            raise ValueError("Customer and Product IDs are required.")

        # Create the wishlist item with the customer and product
        serializer.save(customer_id=customer_id, product_id=product_id)

    def create(self, request, *args, **kwargs):
        try:
            # Call the parent class to handle serializer validation
            return super().create(request, *args, **kwargs)
        except ValueError as e:
            # Return an error response if customer or product is missing
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        

@csrf_exempt
def check_in_wishlist(request):
    if request.method == 'POST':
        product_id=request. POST.get('product')
        customer_id=request.POST.get('customer')
        checkWishlist=models.Wishlist.objects.filter(product__id=product_id, customer__id=customer_id).count()
        msg={
            'bool': False
        }
        if checkWishlist > 0:
            msg={
                'bool': True,
            }
    return JsonResponse(msg)


@csrf_exempt
def delete_customer_orders(request, customer_id):
    if request.method == 'DELETE':
        orders = models.Order.objects.filter(customer__id=customer_id).delete()
        msg={
            'bool': False
        }
        if orders:
            msg={
                'bool': True,
            }
    return JsonResponse(msg)

class CustomerWishItemList(generics.ListAPIView):
    queryset = models.Wishlist.objects.all()
    serializer_class = serializers.WishlistSerializer
    
    def get_queryset(self):
       qs = super().get_queryset()
       customer_id = self.kwargs['pk']
       qs = qs.filter(customer__id=customer_id)
       return qs
    

@csrf_exempt
def remove_from_wishlist(request):
    if request.method == 'POST':
        wishlist_id=request. POST.get('wishlist_id')
        res=models.Wishlist.objects.filter(id=wishlist_id).delete()
        msg={
            'bool': False
        }
        if res:
            msg={
                'bool': True,
            }
    return JsonResponse(msg)

class CustomerAddressList(generics.ListAPIView):
    queryset = models.CustomerAddress.objects.all()
    serializer_class = serializers.CustomerAddressSerializer
    
    def get_queryset(self):
       qs = super().get_queryset()
       customer_id = self.kwargs['pk']
       qs = qs.filter(customer__id=customer_id)
       return qs
    
@csrf_exempt
def mark_default_address(request, pk):
    if request.method == 'POST':
        address_id=request. POST.get('address_id')
        models.CustomerAddress.objects.update(default_address=False)
        res=models.CustomerAddress.objects.filter(id=address_id).update(default_address=True)
        msg={
            'bool': False
        }
        if res:
            msg={
                'bool': True,
            }
    return JsonResponse(msg)


def customer_dashboard (request,pk):
    customer_id = pk
    try:
        customer = models.Customer.objects.get(id=customer_id)
        customer_name = customer.user.get_full_name() or customer.user.username
    except models.Seller.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=404)
    
    totalOrders = models. Order.objects.filter(customer_id=customer_id).count()
    totalWishList = models.Wishlist.objects.filter (customer_id=customer_id).count()
    totalAddress = models.CustomerAddress.objects.filter(customer_id=customer_id).count()
    msg={
        'customerName': customer_name,
        'totalOrders': totalOrders,
        'totalWishList': totalWishList,
        'totalAddress': totalAddress,
    }
    return JsonResponse(msg)

def seller_dashboard (request,pk):
    seller_id = pk
    try:
        seller = models.Seller.objects.get(id=seller_id)
        seller_name = seller.user.get_full_name() or seller.user.username
    except models.Seller.DoesNotExist:
        return JsonResponse({'error': 'Seller not found'}, status=404)
    
    totalProducts = models.Product.objects.filter (seller_id=seller_id).count()
    totalOrders = models. OrderItem.objects.filter(product__seller__id=seller_id).count()
    totalCustomers = models.OrderItem.objects.filter(product__seller__id=seller_id).values('order__customer').distinct().count()
    msg={
        'sellerName': seller_name,
        'totalProducts': totalProducts,
        'totalOrders': totalOrders,
        'totalCustomers': totalCustomers,
    }
    return JsonResponse(msg)



# Set up your Gemini API key
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

@csrf_exempt
def chat_with_gemini(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            if not user_message:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)

            # Load the Gemini model
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(user_message)

            return JsonResponse({"reply": response.text})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)



class SendMessageView(APIView):
    def post(self, request, *args, **kwargs):
        sender_id = request.data.get("sender_id")
        receiver_id = request.data.get("receiver_id")
        content = request.data.get("content")

        # Determine whether the sender is a Seller or Customer
        sender = None
        receiver = None
        
        if request.data.get("sender_type") == "seller":
            sender = models.Seller.objects.get(id=sender_id)
            sender_type = ContentType.objects.get_for_model(models.Seller)
        elif request.data.get("sender_type") == "customer":
            sender = models.Customer.objects.get(id=sender_id)
            sender_type = ContentType.objects.get_for_model(models.Customer)
        
        if request.data.get("receiver_type") == "seller":
            receiver = models.Seller.objects.get(id=receiver_id)
            receiver_type = ContentType.objects.get_for_model(models.Seller)
        elif request.data.get("receiver_type") == "customer":
            receiver = models.Customer.objects.get(id=receiver_id)
            receiver_type = ContentType.objects.get_for_model(models.Customer)

        # Create the message object
        message = models.Message(
            sender_type=sender_type,
            sender_id=sender.id,
            receiver_type=receiver_type,
            receiver_id=receiver.id,
            content=content
        )
        message.save()

        return Response({"message": "Message sent successfully!"}, status=200)
    
    
class GetChatMessagesView(APIView):
    def get(self, request, seller_id, customer_id, *args, **kwargs):
        seller_ct = ContentType.objects.get_for_model(models.Seller)
        customer_ct = ContentType.objects.get_for_model(models.Customer)

        messages = models.Message.objects.filter(
            sender_type=seller_ct,
            sender_id=seller_id,
            receiver_type=customer_ct,
            receiver_id=customer_id
        )

        messages = messages | models.Message.objects.filter(
            sender_type=customer_ct,
            sender_id=customer_id,
            receiver_type=seller_ct,
            receiver_id=seller_id
        )

        messages = messages.order_by('timestamp')

        # Serialize messages
        message_data = [
            {
                "sender": str(message.sender),
                "receiver": str(message.receiver),
                "content": message.content,
                "timestamp": message.timestamp,
            }
            for message in messages
        ]

        return Response({"messages": message_data}, status=status.HTTP_200_OK)




class SellerChatsView(APIView):
    def get(self, request, seller_id, *args, **kwargs):
        seller_type = ContentType.objects.get_for_model(models.Seller)
        customer_type = ContentType.objects.get_for_model(models.Customer)

        # Get all distinct customer IDs who sent or received messages with this seller
        sent_customers = models.Message.objects.filter(
            sender_type=seller_type, sender_id=seller_id,
            receiver_type=customer_type
        ).values_list('receiver_id', flat=True)

        received_customers = models.Message.objects.filter(
            receiver_type=seller_type, receiver_id=seller_id,
            sender_type=customer_type
        ).values_list('sender_id', flat=True)

        customer_ids = set(sent_customers).union(received_customers)
        customers = models.Customer.objects.filter(id__in=customer_ids).select_related('user')

        data = [
            {
                "id": customer.id,
                "username": customer.user.username,
                "profile_img": customer.profile_img.url if customer.profile_img else None
            }
            for customer in customers
        ]

        return Response({"customers": data}, status=status.HTTP_200_OK)


class CustomerChatsView(APIView):
    def get(self, request, customer_id, *args, **kwargs):
        # Get all sellers the customer has chatted with
        messages = models.Message.objects.filter(
            receiver_type=ContentType.objects.get_for_model(models.Customer),
            receiver_id=customer_id
        ).distinct('sender_id')  # Unique chats with sellers

        # Prepare chat list for the customer
        sellers = []
        for message in messages:
            seller = models.Seller.objects.get(id=message.sender_id)
            sellers.append({
                "id": seller.id,
                "username": seller.user.username,
                "profile_img": seller.profile_img.url if seller.profile_img else '',  # Add default if needed
            })

        return Response({"sellers": sellers}, status=status.HTTP_200_OK)
       
    

@csrf_exempt
def record_interaction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        product_id = data.get('product_id')
        interaction_type = data.get('interaction_type')

        if not all([customer_id, product_id, interaction_type]):
            return JsonResponse({'error': 'Missing fields'}, status=400)

        try:
            customer = models.Customer.objects.get(id=customer_id)
            product = models.Product.objects.get(id=product_id)
        except (models.Customer.DoesNotExist, models.Product.DoesNotExist):
            return JsonResponse({'error': 'Customer or Product not found'}, status=404)

        models.Interaction.objects.create(
            customer=customer,
            product=product,
            interaction_type=interaction_type
        )

        return JsonResponse({'message': 'Interaction recorded successfully'})
    return JsonResponse({'error': 'Invalid method'}, status=405)



from .recommendations import recommend_products
@csrf_exempt
def get_recommendations(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        if not customer_id:
            return JsonResponse({'error': 'Missing customer_id'}, status=400)

        recommended_product_ids, recommendation_source = recommend_products(customer_id)
        
        if not recommended_product_ids:
            return JsonResponse({'error': 'No recommendations available'}, status=404)

        # Get products
        # Build ordering manually
        preserved_order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(recommended_product_ids)])

        products = models.Product.objects.filter(id__in=recommended_product_ids).order_by(preserved_order)
        serialized_products = serializers.RecommendedProductSerializer(products, many=True, context={'request': request}).data

        return JsonResponse({
            'recommended_products': serialized_products,
            'source': recommendation_source
        })
    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
def request_password_reset(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        try:
            user = User.objects.get(email=email)
            token = PasswordResetToken.objects.create(user=user)
            return JsonResponse({'token': str(token.token), 'email': email})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User with this email does not exist.'}, status=400)
        

@csrf_exempt
def reset_password(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        token = data.get('token')
        new_password = data.get('password')
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            reset_token.delete()
            return JsonResponse({'success': 'Password reset successful.'})
        except PasswordResetToken.DoesNotExist:
            return JsonResponse({'error': 'Invalid or expired token.'}, status=400)
        


# # Load data once
# model = joblib.load("solar_model/model.pkl")
# le_city = joblib.load("solar_model/city_encoder.pkl")
# panel_data = pd.read_csv("merged_solar_panels_with_city.csv")
# available_wattages = panel_data["Wattage"].dropna().unique()


BASE_DIR = settings.BASE_DIR  # root of your Django project

model_path = os.path.join(BASE_DIR, "solarcalculatormodels", "model.pkl")
encoder_path = os.path.join(BASE_DIR, "solarcalculatormodels", "city_encoder.pkl")
csv_path = os.path.join(BASE_DIR, "solarcalculatormodels","merged_solar_panels_with_city.csv")

model = joblib.load(model_path)
le_city = joblib.load(encoder_path)
panel_data = pd.read_csv(csv_path)
available_wattages = panel_data["Wattage"].dropna().unique()

@api_view(["POST"])
def predict_solar_setup(request):
    try:
        city = request.data.get("city")
        user_load = float(request.data.get("user_load"))  # in watt-hours/day

        if not city or user_load <= 0:
            return Response({"error": "Invalid city or load"}, status=400)

        city_encoded = le_city.transform([city])[0]

        best_result = {
            "total_price": float("inf"),
            "required_panels": 0,
            "panel_wattage": 0,
            "price_per_panel": 0
        }

        for wattage in available_wattages:
            wattage = float(wattage)
            required_kw = user_load / 1000
            required_panels = math.ceil((required_kw * 1000) / wattage)

            # Predict price per panel
            features_df = pd.DataFrame([{
                "Wattage": wattage,
                "CityEncoded": city_encoded,
                "UserLoad": user_load
            }])
            predicted_price_per_panel = model.predict(features_df)[0]
            total_price = predicted_price_per_panel * required_panels

            if total_price < best_result["total_price"]:
                best_result = {
                    "total_price": round(total_price),
                    "required_panels": required_panels,
                    "panel_wattage": int(wattage),
                    "price_per_panel": round(predicted_price_per_panel)
                }


        # ✅ Final prediction summary
        print("\n✅ Final ML Prediction:")
        print(f"   → City: {city}")
        print(f"   → Load: {user_load} Wh")
        print(f"   → Selected Panel Wattage: {best_result['panel_wattage']}W")
        print(f"   → Required Panels: {best_result['required_panels']}")
        print(f"   → Predicted Price/Panel: PKR {best_result['price_per_panel']}")
        print(f"   → Total Estimated Cost: PKR {best_result['total_price']}\n")
        
        return Response(best_result)

    except Exception as e:
        return Response({"error": str(e)}, status=500)