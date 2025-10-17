from django.shortcuts import render
from api import serializers as api_serializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from api import models as api_model
from rest_framework import generics,status
from userauth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from decimal import Decimal

import random

from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string



class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializer.MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset=User.objects.all()
    permission_classes=[AllowAny]
    serializer_class=api_serializer.RegisterSerializer
def generate_random_otp(length=7):
    otp=''.join([str(random.randint(0,9)) for _ in range(length)])
    return otp
class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
    permission_classes= [AllowAny]
    serializer_class=api_serializer.UserSerializer

    def get_object(self):
        email=self.kwargs['email']

        user=User.objects.filter(email=email).first()

        if user:

            uuidb64=user.pk
            refresh=RefreshToken.for_user(user)
            refresh_token=str(refresh.access_token)
            user.refresh_token=refresh_token
            user.otp=generate_random_otp()
            user.save()

            link= f"http://localhost:513/create-new-password/?otp{user.otp}&uuidb64={uuidb64}&=refresh_token{refresh_token}"

            context={
                "link":link,
                "username":user.username
            }

            subject= "password Reset Email"
            text_body=render_to_string("email/password_reset.txt",context)
            html_body=render_to_string("email/password_reset.html",context)

            msg=EmailMultiAlternatives(
                subject=subject,
                from_email=settings.FROM_EMAIL,
                to=[user.email],
                body=text_body
            )

            msg.attach_alternative(html_body,"text/html")
            msg.send()

            print("link ======",link)
        
        return user
        
class PasswordChangeAPIView(generics.CreateAPIView):
    permission_classes=[AllowAny]
    serializer_class=api_serializer.UserSerializer

    def create(self,request,*args,**kwargs):
        payload=request.data

        otp=payload['otp']
        uuidb64=payload['uuid64']
        password=payload['password']

        user=User.objects.get(id=uuidb64,otp=otp)
        if user:
            user.set_password(password)
            user.otp=""
            user.save()

            return Response({"message":"Password Changed Successfully"},status=status.HTTP_201_CREATED)
        else:
            return Response({"message":"User Does Not Exists"},status=status.HTTP_404_NOT_FOUND)

class CategoryListAPIView(generics.ListAPIView):
    queryset=api_model.Category.objects.filter(active=True)
    serializer_class=api_serializer.CategorySerializer
    permission_classes=[AllowAny]

class CourseListAPIView(generics.ListAPIView):
    queryset=api_model.Course.objects.filter(platform_status="Published", teacher_course_status="Published")
    serializer_class=api_serializer.CourseSerializer
    permission_classes=[AllowAny]

class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class=api_serializer.CourseSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        slug=self.kwargs['slug']
        course=api_model.Course.objects.get(slug=slug,platform_status="Published",teacher_course_status="Published")
        return course

class CartAPIView(generics.CreateAPIView):
    queryset=api_model.Cart.objects.all()
    serializer_class=api_serializer.CartSerializer
    permission_classes=[AllowAny]

    def create(self,request,*args,**Kwargs):
        course_id=request.data['course_id']
        user_id=request.data['user_id']
        price=request.data['price']
        country_name=request.data['country_name']
        cart_id=request.data['cart_id']

        course=api_model.Course.objects.filter(id=course_id).first()
        if user_id == "undefined":
            user=User.objects.filter(id=user_id).first()
        else:
            user=None

        try:
            country_object=api_model.Country.objects.filter(name=country_name).first()
            country=country_object.name

        except:
            country_object=None
            country="United States"

        if country_object:
            tax_rate=country_object.tax_rate / 100

        else:
            tax_rate=0
        
        cart=api_model.Cart.objects.filter(cart_id=cart_id,course=course).first()

        if cart:
            cart.course=course
            cart.user=user
            cart.price=price
            cart.tax_fee=Decimal(price) * Decimal(tax_rate)
            cart.country=country
            cart.cart_id=cart_id
            cart.total=Decimal(price) + Decimal(cart.tax_fee)
            cart.save()

            return Response({"message":"Cart Updated Successfully"},status=status.HTTP_200_OK)

        else:
            cart=api_model.Cart()

            cart.course=course
            cart.user=user
            cart.price=price
            cart.tax_fee=Decimal(price) * Decimal(tax_rate)
            cart.country=country
            cart.cart_id=cart_id
            cart.total=Decimal(price) + Decimal(cart.tax_fee)
            cart.save()

            return Response({"message":"Cart Created Successfully"},status=status.HTTP_201_CREATED)

