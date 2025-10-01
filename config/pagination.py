"""
Custom pagination classes for the project
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination with configurable page size
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100  # Permette al client di richiedere fino a 100 elementi
