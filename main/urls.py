from django.urls import path
from . import views
from .views import StripeCheckoutView, chat_with_gemini
from rest_framework import routers

router = routers.DefaultRouter()
router.register('address', views.CustomerAddressViewSet)
router.register('productrating', views.ProductRatingViewSet)

urlpatterns = [
    path('sellers/', views.SellerList.as_view()),
    path('seller/<int:pk>/', views.SellerDetail.as_view()),
    path('seller/login/', views.seller_login, name='seller_login'),
    path('seller-products/<int:seller_id>/', views.SellerProductList.as_view()),
    path('seller/<int:pk>/dashboard/', views.seller_dashboard),
    path('seller-change-password/<int:seller_id>/', views.seller_change_password),
    path('seller/register/', views.seller_register, name='seller_register'),
    path('seller/<int:pk>/orderitems/', views.SellerOrderItemList.as_view()),
    path('seller/<int:pk>/customers/', views.SellerCustomerList.as_view()),
    path('seller/<int:seller_id>/customer/<int:customer_id>/orderitems/', views.SellerCustomerOrderItemList.as_view()),
    path('seller/seller-chats/', views.SellerChatsView.as_view()),

    path('products/', views.ProductList.as_view()),
    path('products/<str:tag>/', views.TagProductList.as_view()),
    path('product/<int:pk>/', views.ProductDetail.as_view()),
    path('related-products/<int:pk>/', views.RelatedProductList.as_view()),
    path('product-imgs/', views.ProductImgList.as_view()),
    path('product-imgs/<int:product_id>/', views.ProductImgsDetail.as_view()),
    path('product-img/<int:pk>/', views.ProductImgDetail.as_view()),
    path('product-reviews/<int:product_id>/', views.ProductRatingViewSet.as_view({'get': 'product_reviews'}), name='product-reviews'),
    
    path('customers/', views.CustomerList.as_view()),
    path('customer/<int:pk>/', views.CustomerDetail.as_view()),
    path('user/<int:pk>/', views.UserDetail.as_view()),
    path('customer/dashboard/<int:pk>/', views.customer_dashboard, name='customer_dashboard'),
    path('customer-change-password/<int:customer_id>/', views.customer_change_password),
    path('customer/login/', views.customer_login, name='customer_login'),
    path('customer/register/', views.customer_register, name='customer_register'),

    path('orders/', views.OrderList.as_view()),
    path('orderitems/', views.OrderItemList.as_view()),
    path('delete-customer-orders/<int:customer_id>/', views.delete_customer_orders),
    path('customer/<int:pk>/orders/', views.CustomerOrderList.as_view()),
    path('customer/<int:pk>/orderitems/', views.CustomerOrderItemList.as_view()),
    path('order/<int:pk>/', views.OrderDetail.as_view()),
    path('order-modify/<int:pk>/', views.OrderModify.as_view()),
    path('mark-as-delivered/<int:order_item_id>/', views.MarkAsDeliveredView.as_view(), name='mark-as-delivered'),
    path('mark-as-received/<int:order_id>/', views.MarkAsReceivedView.as_view(), name='mark-as-delivered'),

    path('categories/', views.CategoryList.as_view()),
    path('category/<int:pk>/', views.CategoryDetail.as_view()),
    
    path('create-checkout-session/', StripeCheckoutView.as_view(), name='create-checkout-session'),
    path('verify-payment-session/<str:session_id>/', views.verify_payment_session, name='verify-payment-session'),
    path('update-order-status/', views.update_order_status, name='update-order-status'),

    #wishlist
    path('wishlist/', views.WishList.as_view()),
    path('check-in-wishlist/', views.check_in_wishlist, name='check_in_wishlist'),
    path('remove-from-wishlist/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('customer/<int:pk>/wishitems/', views.CustomerWishItemList.as_view()),
    path('customer/<int:pk>/address-list/', views.CustomerAddressList.as_view()),
    
    path('mark-default-address/<int:pk>/', views.mark_default_address, name='mark_default_address'),
    
    path('aichat/', chat_with_gemini, name="chat_with_gemini"),
    
    path('send_message/', views.SendMessageView.as_view(), name='send_message'),
    path('get_chat/<int:seller_id>/<int:customer_id>/', views.GetChatMessagesView.as_view(), name='get_chat_messages'),
    path('seller_chats/<int:seller_id>/', views.SellerChatsView.as_view(), name='seller_chats'),
    path('customer_chats/<int:customer_id>/', views.CustomerChatsView.as_view(), name="customer_chats"),
    
    path('record_interaction/', views.record_interaction, name='record_interaction'),
    path('get_recommendations/', views.get_recommendations, name='get_recommendations'),
    
    path('request_password_reset/', views.request_password_reset, name='request_password_reset'),
    path('reset_password/', views.reset_password, name='reset_password'),
    
    path('predict-solar-setup/', views.predict_solar_setup),
]

urlpatterns += router.urls