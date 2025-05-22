from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
import re
from django.contrib.auth.decorators import login_required
from .models import Restaurant, Dish, FoodCategory, OrderItem, RestaurantDetails, PlacedOrder
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from urllib.parse import urlencode

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Account created successfully! Please login.")
        return redirect('login')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('welcome')
        else:
            messages.error(request, 'Invalid Username or Password')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


@login_required
def restaurant_detail_view(request, restaurant_name):
    restaurant = get_object_or_404(Restaurant, name=restaurant_name)
    search_query = request.GET.get('q', '')
    dish_name = request.GET.get('dish', '')

    if dish_name:
        dishes = Dish.objects.filter(restaurant=restaurant, name__iexact=dish_name)
        message = f"Showing results for dish: {dish_name}"
    elif search_query:
        dishes = Dish.objects.filter(restaurant=restaurant, name__icontains=search_query)
        message = f"Search results for: {search_query}"
    else:
        dishes = Dish.objects.filter(restaurant=restaurant)
        message = ""

    return render(request, 'accounts/restaurant_detail.html', {
        'restaurant': restaurant,
        'dishes': dishes,
        'query': search_query,
        'message': message,
    })

@login_required
def dishes_by_category_view(request, category_name):
    dishes = Dish.objects.filter(category__name=category_name)
    category = get_object_or_404(FoodCategory, name=category_name)
    return render(request, 'accounts/dishes_by_category.html', {
        'dishes': dishes,
        'category': category,
    })


@login_required
def your_orders_view(request):
    orders = OrderItem.objects.filter(user=request.user)

    # Calculate total price of all orders for this user
    total_price = sum(order.price for order in orders)

    return render(request, 'accounts/your_orders.html', {
        'username': request.user.username,
        'orders': orders,
        'total_price': total_price  # Pass total to template
    })

from django.shortcuts import redirect, get_object_or_404
from .models import PlacedOrder
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def mark_as_delivered(request, order_id):
    order = get_object_or_404(PlacedOrder, id=order_id)
    if order.delivery_status == "Delivered":
        messages.info(request, "Order already delivered.")
        return redirect('restaurant_dashboard')

    time_diff = timezone.now() - order.placed_time
    if time_diff > timedelta(minutes=5):
        messages.error(request, "You can't deliver now. Time limit exceeded.")
        return redirect('restaurant_dashboard')

    order.delivery_status = "Delivered"
    order.save()
    messages.success(request, "Order marked as Delivered.")
    return redirect('restaurant_dashboard')

from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import urlencode
from .models import Restaurant, Dish, FoodCategory  # adjust if needed

def welcome_view(request):
    query = request.GET.get('q', '').strip()
    location_filter = request.GET.get('location', '').strip()
    rating_filter = request.GET.get('rating', '').strip()

    # Handle search query redirection
    if query:
        matched_restaurant = Restaurant.objects.filter(name__iexact=query).first()
        if matched_restaurant:
            return redirect('restaurant_detail', restaurant_name=matched_restaurant.name)

        matched_category = FoodCategory.objects.filter(name__iexact=query).first()
        if matched_category:
            return redirect('dishes_by_category', category_name=matched_category.name)

        matched_dish = Dish.objects.filter(name__iexact=query).first()
        if matched_dish:
            base_url = reverse('restaurant_detail', kwargs={'restaurant_name': matched_dish.restaurant.name})
            query_string = urlencode({'dish': matched_dish.name})
            return redirect(f'{base_url}?{query_string}')

    # Start with all restaurants
    restaurants = Restaurant.objects.all()

    # Apply location filter if selected
    if location_filter:
        restaurants = restaurants.filter(location__iexact=location_filter)

    # Apply rating filter if selected
    if rating_filter and rating_filter.isdigit():
        restaurants = restaurants.filter(rating__gte=int(rating_filter))

    food_categories = FoodCategory.objects.all()
    locations = Restaurant.objects.values_list('location', flat=True).distinct()

    return render(request, 'accounts/welcome.html', {
        'username': request.user.username,
        'restaurants': restaurants,
        'food_categories': food_categories,
        'locations': locations,
        'query': query,
        'selected_location': location_filter,
        'rating': rating_filter,
    })

@login_required
def submit_order_view(request):
    if request.method == 'GET':
        orders = OrderItem.objects.filter(user=request.user)
        if not orders.exists():
            return redirect('your_orders')
        return render(request, 'accounts/place_order.html', {'orders': orders})

    elif request.method == 'POST':
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        zip_code = request.POST.get('zip_code', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()

        # ✅ City validation: letters and spaces only
        if not re.fullmatch(r'[A-Za-z\s]+', city):
            messages.error(request, "City name must contain only letters and spaces.")
            return redirect('submit_order')

        # ✅ Zip code must be digits only
        if not zip_code.isdigit():
            messages.error(request, "Zip code must contain only numbers.")
            return redirect('submit_order')

        # ✅ Address validation: allow letters, digits, spaces, commas, hyphens, and slashes
        if not re.match(r'^[A-Za-z0-9\s,/-]+$', address):
            messages.error(request, "Address must contain only letters, digits, spaces, commas, hyphens, and slashes.")
            return redirect('submit_order')

        # ✅ Check if all fields are filled
        if not address or not city or not zip_code or not payment_method:
            messages.error(request, "All fields are required.")
            return redirect('submit_order')

        orders = OrderItem.objects.filter(user=request.user)
        if not orders.exists():
            messages.error(request, "No items to place order.")
            return redirect('your_orders')

        # ✅ Place separate order for each restaurant
        for restaurant_id in orders.values_list('dish__restaurant_id', flat=True).distinct():
            restaurant_orders = orders.filter(dish__restaurant_id=restaurant_id)
            restaurant = restaurant_orders.first().dish.restaurant
            restaurant_identifier = restaurant.name

            dish_list = [f"{item.dish.name} (x{item.quantity})" for item in restaurant_orders]
            dish_summary = ", ".join(dish_list)

            total_price = sum(item.dish.price * item.quantity for item in restaurant_orders)

            PlacedOrder.objects.create(
                user=request.user,
                restaurant_name=restaurant_identifier,
                dishes=dish_summary,
                address=address,
                city=city,
                zip_code=zip_code,
                payment_method=payment_method,
                delivery_status="Pending",
                total_price=total_price
            )

            restaurant_orders.delete()

        orders.delete()
        return redirect('order_confirmation')

@login_required
def order_confirmation_view(request):
    return render(request, 'accounts/order_confirmation.html')


# Additional OrderItem operations (cancel, update) remain unchanged
# OrderItem create functionality using Ajax (unchanged)
def place_order_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        dish_id = request.POST.get('dish_id')
        quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not provided

        dish = get_object_or_404(Dish, id=dish_id)
        total_price = dish.price * quantity

        # Create the order item
        order_item = OrderItem.objects.create(
            user=request.user,
            dish=dish,
            quantity=quantity,
            price=total_price
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Added {dish.name} to your orders!',
            'order_id': order_item.id,
            'dish_name': dish.name,
            'dish_price': total_price,
            'quantity': quantity
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


# Cancel order
@login_required
@require_POST
@csrf_exempt
def cancel_order_view(request):
    order_id = request.POST.get('order_id')

    if not order_id:
        return JsonResponse({'status': 'error', 'message': 'Order ID not provided'}, status=400)

    try:
        order = OrderItem.objects.get(id=order_id, user=request.user)
        order.delete()
        return JsonResponse({'status': 'success', 'message': 'Order deleted successfully'})
    except OrderItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)


# Update order quantity
@login_required
@require_POST
def update_order_quantity_view(request):
    order_id = request.POST.get('order_id')
    quantity = int(request.POST.get('quantity'))

    try:
        order = OrderItem.objects.get(id=order_id, user=request.user)
        dish_limit = order.dish.limit

        if quantity > dish_limit:
            return JsonResponse({
                'status': 'error',
                'message': f'Only {dish_limit} units of "{order.dish.name}" are available.'
            }, status=400)

        order.quantity = quantity
        order.price = order.dish.price * quantity  # Recalculate price
        order.save()

        return JsonResponse({
            'status': 'success',
            'new_total_price': f'{order.price:.2f}'  # Show updated price
        })

    except OrderItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

from django.contrib import messages
from .models import RestaurantDetails

def restaurant_login_view(request):
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        restaurant_password = request.POST.get('restaurant_password')

        try:
            restaurant = RestaurantDetails.objects.get(restaurant_id=restaurant_id)
            if restaurant.restaurant_password == restaurant_password:
                # Save the restaurant ID in the session
                request.session['restaurant_id'] = restaurant.restaurant_id
                return redirect('restaurant_dashboard')  # Redirect to dashboard
            else:
                messages.error(request, "Invalid password.")
        except RestaurantDetails.DoesNotExist:
            messages.error(request, "Restaurant ID not found.")

    return render(request, 'accounts/restaurant_login.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import PlacedOrder
from datetime import timedelta

def restaurant_dashboard(request):
    restaurant_id = request.session.get('restaurant_id')  # Retrieved during login

    if not restaurant_id:
        messages.error(request, "You must be logged in as a restaurant.")
        return redirect('restaurant_login')

    # Handle 'Deliver' button POST action
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = PlacedOrder.objects.get(id=order_id, restaurant_name=restaurant_id)
            order.delivery_status = "Delivered"
            order.save()
            messages.success(request, f"Order #{order_id} marked as Delivered.")
        except PlacedOrder.DoesNotExist:
            messages.error(request, "Order not found or you don't have permission.")

    # Fetch and update orders if more than 5 minutes passed with no delivery
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    all_orders = PlacedOrder.objects.filter(restaurant_name=restaurant_id)

    for order in all_orders:
        if (
            order.delivery_status == "Pending"
            and hasattr(order, 'placed_time')
            and order.placed_time <= five_minutes_ago
        ):
            order.delivery_status = "Not Delivered"
            order.save()
            messages.warning(request, f"Order #{order.id} marked as Not Delivered. Sorry for the inconvenience.")

    placed_orders = PlacedOrder.objects.filter(restaurant_name=restaurant_id).order_by('-id')

    context = {
        'restaurant_id': restaurant_id,
        'placed_orders': placed_orders
    }

    return render(request, 'accounts/restaurant_dashboard.html', context)

@login_required
def restaurant_logout(request):
    # Clear the restaurant's session
    if 'restaurant_id' in request.session:
        del request.session['restaurant_id']
    messages.success(request, "You have been logged out.")
    return redirect('restaurant_login')


@login_required
def order_history(request):
    # Get all placed orders for the current user
    user_orders = PlacedOrder.objects.filter(user=request.user).order_by('-placed_on')

    context = {
        'orders': user_orders
    }

    return render(request, 'accounts/order_history.html', context)

