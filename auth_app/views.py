import json
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from django.conf import settings
from django.contrib.auth.models import User, auth
from django.core.mail import EmailMessage

import jwt

from logging_config.logger import get_logger
from auth_app.serializers import LoginSerializer, RegisterSerializer, UsernameSerializer
from auth_app.utils import get_object_by_id, get_object_by_username, set_cache, get_cache
# from auth_app.send import send_data_to_queue

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Logger configuration
logger = get_logger()


class LoginAPIView(APIView):
    """
        Login API View : LoginSerializer, create token, authenticate user, set cache
    """
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="username"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description="password")
        }
    ))
    def post(self, request):
        """
            This method is used for login authentication.
            :param request: It's accept username and password as parameter.
            :return: It's return response that login is successfull or not.
        """
        try:
            # Login serializer
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Create token
            token = jwt.encode({'username': serializer.data.get('username')}, settings.SECRET_KEY, algorithm='HS256')
            # Authenticate username & password
            user = auth.authenticate(username=serializer.data.get('username'), password=serializer.data.get('password'))
            if user is not None:
                # Set cache
                # set_cache('username', serializer.data.get('username'))
                # Login successfull
                return Response({'success': True, 'message': 'Login successfull!', 'data' : {'username': serializer.data.get('username'), 'token': token}}, status=status.HTTP_200_OK)
            else:
                # Login failed
                return Response({'success': False, 'message': 'Login failed!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            logger.exception(e)
            return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'Oops! Something went wrong! Please try again...'}, status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    """
        Register API View : RegisterSerializer, check email & username already exist or not, create new user
    """
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="first name"),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="last name"),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description="email"),
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="username"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description="password")
        }
    ))
    def post(self, request):
        """
            This method is used to create new user instance.
            :param request: It's accept first_name, last_name, email, username and password as parameter.
            :return: It's return response that user created successfully or not.
        """
        try:
            # Register serializer
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Check given email is already registered or not
            if User.objects.filter(email=serializer.data.get('email')).exists():
                return Response({'success': False, 'message': 'Gven email is already registered.', 'data': {'email': serializer.data.get('email')}}, status=status.HTTP_400_BAD_REQUEST)
            # Check given username is already taken or not
            if User.objects.filter(username=serializer.data.get('username')).exists():
                return Response({'success': False, 'message': 'Gven username is already taken', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_400_BAD_REQUEST)
            # Create user instance
            user = User.objects.create_user(first_name=serializer.data.get('first_name'), last_name=serializer.data.get('last_name'), email=serializer.data.get('email'), username=serializer.data.get('username'), password=serializer.data.get('password'))
            # Send data to queue
            # json_data = json.dumps({'username': serializer.data.get('username'), 'user_email': serializer.data.get('email'), 'SECRET_KEY': settings.SECRET_KEY, 'EMAIL_HOST_USER': settings.EMAIL_HOST_USER})
            # send_data_to_queue(data=json_data)
            # Make user as not active
            # user.is_active = False
            user.save()
            # User registration successfull
            return Response({'success': True, 'message': 'Registration successfull!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_200_OK)
        except ValidationError as e:
            logger.exception(e)
            return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'Oops! Something went wrong! Please try again...'}, status=status.HTTP_400_BAD_REQUEST)


class ResetUsernameAPIView(APIView):
    """
        Reset Username API View : UsernameSerializer, reset username
    """
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="user id"),
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="new username")
        }
    ))
    def put(self, request):
        """
            This method is used to update username of user instance.
            :param request: It's accept id, username as parameter.
            :return: It's return response that username successfully updated or not.
        """
        try:
            # Username serializer
            serializer = UsernameSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Get user instance according to id
            user = get_object_by_id(request.data.get('id'))
            # Reset username
            user.username = serializer.data.get('username')
            user.save()
            # User name updated successfully
            return Response({'success': True, 'message': 'Reset username successfully!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_200_OK)
        except User.DoesNotExist as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'User does not exist!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            logger.exception(e)
            return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'Oops! Something went wrong! Please try again...'}, status=status.HTTP_400_BAD_REQUEST)
    

class ResetPasswordAPIView(APIView):
    """
        Reset Password API View : LoginSerializer, reset password
    """
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="username"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description="new password")
        }
    ))
    def put(self, request):
        """
            This method is used to reset password for a user instance.
            :param request: It's accept username and password as parameter.
            :return: It's return response that password is updated or not.
        """
        try:
            # Login serializer
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Get user instance according to username
            user = get_object_by_username(serializer.data.get('username'))
            # Reset password
            user.set_password(serializer.data.get('password'))
            user.save()
            # Password reseted successfully
            return Response({'success': True, 'message': 'Reset password successfully!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_200_OK)
        except User.DoesNotExist as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'User does not exist!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            logger.exception(e)
            return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'Oops! Something went wrong! Please try again...'}, status=status.HTTP_400_BAD_REQUEST)
    

class UserDeleteAPIView(APIView):
    """
        User Delete API View : UsernameSerializer, delete user instance
    """
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="username")
        }
    ))
    def delete(self, request):
        """
            This method is used to delete user instance.
            :param request: It's accept username as parameter.
            :return: It's return that user is successfully deleted or not.
        """
        try:
            # Username serializer
            serializer = UsernameSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Get user instance according to username
            user = get_object_by_username(serializer.data.get('username'))
            # Delete user instance
            user.delete()
            # User deleted successfully
            return Response({'success': True, 'message': 'User deleted successfully!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_200_OK)
        except User.DoesNotExist as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'User does not exist!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            logger.exception(e)
            return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'Oops! Something went wrong! Please try again...'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailAPIView(APIView):
    """
        VerifyEmailAPIView : Token, decode token, activate user
    """
    def get(self, request, *args,**kwargs):
        try:
            # Getting token from URL
            token = kwargs['token']
            # Decode token
            data = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            # Get user
            user = get_object_by_username(data.get('username'))
            # Set user as active
            user.is_active = True
            user.save()
            # User activated successfully
            return Response({'success': True, 'message': 'Account activated successfully!', 'data': {'username': data.get('username')}}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'Oops! Something went wrong! Please try again...'}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordAPIView(APIView):
    """
        ForgotPasswordAPIView: 
    """
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="username")
        }
    ))
    def post(self, request):
        try:
            # Username serializer
            serializer = UsernameSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Get user instance according to username
            user = get_object_by_username(serializer.data.get('username'))
            # Extract email
            user_email = user.email
            # Reset password link
            reset_password_link = 'http://127.0.0.1:4200/reset-password'
            # Sending activation mail
            email = EmailMessage(
                'Reset your account password', # Subject
                'Please click this link to reset your account password: ' + reset_password_link, # Body
                settings.EMAIL_HOST_USER, # From
                [user_email], # To
            )
            email.send(fail_silently=False)
            return Response({'success': True, 'message': 'Email sended successfully for reset password!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_200_OK)
        except User.DoesNotExist as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'User does not exist!', 'data': {'username': serializer.data.get('username')}}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            logger.exception(e)
            return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(e)
            return Response({'success': False, 'message': 'Oops! Something went wrong! Please try again...'}, status=status.HTTP_400_BAD_REQUEST)
