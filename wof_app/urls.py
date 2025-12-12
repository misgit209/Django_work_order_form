from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/get_tr_item_codes/", views.get_tr_item_codes, name="get_tr_item_codes"),
    path("api/get_line_name/", views.get_line_name, name="get_line_name"),
    path("api/get_operation_name/", views.get_operation_name, name="get_operation_name"),
    path("api/get_employee_name/", views.get_employee_name, name="get_employee_name"),
]
