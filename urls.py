from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Tambahkan ini
from django.conf.urls.static import static # Tambahkan ini

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('penjualan.urls')),
]

# Konfigurasi agar file media/gambar bisa diakses saat DEBUG=True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)