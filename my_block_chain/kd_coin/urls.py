from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('receive_transaction', views.receive_transaction, name='receive_transaction'),
    path('receive_nonce', views.receive_nonce, name='receive_nonce'),
    path('loop', views.loop, name='loop'),
    path('test', views.test, name='test'),
    
]