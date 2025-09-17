from datetime import datetime

class LogIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log IP address
        ip = self.get_client_ip(request)
        print(f"\n🌐 [{datetime.now().strftime('%H:%M:%S')}] Connection from IP: {ip}")
        print(f"   Path: {request.path}")
        print(f"   Method: {request.method}")
        
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip