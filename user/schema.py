import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model, authenticate
from .models import User
from django.conf import settings
import random
import string
from django.core.mail import send_mail
import jwt
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

# def jwt_encode(user):
#     payload = {
#         "email": user.email,
#         "username": user.username,
#         "password": user.password
#     }
#     return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def get_user_from_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        User = get_user_model()
        return User.objects.get(id=user_id)
    except (jwt.DecodeError, User.DoesNotExist):
        return None


class Query(graphene.ObjectType):
    me = graphene.Field(lambda: UserType)

    def resolve_me(self, info):
        user = get_user_from_token(info.context.headers["Authorization"])
        if user is None:
            raise Exception("Not authenticated")
        return user


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = "__all__"


class RegisterUserMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)
    message = graphene.String()
    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, username, email, password):
        try:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            # import pdb;pdb.set_trace()
        except Exception as e:
            return RegisterUserMutation(success=False, message=str(e))
        token = RefreshToken.for_user(user).access_token
        user.save()
        subject = "Verify your account"
        # current_site = info.context.request.build_absolute_uri()
        # relative_link = reverse("verifyAccount")
        absurl = (
            "http://127.0.0.1:8000/user/" + "verifyAccount/" + "?token=" + str(token)
        )
        message = f"Follow this link to verify your account: {absurl}"
        from_email = "greatblogs.mail@gmail.com"
        to_email = [user.email]
        mail = send_mail(subject, message, from_email, to_email)
        print(subject, message, from_email, to_email, mail)
        return RegisterUserMutation(
            user=user, message="your are register", success=True
        )


class LoginUserMutation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    token = graphene.String()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, email, password):
        user = authenticate(email=email, password=password)
        # import pdb
        # pdb.set_trace()
        # print("user", user.email, user.username, user.password)
        if user is None:
            return LoginUserMutation(success=False, message="Invalid credentials")
        if not user.is_verified:
            return LoginUserMutation(success=False, message="Email is not verified")
        return LoginUserMutation(
            user=user,
            success=True,
            message="Successfully logged in",
            token=str(user.tokens()),
        )


class DeleteUserMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    user = graphene.Field(UserType)

    @classmethod
    def mutate(cls, root, info, id):
        user = User.objects.get(id=id)
        user.delete()
        return


class Mutation(graphene.ObjectType):
    register_user = RegisterUserMutation.Field()
    login = LoginUserMutation.Field()
    # verifyAccount = VerifyAccountMutation.Field()
    delete_user = DeleteUserMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
