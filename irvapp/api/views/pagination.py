from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FastAPIPagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "size"
    page_size = 50

    def get_paginated_response(self, data):
        page_size = (
            self.get_page_size(self.request)
            or self.page.paginator.per_page
        )
        return Response(
            {
                "items": data,
                "total": self.page.paginator.count,
                "page": self.page.number,
                "size": page_size,
                "pages": self.page.paginator.num_pages,
            }
        )
