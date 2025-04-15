# Add this to a file called middleware.py in your recipesharing directory

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code executed before view
        print(f"Request headers: {request.headers}")
        response = self.get_response(request)
        # Code executed after view
        if response.status_code == 400:
            print(f"400 error response: {response.content}")
        return response