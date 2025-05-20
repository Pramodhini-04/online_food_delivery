from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('restaurant/<str:restaurant_name>/', views.restaurant_detail_view, name='restaurant_detail'),
    path('category/<str:category_name>/', views.dishes_by_category_view, name='dishes_by_category'),
    path('your-orders/', views.your_orders_view, name='your_orders'),
    path('place-order/', views.place_order_view, name='place_order'),
    path('cancel-order/', views.cancel_order_view, name='cancel_order'),
    path('update-order-quantity/', views.update_order_quantity_view, name='update_order_quantity'),
    path('submit-order/', views.submit_order_view, name='submit_order'),
    path('order-confirmation/', views.order_confirmation_view, name='order_confirmation'),
    path('restaurant_login/', views.restaurant_login_view, name='restaurant_login'),
    path('logout/', views.logout_view, name='logout'),
    path('order_history/', views.order_history, name='order_history'),
    path('restaurant_dashboard/', views.restaurant_dashboard, name='restaurant_dashboard'),
    path('restaurant_logout/', views.restaurant_logout, name='restaurant_logout'),
    path('mark-as-delivered/<int:order_id>/', views.mark_as_delivered, name='mark_as_delivered'),
]

