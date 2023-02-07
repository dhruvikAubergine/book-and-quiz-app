from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import VerifyEmailView
from graphene_django.views import GraphQLView

urlpatterns =[
    path('', csrf_exempt(GraphQLView.as_view(graphiql=True)), name="user"),
    path('verifyAccount/', VerifyEmailView.as_view(), name="verifyAccount"),
]