from django.db import models
from django.contrib.auth.models import User


class FoodCategory(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories/', default='categories/default.jpg')

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='restaurants/', default='restaurants/default.jpg')
    rating = models.FloatField(default=4.5)
    delivery_time = models.IntegerField(default=30)  # in minutes
    offer = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


from django.db import models

class Dish(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_card')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='dishes/', default='dishes/default.jpg')
    category = models.ForeignKey(FoodCategory, on_delete=models.SET_NULL, null=True, blank=True)

    limit = models.PositiveIntegerField(default=0, help_text="Maximum number of dishes available or per order.")

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"



class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    placed_order = models.ForeignKey('PlacedOrder', on_delete=models.CASCADE, related_name='items', null=True, blank=True)

    def save(self, *args, **kwargs):
        self.price = self.dish.price * self.quantity  # Automatically update price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order for {self.dish.name} by {self.user.username} (x{self.quantity})"

    @staticmethod
    def get_total_price_for_user(user):
        return sum(item.price for item in OrderItem.objects.filter(user=user))

class RestaurantDetails(models.Model):
    restaurant_id = models.CharField(max_length=150, unique=True)
    restaurant_password = models.CharField(max_length=128)

    def __str__(self):
        return self.restaurant_id

class PlacedOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant_name = models.CharField(max_length=200)  # New field
    dishes = models.TextField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    payment_method = models.CharField(max_length=100)
    delivery_status = models.CharField(max_length=50, default="Pending")  # Default status
    placed_on = models.DateField(auto_now_add=True)  # Date only, no time
    placed_time = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.restaurant_name} - {self.placed_on}"

