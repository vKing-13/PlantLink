class XFrameOptionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = "frame-ancestors 'self' http://localhost:8000 https://cdd8-161-139-102-62.ngrok-free.app"  # Adjust the port if necessary
        return response
