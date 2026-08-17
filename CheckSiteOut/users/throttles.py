from rest_framework.throttling import SimpleRateThrottle


class TokenPollThrottle(SimpleRateThrottle):
    scope = "login_throttle"

    def get_cache_key(self, request, view):
        token = request.query_params.get("token")
        ident = token or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
