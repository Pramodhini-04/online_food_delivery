from django.contrib import admin
from django.utils.html import format_html
from .models import FoodCategory, Restaurant, Dish, OrderItem, RestaurantDetails, PlacedOrder


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview')
    search_fields = ('name',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 50px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image'


class DishInline(admin.TabularInline):
    model = Dish
    extra = 1


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'rating', 'delivery_time', 'offer')
    search_fields = ('name', 'location')
    list_filter = ('location', 'rating', 'delivery_time')
    inlines = [DishInline]

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'limit', 'image_preview')
    search_fields = ('name', 'restaurant__name', 'category__name')
    list_filter = ('restaurant', 'category')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 50px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image'

    fieldsets = (
        (None, {
            'fields': (
                'name',
                'restaurant',
                'category',
                'description',
                'price',
                'limit',        # ✅ added here
                'image'
            )
        }),
    )



@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'dish', 'quantity', 'price')
    list_filter = ('user', 'dish')
    search_fields = ('user__username', 'dish__name')
    readonly_fields = ('price',)


@admin.register(RestaurantDetails)
class RestaurantDetailsAdmin(admin.ModelAdmin):
    list_display = ('restaurant_id',)
    search_fields = ('restaurant_id',)


@admin.register(PlacedOrder)
class PlacedOrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant_name', 'delivery_status', 'placed_on', 'total_price')
    list_filter = ('delivery_status', 'placed_on', 'restaurant_name')
    search_fields = ('user__username', 'restaurant_name', 'city', 'zip_code')
    readonly_fields = ('placed_on', 'total_price')

    def total_price(self, obj):
        # Use the related_name='items' to access OrderItems
        total = sum(item.price for item in obj.items.all())
        return total
    total_price.short_description = 'Total Price'
