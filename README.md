# 💰 TraceFund

**Pencatatan keuangan pribadi, langsung dari Discord.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?logo=docker&logoColor=white)

TraceFund adalah bot Discord untuk mencatat pemasukan dan pengeluaran dalam rupiah, memantau budget, serta meninjau laporan keuangan melalui slash command. Transaksi disimpan di SQLite agar catatan keuangan dapat dikelola tanpa layanan database terpisah. Akses dibatasi ke satu akun Discord yang dikonfigurasi, dan respons bot bersifat *ephemeral*, sehingga hanya pengguna yang menjalankan command yang dapat melihatnya.

## ✨ Fitur Utama

- **Pencatatan transaksi:** simpan pemasukan dan pengeluaran dengan nominal, deskripsi, dan tanggal otomatis.
- **Ringkasan bulanan dan tahunan:** lihat total pemasukan, pengeluaran, jumlah transaksi, dan saldo periode tertentu.
- **Analisis lintas bulan:** temukan bulan dengan pemasukan atau pengeluaran terbesar, serta saldo terbaik dan terburuk.
- **Pencarian pengeluaran:** hitung total berdasarkan potongan deskripsi, dengan filter bulan dan tahun.
- **Budget bulanan:** tetapkan batas pengeluaran dan periksa sisa atau kelebihan budget.
- **Pengelolaan transaksi:** lihat ID dan saldo berjalan, ubah nominal serta deskripsi, atau hapus melalui tombol konfirmasi.
- **Ekspor CSV:** unduh laporan transaksi dengan saldo berjalan dan encoding UTF-8 BOM.
- **Import Markdown:** bangun database transaksi dari catatan keuangan historis.
- **Backup otomatis:** buat salinan SQLite setiap startup bot dan simpan maksimal 30 backup terbaru.
- **Dukungan Docker Compose:** jalankan bot dengan database dan backup yang tersimpan di host.

## Tech Stack

| Teknologi | Peran |
| --- | --- |
| Python | Bahasa pemrograman; image Docker menggunakan Python 3.11 |
| `discord.py >=2.4,<3` | Discord client, slash command, dan tombol interaktif |
| `python-dotenv >=1.0,<2` | Membaca konfigurasi `.env` saat dijalankan lokal |
| SQLite / `sqlite3` | Menyimpan transaksi dan budget; tersedia dalam pustaka standar Python |
| Docker dan Docker Compose | Build image, menjalankan container, dan persistensi data |

## Prasyarat

- Git untuk meng-clone repository.
- Akun Discord, aplikasi bot, dan token bot.
- User ID Discord untuk akun yang diizinkan menggunakan bot.
- **Untuk menjalankan lokal:** Python 3.11 dan `pip`.
- **Untuk menjalankan dengan container:** Docker Engine atau Docker Desktop, serta Docker Compose v2.
- Koneksi internet agar bot dapat terhubung ke Discord.

## 🚀 Instalasi dan Setup

### 1. Clone repository

```bash
git clone https://github.com/Psr354/TraceFund.git
cd TraceFund
```

Jalankan perintah berikutnya dari direktori utama proyek agar konfigurasi dan data berada di lokasi yang sesuai.

### 2. Konfigurasi bot Discord

1. Buka [Discord Developer Portal](https://discord.com/developers/applications) dan buat atau pilih aplikasi bot.
2. Ambil token dari halaman **Bot**.
3. Di Discord, aktifkan **Developer Mode** melalui pengaturan **Advanced**, lalu salin **User ID** akun sendiri.
4. Buat file `.env` di direktori utama proyek:

```dotenv
DISCORD_TOKEN=isi_token_bot_anda
ALLOWED_USER_ID=123456789012345678
```

| Variabel | Wajib | Keterangan |
| --- | --- | --- |
| `DISCORD_TOKEN` | Ya | Token untuk login bot ke Discord |
| `ALLOWED_USER_ID` | Ya | ID numerik dari satu akun yang diizinkan menjalankan command |

Undang bot ke server menggunakan URL berikut. Ganti `APPLICATION_ID` dengan ID aplikasi dari Developer Portal:

```text
https://discord.com/oauth2/authorize?client_id=APPLICATION_ID&scope=bot%20applications.commands&permissions=0
```

Simpan token secara pribadi. `.env` sudah masuk `.gitignore`; jika token terpapar, reset token dan perbarui konfigurasi.

### 3. Jalankan lokal

**Windows PowerShell:**

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

**Linux, macOS, atau WSL** dengan Python 3.11 tersedia:

```bash
python3.11 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Bot membuat tabel database dan backup saat startup, lalu menyinkronkan slash command. Log `Bot online sebagai ...` menandakan bot berhasil terhubung. Hentikan proses dengan `Ctrl+C` dan keluar dari virtual environment menggunakan `deactivate`.

### Alternatif: jalankan dengan Docker Compose

Siapkan `.env` seperti langkah sebelumnya. Jika `tracefund.db` belum ada, buat file kosong sebelum menjalankan Compose agar bind mount diperlakukan sebagai file.

**Windows PowerShell:**

```powershell
if (-not (Test-Path -LiteralPath .\tracefund.db)) {
    New-Item -ItemType File -Path .\tracefund.db
}
docker compose up -d --build
```

**Linux, macOS, atau WSL:**

```bash
touch tracefund.db
docker compose up -d --build
```

Periksa status dan log:

```bash
docker compose ps
docker compose logs -f tracefund
```

Perintah operasional:

```bash
# Restart bot
docker compose restart tracefund

# Terapkan perubahan kode dengan build ulang
docker compose up -d --build

# Hentikan dan hapus container; data tetap tersimpan di host
docker compose down
```

Konfigurasi `restart: unless-stopped` membuat container dimulai ulang otomatis kecuali dihentikan secara manual.

## 📖 Cara Penggunaan

Di Discord, ketik `/` dan pilih command TraceFund dari autocomplete. Isi parameter melalui formulir slash command; contoh berikut menunjukkan nama command dan nilai parameternya.

### Alur penggunaan sederhana

```text
/pemasukan nominal:500000 deskripsi:freelance
/pengeluaran nominal:25000 barang:makan siang
/ringkasan
/budget nominal:1000000
/cekbudget
```

Nominal berupa bilangan bulat dalam rupiah, lebih besar dari nol, tanpa pemisah ribuan. Gunakan `25000` untuk Rp25.000.

### Referensi command

| Command | Fungsi | Contoh |
| --- | --- | --- |
| `/pemasukan` | Catat pemasukan baru | `/pemasukan nominal:500000 deskripsi:gaji` |
| `/pengeluaran` | Catat pengeluaran baru | `/pengeluaran nominal:50000 barang:bensin` |
| `/ringkasan` | Ringkasan bulanan | `/ringkasan bulan:8 tahun:2025` |
| `/total` | Total dan detail pengeluaran; nama barang opsional | `/total barang:bensin tahun:2025` |
| `/analisis` | Analisis seluruh bulan yang memiliki transaksi | `/analisis` |
| `/tahunan` | Ringkasan tahunan | `/tahunan tahun:2025` |
| `/riwayat` | Daftar transaksi dengan ID dan saldo berjalan | `/riwayat bulan:8 tahun:2025` |
| `/export` | Unduh transaksi sebagai CSV | `/export tahun:2025` |
| `/ubah` | Ubah nominal dan deskripsi berdasarkan ID | `/ubah id_transaksi:1 nominal:30000 deskripsi:makan siang` |
| `/hapus` | Hapus transaksi setelah konfirmasi tombol | `/hapus id_transaksi:1` |
| `/budget` | Tetapkan atau perbarui budget bulanan | `/budget nominal:1000000 bulan:8 tahun:2025` |
| `/cekbudget` | Lihat pemakaian dan sisa budget bulanan | `/cekbudget bulan:8 tahun:2025` |

Gunakan ID yang tampil pada `/riwayat` saat mengubah atau menghapus transaksi. `/ubah` mempertahankan tanggal dan jenis transaksi.

### Periode dan perhitungan

- `bulan` menerima angka **1–12** dan `tahun` menerima **2000–2100**.
- `/ringkasan`, `/budget`, dan `/cekbudget` menggunakan bulan serta tahun berjalan untuk parameter yang dikosongkan.
- `/tahunan` menggunakan tahun berjalan jika `tahun` dikosongkan.
- `/total` tanpa periode mencari seluruh pengeluaran; `barang` dicocokkan sebagai potongan teks deskripsi tanpa membedakan huruf besar dan kecil. Kategori tidak dikelompokkan otomatis.
- `/riwayat` dengan filter menampilkan seluruh transaksi yang cocok. Tanpa filter, implementasi saat ini mengambil maksimal **15 transaksi paling awal**, meskipun label respons menyebut transaksi terakhir.
- `/export` tanpa parameter mengekspor bulan berjalan; hanya `tahun` mengekspor satu tahun penuh.
- Untuk `/total`, `/riwayat`, dan `/export`, hanya `bulan` memakai tahun berjalan; hanya `tahun` mencakup seluruh tahun tersebut.
- Saldo ringkasan adalah pemasukan dikurangi pengeluaran pada periode yang dipilih. Saldo berjalan pada riwayat dan CSV dihitung dari seluruh transaksi, menurut tanggal lalu ID.

Tanggal pencatatan dan periode berjalan mengikuti waktu lokal sistem yang menjalankan bot. Tidak ada konfigurasi zona waktu khusus di aplikasi.

## Import Data Historis

`seed_db.py` membaca file `.md` langsung dari folder sumber. Nama file harus mengikuti pola `<nama bulan> <tahun>.md`, misalnya `Agustus 2025.md`.

Contoh isi file:

```markdown
pemasukan:
500K
150K

pengeluaran:
bensin: 40K
makan: 22,5K
```

Importer mendukung nama bulan Indonesia serta `December`, nominal berakhiran `K` atau `k`, desimal berkoma, tag HTML sederhana, dan label `pengeluran`. Transaksi diberi tanggal **hari pertama bulan tersebut pukul 12.00**, dan deskripsi pemasukan menjadi `Pemasukan`.

Jalankan menggunakan Python dari direktori utama proyek:

```bash
python seed_db.py --source-dir "./data-historis"
```

> **Perhatian:** importer menghapus seluruh isi tabel `transactions` sebelum memasukkan hasil import. Hentikan bot dan salin `tracefund.db` sebagai backup sebelum menjalankannya pada database yang sudah berisi data. Importer tidak membuat backup otomatis dan tidak mengubah tabel budget.

## Penyimpanan dan Backup

| Lokasi | Isi |
| --- | --- |
| `tracefund.db` | Database SQLite dengan tabel `transactions` dan `budgets` |
| `backups/tracefund-YYYYMMDD-HHMMSS.db` | Salinan database saat startup bot |

Docker Compose memasang `./tracefund.db` ke `/app/tracefund.db` dan `./backups` ke `/app/backups`. Data tetap tersedia setelah container dihentikan atau image dibangun ulang selama file dan folder di host dipertahankan.

Backup dibuat setiap startup, bukan secara berkala, dengan retensi maksimal 30 file `.db` terbaru di folder `backups/`. Untuk memulihkan data, hentikan bot, simpan salinan database saat ini, ganti `tracefund.db` dengan backup yang dipilih, lalu jalankan bot kembali.

## Struktur Proyek

```text
TraceFund/
├── main.py              # Bot, slash command, database, dan backup
├── seed_db.py           # Import catatan Markdown ke SQLite
├── requirements.txt     # Dependensi Python
├── Dockerfile           # Image bot berbasis Python 3.11
├── docker-compose.yml   # Service, environment, dan volume
├── .gitignore           # Pengecualian konfigurasi dan data lokal
├── README.md            # Dokumentasi proyek
├── .env                 # Konfigurasi lokal; tidak dilacak Git
├── tracefund.db         # Database runtime; tidak dilacak Git
└── backups/             # Dibuat saat startup; tidak dilacak Git
```

## Troubleshooting

| Gejala | Langkah pemeriksaan |
| --- | --- |
| Bot gagal startup | Pastikan `DISCORD_TOKEN` terisi dan `ALLOWED_USER_ID` berupa angka. Untuk Docker, periksa `docker compose logs --tail=100 tracefund`. |
| Akses command ditolak | Cocokkan `ALLOWED_USER_ID` dengan User ID akun yang menjalankan command. |
| Slash command tidak muncul | Pastikan undangan menyertakan scope `applications.commands`, periksa log sinkronisasi, lalu muat ulang Discord. |
| Command terkirim sebagai teks biasa | Pilih command dari autocomplete setelah mengetik `/`. |
| SQLite gagal dibuka dalam Docker | Pastikan `tracefund.db` di host berupa file, bukan direktori, dan volume sesuai konfigurasi Compose. |
| Data tidak ditemukan setelah restart | Periksa lokasi database dan jalankan aplikasi dari direktori proyek yang sama. |
| Import Markdown gagal | Periksa path folder, ekstensi `.md`, pola nama file, dan encoding UTF-8. |

## Berkontribusi

1. Fork repository dan buat branch untuk perubahan yang terfokus.
2. Siapkan environment lokal sesuai panduan instalasi.
3. Terapkan perubahan dan perbarui dokumentasi jika perilaku command berubah.
4. Periksa sintaks Python dan, jika mengubah deployment, konfigurasi Compose:

   ```bash
   python -m py_compile main.py seed_db.py
   docker compose config --quiet
   ```

5. Verifikasi command yang terdampak menggunakan bot dan database pengembangan sendiri.
6. Buka pull request dengan penjelasan perubahan serta hasil verifikasi.

Sebelum commit, periksa `git status --short`. Jangan sertakan `.env`, database, backup, atau data keuangan pribadi.

## Kontak

Repository dikelola melalui akun GitHub [Psr354](https://github.com/Psr354). Untuk pertanyaan, laporan masalah, atau usulan fitur, gunakan [Issues TraceFund](https://github.com/Psr354/TraceFund/issues).
