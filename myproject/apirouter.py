import importlib
from django.http import HttpRequest
from django.urls import include, path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class NestedApiRouter(APIView):
    name = 'Nested Api Root'

    def __init__(self, jwt_auth=False):
        self.jwt_auth = jwt_auth
        self.registered_apps = []
        self.added_urls = []
        super().__init__()

    def register_app(self, route, label: str):
        module, variable = label.split(':', 1)
        module = importlib.import_module(module)
        router = getattr(module, variable)
        self.added_urls.append(
            path(f"{route}/", include(router.urls))
        )
        if route not in self.registered_apps:
            self.registered_apps.append(route)

    def get(self, request: HttpRequest, registered_apps):
        res = dict()
        for app in registered_apps:
            res[app] = request.build_absolute_uri(f"{app}/")
        res['login'] = request.build_absolute_uri('token/')
        res['refresh'] = request.build_absolute_uri('token/refresh/')
        return Response(res)

    @property
    def urls(self):
        res = self.added_urls + [
            path('', self.as_view(), name='api-router', kwargs={
                'registered_apps': self.registered_apps
            }),
        ]
        if self.jwt_auth:
            res += [
                path(
                    'token/', TokenObtainPairView.as_view(),
                    name='token_obtain_pair'
                ),
                path(
                    'token/refresh/', TokenRefreshView.as_view(),
                    name='token_refresh'
                ),
            ]
        return res
