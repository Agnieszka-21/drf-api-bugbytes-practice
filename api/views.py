from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view

from api.serializers import ProductSerializer
from api.models import Product


@api_view(['GET'])
def product_list(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)