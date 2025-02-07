import json
import os

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, hashers
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserProfile
from .serializers import ProfileSerializer
from .forms import ProfileForm


class SignInAPIView(APIView):
    """
    Класс, отвечающий за вход пользователя в систему.
    """
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response(status=200)
        return Response(status=500)


class SingOutAPIView(APIView):
    """
    Класс, отвечающий за выход пользователя из системы
    """
    def post(self, request):
        logout(request)
        return Response(status=200)


class SignUpAPIView(APIView):
    """
    Класс, отвечающий за регистрацию новых пользователей
    """
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        name = data['name']
        email = username + '@django.ru'
        user = User.objects.create(username=username, email=email)
        user.password = hashers.make_password(password)
        user.save()
        # создается профиль пользователя с аватаркой "по-умолчанию"
        UserProfile.objects.create(
            user=user, email=email,
            avatar='avatar_default.png',
        )
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response(status=200)
        return Response(status=500)


class ProfileAPIView(APIView):
    """
    Класс, отвечающий за редактирование профиля пользователя
    можно редактировать:
    - ФИО
    - Номер телефона
    - адрес электронной почты
    - менять пароль
    - менять аватарку
    """

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile)
        print(serializer.data)
        return Response(serializer.data)

    def post(self, request):
        full_name = request.data['fullName'].split()
        surname = full_name[0]
        name = full_name[1]
        patronymic = full_name[2]
        phone = request.data['phone']

        profile = UserProfile.objects.get(user=request.user)
        profile.name = name
        profile.surname = surname
        profile.patronymic = patronymic
        profile.phone = phone
        profile.save()

        data = {
            "full_name": f"{profile.surname} {profile.name} {profile.patronymic}",
            "email": profile.email,
            "phone": profile.phone,
            "avatar": {
                "src": profile.avatar.url,
                "alt": profile.avatar.name,
            },
        }
        return JsonResponse(data)


class AvatarUpdateAPIView(APIView):
    """
        Класс отвечающий за смену аватарки пользователя.
        А так же удаление старого файла аватарки
    """
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        avatar_file = request.FILES.get('avatar')
        avatar_file_path = os.path.join(settings.MEDIA_ROOT, str(profile.avatar))

        # если получили новый файл аватара, то удалим
        # старый, если он конечно доступен и это не аватарка по-умолчанию
        if avatar_file:
            if os.path.isfile(avatar_file_path) and profile.avatar != 'avatar_default.png':
                os.remove(avatar_file_path)

        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return Response(status=200)
        return Response(status=500)


class ChangePasswordAPIView(APIView):
    """
    Класс, отвечающий за смену пароля пользователя.
    """
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        user = request.user
        current_password = request.data.get('currentPassword')
        new_password = request.data.get('newPassword')
        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            return Response(status=200)
        return Response(status=500)
