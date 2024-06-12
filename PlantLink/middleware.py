class XFrameOptionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = "frame-ancestors 'self' https://921c-2001-d08-1810-5077-29e4-1c1b-a3bc-a094.ngrok-free.app/"  # Adjust the port if necessary
        return response
