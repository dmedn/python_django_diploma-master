from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from myauth.models import UserProfile


class Product(models.Model):
    """
    Класс Product, определяет свойства товара в магазине. Товары могут иметь:
    - category (категория к которой относится товар, например - "компьютеры")
    - subcategory   (у компьютеров может быть подкатегория, например "intel" или "amd")
    - price         (цена товара)
    - count         (количество товара на складе)
    - date          (дата занесения товара в базу данных)
    - title         (название товара)
    - description   (описание товара)
    - specification (спецификация)
    - free_delivery  (бесплатная или нет доставка)
    - tags          (ключевые слова товара, по которым может осуществляться поиск товара)
    - rating        (рейтинг товара)
    - count_of_orders   (количество единиц товара в заказе)
    """

    class Meta:
        ordering = ["title", "price", ]
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    title = models.CharField(max_length=200, verbose_name="Название продукта")
    price = models.DecimalField(default=0, max_digits=8, decimal_places=2)
    description = models.TextField(null=False, blank=True)
    count = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    free_delivery = models.BooleanField(default=True)
    count_of_orders = models.IntegerField(default=0)
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    subcategory = models.ForeignKey("Subcategory", on_delete=models.CASCADE)
    tags = models.ManyToManyField("Tag", verbose_name="Тег", related_name="tags")
    specification = models.ManyToManyField(
        "Specification", verbose_name="Характеристика", related_name="specification"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    def get_image(self):
        images = ProductImage.objects.filter(product_id=self.pk)
        return [
            {"src": item.image.url, "alt": item.image.name} for item in images
        ]

    def get_rating(self):
        reviews = Review.objects.filter(product_id=self.pk).values_list("rate", flat=True)
        if reviews.count == 0:
            rating = 0
            return rating
        rating = sum(reviews) / reviews.count()
        return rating

    def __str__(self):
        return self.title


def product_image_directory_path(instance: "ProductImage", filename: str) -> str:
    return f"products/product_{instance.pk}/images/{filename}"


class ProductImage(models.Model):
    """
        Класс отвечающий за связь конкретного товара с его изображениями
        он в себе имеет поля:
        - product
        - image
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=product_image_directory_path, blank=True)


def category_image_directory_path(instance: "Category", filename: str) -> str:
    return f"categories/category_{instance.pk}/image/{filename}"


class Category(models.Model):
    """
    Данный класс определяет основную категорию к которой будет
    относиться группа товаров, она в себе будет иметь:
    - title     (название категории)
    - image     (изображение данной категории)
    """
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    title = models.CharField(max_length=200, verbose_name="Название категории товаров")
    image = models.ImageField(
        null=True, blank=True,
        upload_to=category_image_directory_path,
    )

    def get_image(self):
        image = {
            "src": self.image.url,
            "alt": self.image.name,
        }
        return image


def subcategory_image_directory_path(instance: "Subcategory", filename: str) -> str:
    return f"subcategories/subcategory_{instance.pk}/image/{filename}"


class Subcategory(models.Model):
    """
    Данный класс определяет подкатегорию группы товаров. Имеет поля:
    - title         (название подкатегории)
    - category      (к какой категории относится эта подкатегория)
    - image         (изображение для данной подкатегории)
    """
    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"

    title = models.CharField(max_length=200, verbose_name="Название подкатегории товаров")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name="Название подкатегории товаров")
    image = models.ImageField(
        null=True, blank=True, upload_to=subcategory_image_directory_path
    )

    def get_image(self):
        image = {
            "src": self.image.url,
            "alt": self.image.name,
        }
        return image


class Tag(models.Model):
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Review(models.Model):
    """
    Данный класс отвечает за написание отзывов пользователями. Он имеет поля:
    - author        (кто написал отзыв)
    - text          (текст отзыва)
    - date          (дата и время написания отзыва)
    - product       (товар, с которым связан отзыв)
    - rate          (оценка товара)
    """
    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    text = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время создания отзыва")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Отзыв о товаре", related_name="reviews")
    rate = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(5), ], verbose_name="Оценка товара"
    )

    def __str__(self):
        return self.rate


class Specification(models.Model):
    """
     Класс, отвечающий за некие характеристики продукта. Имеет поля:
     - name
     - value
    """
    class Meta:
        verbose_name = "Характеристика"
        verbose_name_plural = "Характеристики"

    name = models.CharField(max_length=50, blank=True, null=True)
    value = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name}: {self.value}"


class Sale(models.Model):
    """
    Класс, отвечающий за распродажи каких-либо товаров. Имеет поля:
    - product       (продукт для распродажи)
    - date_from     (дата начала распродажи)
    - date_to       (дата конца распродажи)
    - discount      (размер скидки на товар)
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="sale_info")
    date_from = models.DateField()
    date_to = models.DateField()
    discount = models.DecimalField(max_digits=10, decimal_places=2)


class Basket(models.Model):
    """
    Модель корзины для товаров, связанная с пользователем и имеет поля:
    - user
    - created_at
    И сообщение об ошибке, если программа пытается обратиться к корзине,
    которой еще не существует.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    DoesNotExist = "Корзины не существует."


class BasketItem(models.Model):
    """
    Класс модели продуктов в корзине. Имеет поля:
    - basket    (связь с корзиной пользователя)
    - product   (связь с товарами)
    - quantity  (количество товаров)
    """

    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name="baskets")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="products")
    quantity = models.PositiveSmallIntegerField(default=1)


class Order(models.Model):
    """
    Класс, отвечающий за создание заказа из добавленных в корзину продуктов. Имеет поля:
    - full_name         (имя пользователя, с которым связан заказ)
    - created_at        (когда создан заказ)
    - products          (какие в нём продукты)
    - city              (Город доставки)
    - delivery_address  (Адрес доставки)
    - delivery_type     (Тип доставки: простая или экспресс)
    - payment_type      (Как будет оплачиваться заказ)
    - total_cost        (Итоговая сумма заказа)
    - status               (Статус заказа)
    - basket            (Связь с корзиной пользователя    )
    - payment_error     (Ошибка оплаты заказа)
    """

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
    DELIVERY_OPTIONS = (
        ("delivery", "Доставка"),
        ("express", "Экспресс доставка"),
    )
    PAYMENT_OPTIONS = (
        ("online", "Онлайн оплата"),
        ("online_any", "Онлайн оплата со случайного счета"),
    )

    full_name = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Покупатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания заказа")
    products = models.ManyToManyField(Product, related_name="orders")
    city = models.CharField(max_length=100, verbose_name="Город доставки")
    delivery_address = models.CharField(max_length=200, verbose_name="Адрес доставки")
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_OPTIONS, default="Доставка")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_OPTIONS, default="Онлайн оплата")
    total_cost = models.DecimalField(
        default=0, max_digits=8, decimal_places=2, verbose_name="Итоговая сумма заказа"
    )
    status = models.CharField(max_length=255, default="В обработке")
    basket = models.ForeignKey(
        Basket, on_delete=models.CASCADE, related_name="orders", default=None)
    payment_error = models.CharField(max_length=255, blank=True, default="")
    archived = models.BooleanField(default=False)


class DeliveryPrices(models.Model):
    """
    В данном классе можно менять стоимость доставки товаров
    """
    class Meta:
        verbose_name = "Стоимость доставки"

    delivery_cost = models.DecimalField(
        default=0,
        max_digits=8,
        decimal_places=2,
        verbose_name="Стоимость доставки",
    )

    delivery_express_cost = models.DecimalField(
        default=0,
        max_digits=8,
        decimal_places=2,
        verbose_name="Стоимость экспресс доставки",
    )

    delivery_free_minimum_cost = models.DecimalField(
        default=0,
        max_digits=8,
        decimal_places=2,
        verbose_name="Наименьшая сумма для бесплатной доставки",
    )


class Payment(models.Model):
    """
    Класс модели оплаты заказа имеет поля:
    - order             (Какой заказ будем оплачивать)
    - card_number       (Номер банковской карты)
    - validity period   (Срок действия карты)
    - success           (Статус выполнения оплаты)
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="pay_order")
    card_number = models.CharField(max_length=16)
    validity_period = models.CharField(max_length=20)
    success = models.BooleanField(default=False)
