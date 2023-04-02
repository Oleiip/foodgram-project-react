from datetime import datetime

from api.filters import RecipeFilter
from api.pagination import CustomPageNumberPagination
from api.permissions import IsAuthorOrAdminPermission
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeReadSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, TagSerializer)
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCart, Tag)
from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Subscription

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer

        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=('post',))
    def favorite(self, request, pk=None):
        context = {"request": request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = FavoriteSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        get_object_or_404(
            Favorite,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post',))
    def shopping_cart(self, request, pk):
        context = {'request': request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = ShoppingCartSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        get_object_or_404(
            ShoppingCart,
            user=request.user.id,
            recipe=get_object_or_404(Recipe, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        recipes = [item.recipe.id for item in shopping_cart]
        buy_list = RecipeIngredients.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient'
        ).annotate(
            amount=Sum('amount')
        )
        today = datetime.today()
        buy_list_text = (
            f'Список покупок для: {user.get_full_name()}\n\n'
            f'Дата: {today:%Y-%m-%d}\n\n'
        )
        for item in buy_list:
            ingredient = Ingredient.objects.get(pk=item['ingredient'])
            amount = item['amount']
            buy_list_text += (
                f'{ingredient.name}, {amount} '
                f'{ingredient.measurement_unit}\n'
            )

        response = HttpResponse(buy_list_text, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=shopping-list.txt'
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CustomUserViewSet(UserViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPageNumberPagination

    @action(
        detail=False,
        methods=('get',),
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated, ),
        url_path='me',
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            paginated_queryset, many=True, context={'request': request}
        )

        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        serializer_class=SubscriptionSerializer
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if user == author:
            raise exceptions.ValidationError(
                'Подписка на самого себя запрещена.'
            )
        if Subscription.objects.filter(user=user,
                                       author=author).exists():
            raise exceptions.ValidationError('Подписка уже оформлена.')

        Subscription.objects.create(user=user, author=author)
        serializer = self.get_serializer(author)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            user=user, author=author)
        if not subscription.exists():
            return Response(
                {'errors': 'Нет такой подписки'},
                status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
