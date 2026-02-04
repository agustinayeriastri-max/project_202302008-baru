from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Sum
from xhtml2pdf import pisa
from datetime import datetime
from django.utils import timezone 

# Import model dari app penjualan
from penjualan.models import (
    KategoriSepatu, Supplier, Barang, 
    TransaksiPembelian, DetailPembelian, JurnalUmum
)

def welcome_page(request):
    return render(request, 'pembelian/welcome.html')

def dashboard(request):
    context = {
        'total_barang': Barang.objects.count(), 
        'total_supplier': Supplier.objects.count(),
        'total_transaksi': TransaksiPembelian.objects.count(),
        'total_pembelian': TransaksiPembelian.objects.aggregate(Sum('total_harga'))['total_harga__sum'] or 0,
        'barang_menipis': Barang.objects.filter(stok__lt=5),
    }
    return render(request, 'pembelian/dashboard.html', context)

# --- KATEGORI ---
def kategori_list(request):
    kategori = KategoriSepatu.objects.all()
    return render(request, 'pembelian/kategori_list.html', {'kategori': kategori})

def tambah_kategori(request):
    if request.method == 'POST':
        isi_nama = request.POST.get('nama_kategori') 
        if isi_nama:
            KategoriSepatu.objects.create(nama=isi_nama)
            return redirect('penjualan:kategori_list')
    return render(request, 'pembelian/tambah_kategori.html')

def hapus_kategori(request, id):
    obj = get_object_or_404(KategoriSepatu, id=id)
    obj.delete()
    return redirect('penjualan:kategori_list')

# --- BARANG ---
def barang_per_kategori(request, id):
    kategori_obj = get_object_or_404(KategoriSepatu, id=id)
    semua_barang = Barang.objects.filter(kategori=kategori_obj)
    context = {'kategori': kategori_obj, 'semua_barang': semua_barang}
    return render(request, 'pembelian/barang_per_kategori.html', context)

def edit_barang(request, id):
    barang = get_object_or_404(Barang, id=id)
    kategori_list = KategoriSepatu.objects.all()
    if request.method == 'POST':
        barang.nama_barang = request.POST.get('nama_barang')
        barang.stok = request.POST.get('stok')
        barang.harga_beli = request.POST.get('harga_beli')
        id_kat = request.POST.get('kategori')
        if id_kat:
            barang.kategori = get_object_or_404(KategoriSepatu, id=id_kat)
        barang.save()
        return redirect('penjualan:barang_per_kategori', id=barang.kategori.id)
    return render(request, 'pembelian/edit_barang.html', {'barang': barang, 'kategori_list': kategori_list})

def hapus_barang(request, id):
    barang = get_object_or_404(Barang, id=id)
    id_kategori = barang.kategori.id
    barang.delete()
    return redirect('penjualan:barang_per_kategori', id=id_kategori)

# --- TRANSAKSI (RESTOCK) ---
def list_transaksi(request):
    transaksi_list = TransaksiPembelian.objects.all().order_by('-id')
    return render(request, 'pembelian/list_transaksi.html', {'transaksi_list': transaksi_list})

def detail_transaksi(request, id):
    transaksi = get_object_or_404(TransaksiPembelian, id=id)
    return render(request, 'pembelian/detail_transaksi.html', {'transaksi': transaksi})

def tambah_transaksi(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        barang_id = request.POST.get('barang')
        jumlah = int(request.POST.get('jumlah', 0))
        harga_input = float(request.POST.get('harga_beli', 0))
        total = jumlah * harga_input

        supplier_obj = get_object_or_404(Supplier, id=supplier_id)
        barang_obj = get_object_or_404(Barang, id=barang_id)
        
        transaksi = TransaksiPembelian.objects.create(supplier=supplier_obj, total_harga=total)

        DetailPembelian.objects.create(
            transaksi=transaksi, 
            barang=barang_obj, 
            jumlah=jumlah, 
            harga_beli=harga_input,
            total_harga=total
        )
        
        barang_obj.stok += jumlah
        barang_obj.save()

        # Posting ke Jurnal
        JurnalUmum.objects.create(
            keterangan=f"Restock {barang_obj.nama_barang}",
            akun="Persediaan Barang",
            debit=total,
            kredit=0,
            ref_transaksi=transaksi
        )
        JurnalUmum.objects.create(
            keterangan=f"Restock {barang_obj.nama_barang}",
            akun="Kas",
            debit=0,
            kredit=total,
            ref_transaksi=transaksi
        )
        return redirect('penjualan:list_transaksi')
    
    context = {
        'suppliers': Supplier.objects.all(), 
        'barangs': Barang.objects.all()
    }
    return render(request, 'pembelian/tambah_barang.html', context)

def hapus_transaksi(request, id):
    transaksi = get_object_or_404(TransaksiPembelian, id=id)
    transaksi.delete()
    return redirect('penjualan:list_transaksi')

# --- JURNAL & LAPORAN ---
def jurnal_list(request):
    jurnal = JurnalUmum.objects.all().order_by('id')
    return render(request, 'pembelian/jurnal_list.html', {'jurnal': jurnal})

def laporan_pembelian(request):
    data_laporan = DetailPembelian.objects.all().order_by('-transaksi__tanggal')
    total = TransaksiPembelian.objects.aggregate(Sum('total_harga'))['total_harga__sum'] or 0
    
    context = {
        'detail_list': data_laporan, 
        'total': total
    }
    return render(request, 'pembelian/laporan_pembelian.html', context)

def cetak_pdf(request):
    detail_list = DetailPembelian.objects.all().order_by('-transaksi__tanggal')
    total = TransaksiPembelian.objects.aggregate(Sum('total_harga'))['total_harga__sum'] or 0
    context = {
        'detail_list': detail_list, 
        'total': total, 
        'now': datetime.now()
    }
    response = HttpResponse(content_type='application/pdf')
    
    # PERUBAHAN DI SINI: 'inline' agar PDF terbuka langsung di browser
    response['Content-Disposition'] = 'inline; filename="laporan_restock.pdf"'
    
    template = get_template('pembelian/laporan_pdf.html')
    html = template.render(context)
    
    # Membuat PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # Cek jika terjadi error
    if pisa_status.err:
        return HttpResponse('Gagal membuat PDF', status=500)
        
    return response
