import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter

from .models import (
    Category,
    Product,
    Review, Tag,
    Sale,
    Basket,
    BasketItem,
    Order,
    Payment,
    DeliveryPrices,
)
from .serializers import (
    ProductSerializer,
    DetailsSerializer,
    TagSerializer,
    BasketItemSerializer, OrderSerializer,

)

from myauth.models import UserProfile


class CategoryAPIView(APIView):
    """
    Класс отвечающий за вывод категорий и подкатегорий товаров
    на кнопку "All Departments"
    """

    def get(self, request):
        categories = Category.objects.all()
        categories_data = []
        for category in categories:
            subcategories = category.subcategory_set.all()
            subcategories_data = []
            for subcategory in subcategories:
                data_sub = {
                    "id": subcategory.pk,
                    "title": subcategory.title,
                    "image": subcategory.get_image(),
                }
                subcategories_data.append(data_sub)
            data_cat = {
                "id": category.pk,
                "title": category.title,
                "image": category.get_image(),
                "subcategories": subcategories_data,
            }
            categories_data.append(data_cat)
        return JsonResponse(categories_data, safe=False)


class BannerListAPIView(ListAPIView):
    """
    Класс, отвечающий за вывод трех баннеров с продуктов с самым высоким рейтингом
    """
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(rating__gt=0).order_by('-rating')[:3]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PopularListAPIView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(tags__name__in=['popular'])[:8]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class LimitedListAPIView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(tags__name__in=['limited'])[:16]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductDetailsRetrieveAPIView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = DetailsSerializer
    lookup_url_kwarg = "id"


class CatalogAPIView(APIView):
    """
    Класс отвечающий за вывод каталога товаров с фильтрацией и сортировкой.
    """
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        'category': ['exact'],      # точное соответствие
        'price': ['gte', 'lte'],    # диапазон от "больше или равно" до "меньше или равно"
        'freeDelivery': ['exact'],  # точное соответствие
        'count': ['gt'],             # больше
        'title': ['icontains'],      # содержит (неточное определение)
        'tags__name': ['exact'],     # точное соответствие
    }
    ordering_fields = [
        'id',
        'category__id',
        'price',
        'count',
        'date',
        'title',
        'freeDelivery',
        'rating',
    ]

    def filter_queryset(self, products):
        category_id = self.request.GET.get('category')
        min_price = float(self.request.GET.get('filter[minPrice]', 0))
        max_price = float(self.request.GET.get('filter[maxPrice]', float('inf')))
        free_delivery = self.request.GET.get('filter[freeDelivery]', '').lower() == 'true'
        available = self.request.GET.get('filter[available]', '').lower() == 'true'
        name = self.request.GET.get('filter[name]', '').strip()
        tags = self.request.GET.getlist('tags[]')
        sort_field = self.request.GET.get('sort', 'id')
        sort_type = self.request.GET.get('sortType', 'inc')

        if category_id:
            products = products.filter(category__id=category_id)
        products = products.filter(price__gte=min_price, price__lte=max_price)
        if free_delivery:
            products = products.filter(freeDelivery=True)
        if available:
            products = products.filter(count__gt=0)
        if name:
            products = products.filter(title__icontains=name)
        for tag in tags:
            products = products.filter(tags__name=tag)
        if sort_type == 'inc':
            products = products.order_by(sort_field)
        else:
            products = products.order_by('-' + sort_field)

        return products

    def get(self, request):
        products = Product.objects.all()
        filtered_products = self.filter_queryset(products)
        page_number = int(request.GET.get('currentPage', 1))
        limit = int(request.GET.get('limit', 20))
        paginator = Paginator(filtered_products, limit)
        page = paginator.get_page(page_number)
        products_list = []
        for product in page:
            products_list.append(ProductSerializer(product).data)
        catalog_data = {
            "items": products_list,
            "currentPage": page_number,
            "lastPage": paginator.num_pages
        }
        return Response(catalog_data)


class ProductReviewAPIView(ProductDetailsRetrieveAPIView):
    """
    Класс, обрабатывающий оставление пользователями отзывов о товаре
    """
    def post(self, request, **kwargs):
        if request.user.is_authenticated:
            profile = UserProfile.objects.get(user=request.user)
            product = Product.objects.get(pk=kwargs['id'])
            author = profile
            text = request.data['text']
            rate = request.data['rate']

            review = Review.objects.create(
                author=author,
                text=text,
                rate=rate,
                product=product,
            )
            review.save()
            return Response(status=200)
        return Response(status=403)


class TagListAPIView(ListAPIView):
    """
    Класс отвечающий за вывод тегов к товару
    """
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.all().distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SalesListAPIView(APIView):
    """
    Класс обрабатывающий товары, попадающие под распродажу
    """
    def get(self, request):
        page_number = int(request.GET.get('currentPage', 1))
        limit = int(request.GET.get('limit', 20))
        obj_list = []
        for obj in Sale.objects.all():
            obj_list.append(obj)
        paginator = Paginator(obj_list, limit)
        page = paginator.get_page(page_number)
        serialized_data = []

        for sale in page:
            serialized_data.append({
                "id": sale.product.id,
                "price": sale.product.price,
                "salePrice": sale.product.price - sale.discount,
                "dateFrom": sale.date_from,
                "dateTo": sale.date_to,
                "title": sale.product.title,
                "images": [
                    {
                        "src": settings.MEDIA_URL + str(image.image),
                        "alt": sale.product.title,
                    }
                    for image in
                    sale.product.images.all()],
            })
        response_data = {
            "items": serialized_data,
            "currentPage": page_number,
            "lastPage": paginator.num_pages
        }
        return Response(response_data)


class BasketItemsAPIView(APIView):
    """
    Класс, отвечающий за чтение, добавление и удаление данных о
    товарах в корзине
    """
    def get(self, request):
        """
        Вывод информации о товарах в корзине
        """
        if request.user.is_anonymous:
            anon_user = User.objects.get(username="anonymous")
            request.user = User.objects.get(id=anon_user.id)

        queryset = BasketItem.objects.filter(basket__user=request.user)
        serializer = BasketItemSerializer(queryset, many=True)

        return Response(serializer.data)

    def post(self, request):
        # Обрабатывается нажатие на кнопку "Add to cart"
        # принимаем данные, об id товара и его количестве из запроса
        id = request.data['id']
        count = request.data['count']

        # если вход не осуществлен, то назначаем пользователя по-умолчанию
        if request.user.is_anonymous:
            anon_user = User.objects.get(username="anonymous")
            basket, created = Basket.objects.update_or_create(user=anon_user)
        else:
            try:
                basket = request.user.basket
            except Basket.DoesNotExist:
                basket = Basket.objects.create(user=request.user)

        # получаем объект продукта по его id
        product = Product.objects.get(id=id)
        # создаем объект продукта в корзине, если его еще там нет
        basket_item, created = BasketItem.objects.get_or_create(basket=basket, product=product)

        # мы можем добавлять количество товара в корзину, но не больше чем его есть в наличии
        if not created and (product.count - basket_item.quantity) != 0:
            basket_item.quantity += count
            basket_item.save()

        # получаем обновленные данные корзины, передаем в сериализатор
        # где они обрабатываются и возвращаются для отображения на страничке
        basket_items = BasketItem.objects.filter(basket=basket)
        serializer = BasketItemSerializer(basket_items, many=True)

        return Response(serializer.data, status=201)

    def delete(self, request):
        id = request.data['id']
        count = request.data['count']

        try:
            if request.user.is_anonymous:
                anon_user = User.objects.get(username="anonymous")
                request.user = User.objects.get(id=anon_user.id)
            # получаем объект, который хотим удалить
            basket = request.user.basket
            # получаем продукт, который хотим удалить из корзины
            product = Product.objects.get(id=id)
            # получаем товар в корзине для удаления
            basket_item = BasketItem.objects.get(basket=basket, product=product)
            if basket_item.quantity > count:
                basket_item.quantity -= count  # будем нажимать кнопку "минус" до тех пор пока не будет 0
                basket_item.save()
            else:
                basket_item.delete()

            # получаем обновленные данные корзины, передаем в сериализатор
            # где они обрабатываются и возвращаются для отображения на страничке
            basket_items = BasketItem.objects.filter(basket=basket)
            serializer = BasketItemSerializer(basket_items, many=True)

            return Response(serializer.data)
        except Basket.DoesNotExist:
            return Response("Товары в корзине не найдены", status=404)


class OrdersAPIView(APIView):
    """
    Класс обрабатывающий создание заказа. Вывод истории заказов.
    """
    def get(self, request):
        """
        Данный метод отвечает за вывод истории заказов в меню профиля пользователя
        """
        orders = Order.objects.filter(archived=True)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Создается заказ из находящихся в корзине товаров, либо передается номер
        незакрытого заказа, для завершения оформления.
        """
        try:
            # Необходимо перед первым вызовом DeliveryPrices создать объект
            # delivery_price в админке и назначить стоимость доставки, иначе будет ошибка
            delivery_price = DeliveryPrices.objects.get(id=1)
            basket = request.user.basket
            profile = UserProfile.objects.get(user=request.user)
            basket_items = BasketItem.objects.filter(basket__user=request.user)
            total_cost = 0
            # Проверим, есть ли у нас незакрытые заказы, если нет то создадим новый
            active_order = Order.objects.filter(archived=False)
            if not active_order:
                order = Order.objects.create(full_name=profile, basket=basket)
                for item in basket_items:
                    product = Product.objects.get(pk=item.product.pk)
                    product.count_of_orders = item.quantity
                    total_cost += item.product.price * item.quantity
                    product.save()
                if total_cost > delivery_price.delivery_free_minimum_cost:
                    order.total_cost = total_cost
                else:
                    order.total_cost = total_cost + delivery_price.delivery_cost
                order.save()
                response_data = {"orderId": order.pk}
                return JsonResponse(response_data)
            else:
                # если был незавершенный заказ, то завершим его
                return JsonResponse({"orderId": active_order[0].pk})
        except Basket.DoesNotExist:
            error_data = {"error": "У данного пользователя пока нет 'корзины'"}
            return JsonResponse(error_data)


class OrderRegistrationAPIView(APIView):
    """
    Класс, обрабатывающий оформление заказа. Доставка. Оплата.
    """
    def get(self, request, order_id):
        order = Order.objects.get(pk=order_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        delivery_type = request.data["deliveryType"]
        payment_type = request.data["paymentType"]
        city = request.data["city"]
        address = request.data["address"]
        status_order = "подтвержден"
        print(delivery_type)
        if delivery_type == "express":
            delivery_price = DeliveryPrices.objects.get(id=1)
            order.total_cost += delivery_price.delivery_express_cost
            order.save()

        order.delivery_type = delivery_type
        order.payment_type = payment_type
        order.city = city
        order.address = address
        order.status = status_order
        order.save()
        response_data = {"orderId": order.id}
        return Response(response_data, status=200)


class PaymentAPIView(APIView):
    """
    Класс, отвечающий за оплату заказа
    """
    def post(self, request, order_id):
        data = request.data
        card_number = data['number']
        expiration_month = data['month']
        expiration_year = data['year']
        current_year = datetime.datetime.now().year % 100

        # проверяем срок действия кредитной карты
        if int(expiration_year) < current_year or (
                int(expiration_year == current_year) and
                int(expiration_month) < datetime.datetime.now().month):
            order = Order.objects.get(id=order_id)
            order.payment_error = "Payment expired"
            order.save()
            print("payment expired")
            return JsonResponse({"error": "Payment expired"})

        # номер должен быть чётным и не длиннее восьми цифр
        if not (len(card_number.strip()) <= 8 and int(card_number) % 2 == 0):
            print("card number invalid")
            return JsonResponse({"error": "Неверный номер банковской карты"})
        res_date = f"{expiration_month}.{expiration_year}"
        order = Order.objects.get(id=order_id)
        payment = Payment.objects.create(order=order, card_number=card_number, validity_period=res_date)
        order.status = 'оплачено'
        order.archived = True
        order.save()
        # заказ оплачен
        # можно очистить корзину
        basket = Basket.objects.get(user=request.user)
        basket_items = BasketItem.objects.filter(basket=basket)
        for basket_item in basket_items:
            product = Product.objects.get(pk=basket_item.product.pk)
            product.count -= basket_item.quantity
            payment.success = True
            payment.save()
        basket_items.delete()
        return HttpResponse(status=200)

