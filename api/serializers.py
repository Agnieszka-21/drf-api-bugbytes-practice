from rest_framework import serializers
from django.db import transaction

from .models import Product, Order, OrderItem, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # exclude = ('password', 'user_permissions') # can be problematic - not specific enough
        # fields = '__all__' # not recommended in most cases - be as explicit as possible
        fields = (
            'username',
            'email',
            'is_staff',
            'is_authenticated', # with fields you can reference properties on the model
            'get_full_name', # with fields you can reference methods on the model that don't have any arguments
            'orders' # with fields you can reference related fields
        )


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'description',
            'name',
            'price',
            'stock',
        )

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0"
            )
        else:
            return value
        

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    product_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source='product.price'
    )

    class Meta:
        model = OrderItem
        fields = (
            'product_name',
            'product_price',
            'quantity',
            'item_subtotal'
        )


class OrderCreateSerializer(serializers.ModelSerializer):
    class OrderItemCreateSerializer(serializers.ModelSerializer):
        class Meta:
            model = OrderItem
            fields = ('product', 'quantity')

    order_id = serializers.UUIDField(read_only=True)
    items = OrderItemCreateSerializer(many=True, required=False)

    def update(self, instance, validated_data):
        orderitem_data = validated_data.pop('items')

        with transaction.atomic(): # prevents the order from being partially updated should anything go wrong
            instance = super().update(instance, validated_data)
            if orderitem_data is not None:
                # Clear existing items (optional, depends on requirements)
                instance.items.all().delete()
                # (Re)Create the items with the updated data
                for item in orderitem_data:
                    OrderItem.objects.create(order=instance, **item)
        return instance

    def create(self, validated_data):
        orderitem_data = validated_data.pop('items')

        with transaction.atomic(): # prevents the order from being partially created should anything go wrong
            order = Order.objects.create(**validated_data)
            for item in orderitem_data:
                OrderItem.objects.create(order=order, **item)
        return order

    class Meta:
        model = Order
        fields = (
            'order_id',
            'user',
            'status',
            'items',
        )
        extra_kwargs = {
            'user': {'read_only': True}
        }
        

class OrderSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        order_items = obj.items.all()
        return sum(order_item.item_subtotal for order_item in order_items)

    class Meta:
        model = Order
        fields = (
            'order_id',
            'created_at',
            'user',
            'status',
            'items',
            'total_price'
        )


class ProductInfoSerializer(serializers.Serializer):
    products = ProductSerializer(many=True)
    count = serializers.IntegerField()
    max_price = serializers.FloatField()
