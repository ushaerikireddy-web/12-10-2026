import time

from django.contrib import messages
from django.core.cache import caches
from django.shortcuts import redirect, render
from django.views import View

from .forms import ContactForm
from .models import AboutUs


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class AboutView(View):
    def get(self, request):
        about = AboutUs.objects.filter(is_published=True).order_by('-updated_at').first()
        return render(request, 'pages/about.html', {'about': about})


class ContactView(View):
    template_name = 'pages/contact.html'
    RATE_LIMIT = 5  # messages
    WINDOW = 3600  # per hour per IP

    def get(self, request):
        return render(request, self.template_name, {'form': ContactForm()})

    def post(self, request):
        form = ContactForm(request.POST)
        ip = _client_ip(request)
        cache = caches['default']
        key = f'contact:{ip}'
        history = cache.get(key, [])
        now = time.time()
        history = [t for t in history if now - t < self.WINDOW]
        if len(history) >= self.RATE_LIMIT:
            messages.error(request, 'Too many messages. Please try again later.')
            return render(request, self.template_name, {'form': form}, status=429)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ip_address = ip if '.' in (ip or '') or ':' in (ip or '') else None
            try:
                msg.save()
            except Exception:
                msg.ip_address = None
                msg.save()
            history.append(now)
            cache.set(key, history, self.WINDOW)
            messages.success(request, 'Thank you! Your message has been received.')
            return redirect('pages:contact-success')
        return render(request, self.template_name, {'form': form}, status=400)


class ContactSuccessView(View):
    def get(self, request):
        return render(request, 'pages/contact_success.html')
