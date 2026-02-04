from django.db import models

class KategoriSepatu(models.Model):
    nama = models.CharField(max_length=100)
    gambar = models.ImageField(upload_to='kategori/', null=True, blank=True)
    
    def __str__(self):
        return self.nama

class Supplier(models.Model):
    nama = models.CharField(max_length=200)
    telepon = models.CharField(max_length=20)
    
    def __str__(self):
        return self.nama

class Barang(models.Model):
    nama_barang = models.CharField(max_length=200) 
    kategori = models.ForeignKey(KategoriSepatu, on_delete=models.CASCADE)
    stok = models.IntegerField(default=0)
    harga_beli = models.DecimalField(max_digits=12, decimal_places=2)
    gambar = models.ImageField(upload_to='sepatu/', null=True, blank=True)
    
    def __str__(self):
        return self.nama_barang

class TransaksiPembelian(models.Model):
    tanggal = models.DateTimeField(auto_now_add=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    total_harga = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"TRX-{self.id} | {self.supplier.nama}"

class DetailPembelian(models.Model):
    transaksi = models.ForeignKey(TransaksiPembelian, on_delete=models.CASCADE, related_name='details')
    barang = models.ForeignKey(Barang, on_delete=models.CASCADE)
    jumlah = models.IntegerField()
    harga_beli = models.DecimalField(max_digits=12, decimal_places=2)
    total_harga = models.DecimalField(max_digits=15, decimal_places=2)

class JurnalUmum(models.Model):
    tanggal = models.DateTimeField(auto_now_add=True)
    keterangan = models.CharField(max_length=255)
    akun = models.CharField(max_length=100)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    kredit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ref_transaksi = models.ForeignKey(TransaksiPembelian, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.akun} - {self.keterangan}"
