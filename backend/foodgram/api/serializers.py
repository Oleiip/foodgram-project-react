import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCart, Tag)
from rest_framework import serializers, status
from rest_framework.validators import UniqueTogetherValidator

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if self.context.get('request').user.is_anonymous:
            return False
        return obj.following.filter(user=request.user).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя"""
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'password')


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор подписок"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes_count', 'recipes'
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def validate(self, data):
        author_id = self.context.get(
            'request').parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = self.context.get('request').user
        if user.follower.filter(author=author_id).exists():
            raise serializers.ValidationError(
                detail='Подписка уже существует',
                code=status.HTTP_400_BAD_REQUEST,
            )
        if user == author:
            raise serializers.ValidationError(
                detail='Нельзя подписаться на самого себя',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )
        validators = [
            UniqueTogetherValidator(
                queryset=Ingredient.objects.all(),
                fields=('name', 'measurement_unit'),
                message=('Такой ингредиент уже есть базе.')
            )
        ]


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class Base64ImageField(serializers.ImageField):
    """Сериализатор фото"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор связи ингридиентов и рецепта"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name', read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')
        extra_kwargs = {
            'amount': {
                'min_value': None,
            },
        }


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра рецепта"""
    author = CustomUserSerializer(read_only=True,
                                  default=serializers.CurrentUserDefault())
    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientsSerializer(many=True,
                                              source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        user_name = self.context['request'].user

        if self.context['request'].user.is_authenticated:
            user = get_object_or_404(
                User, username=user_name)
            return user.favorites.filter(recipe=obj.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user_name = self.context['request'].user

        if self.context['request'].user.is_authenticated:
            user = get_object_or_404(
                User, username=user_name)
            return user.shopping_list.filter(recipe=obj.id).exists()
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор создания и обновления рецепта"""
    ingredients = RecipeIngredientsSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('author', 'name'),
                message='Вы уже создавали рецепт с таким названием.'
            )
        ]

    def validate_tags(self, tags):
        for tag in tags:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Указанного тега не существует')
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Минимальное время приготовления 1 минута')
        return cooking_time

    def validate_ingredients(self, ingredients):
        ingredients_list = []
        if not ingredients:
            raise serializers.ValidationError(
                'Отсутствуют ингридиенты')
        for ingredient in ingredients:
            if ingredient['id'] in ingredients_list:
                raise serializers.ValidationError(
                    'Ингридиенты должны быть уникальны')
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента больше 0')
            ingredients_list.append(ingredient['id'])
        return ingredients

    @staticmethod
    def save_ingredients(recipe, ingredients):
        """Метод создания ингредиента."""
        ingredients_list = []
        for ingredient in ingredients:
            ingredients_list.append(
                RecipeIngredients(
                    amount=ingredient['amount'],
                    ingredient=get_object_or_404(
                        Ingredient, pk=ingredient['id']), recipe=recipe,
                    )
                )
        RecipeIngredients.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        """Метод создания рецепта."""
        request = self.context.get('request', None)
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=request.user)
        recipe.tags.set(tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления рецепта."""
        instance.tags.clear()
        RecipeIngredients.objects.filter(recipe=instance).delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.save_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок"""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data['user']
        if user.shopping_list.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже есть в корзине'
            )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов"""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data['user']
        if user.favorites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
