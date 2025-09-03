from rest_framework.throttling import UserRateThrottle

class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'

class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'

class PremiumUserRateThrottle(UserRateThrottle):
    """Higher rate limits for premium users"""
    
    def allow_request(self, request, view):
        if request.user.is_authenticated and request.user.is_premium:
            # Premium users get 10x the rate limit
            self.rate = '1000/hour'
        return super().allow_request(request, view)
