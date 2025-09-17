from importlib import import_module
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response 
from django.utils import timezone

app_name = 'base_app'

def get_serializer_class(model_name):
    module_name = 'base_app.serializers'  # Replace with your actual module name
    try:
        module = import_module(module_name)
        serializer_class_name = f"{model_name}Serializers"
        serializer_class = getattr(module, serializer_class_name, None)
        if serializer_class is None:
            raise AttributeError(f"Serializer '{serializer_class_name}' not found in module '{module_name}'")
        if not issubclass(serializer_class, serializers.Serializer):
            raise TypeError(f"'{serializer_class}' is not a valid serializer class")
        return serializer_class
    except ModuleNotFoundError:
        raise ImportError(f"Module '{module_name}' not found")
    except AttributeError as e:
        raise e
    except TypeError as e:
        raise e
    
def get_filtered_queryset(model_class, field=None, value=None, params=None):
    EXCLUDED_KEYS = ['page', 'per_page']
    if field and value:
        return model_class.objects.filter(**{field: value})
    elif params:
        filters = {}
        for k, v in params.items():
            if k in EXCLUDED_KEYS:
                continue
            if v:
                filters[f"{k}__in" if ',' in v else k] = v.split(',') if ',' in v else v
        return model_class.objects.filter(**filters)
    return model_class.objects.none()

class CustomPageNumberPagination(PageNumberPagination):
    page_size = None  # Disable default
    page_size_query_param = 'per_page'  # Allow user to set
    max_page_size = 1000  # Prevent abuse

    def get_paginated_response(self, data):
        return Response({
            'status': True,
            'data': data,
            'pagination': {
                'total_items': self.page.paginator.count,
                'current_page': self.page.number,
                'per_page': self.get_page_size(self.request),
                'total_pages': self.page.paginator.num_pages,
            }
        })
