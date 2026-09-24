# TraceFund

TraceFund adalah bot Discord untuk pencatatan keuangan pribadi menggunakan Python, `discord.py`, SQLite, dan Docker.

Bot hanya dapat digunakan oleh satu Discord user yang ID-nya ditentukan melalui `ALLOWED_USER_ID`. Semua jawaban bot menggunakan ephemeral response, sehingga hanya user yang menjalankan command yang dapat melihat hasilnya.

## Daftar Command

| Command | Fungsi |
|---|---|
| `/pemasukan` | Mencatat pemasukan |
| `/pengeluaran` | Mencatat pengeluaran |
| `/ringkasan` | Melihat pemasukan, pengeluaran, dan saldo suatu bulan |
| `/total` | Menghitung total pengeluaran berdasarkan nama barang/kategori |
| `/analisis` | Menganalisis seluruh bulan |
| `/tahunan` | Melihat total pemasukan dan pengeluaran dalam satu tahun |
| `/riwayat` | Melihat transaksi terakhir |
| `/export` | Mengunduh laporan transaksi CSV |
| `/ubah` | Mengubah transaksi berdasarkan ID |
| `/hapus` | Menghapus transaksi berdasarkan ID |
| `/budget` | Menetapkan budget pengeluaran bulanan |
| `/cekbudget` | Melihat pemakaian budget |

## Cara Memulai

### 1. Siapkan file `.env`

Buat file `.env` di folder utama project:

```env
DISCORD_TOKEN=token_bot_discord
ALLOWED_USER_ID=123456789012345678
```

Jangan tambahkan tanda kutip dan jangan membagikan nilai `DISCORD_TOKEN`.

### 2. Mendapatkan `DISCORD_TOKEN`

1. Buka <https://discord.com/developers/applications>.
2. Pilih aplikasi TraceFund.
3. Buka menu **Bot**.
4. Klik **Reset Token** atau **Copy Token**.
5. Masukkan token ke `.env`.

Jika token pernah tersebar, segera lakukan **Reset Token** dan perbarui `.env`.

### 3. Mendapatkan `ALLOWED_USER_ID`

1. Buka Discord.
2. Masuk ke **User Settings > Advanced**.
3. Aktifkan **Developer Mode**.
4. Klik kanan nama/avatar akun sendiri.
5. Pilih **Copy User ID**.
6. Masukkan angka tersebut ke `.env`.

### 4. Invite bot ke server

Ambil **Application ID** dari menu **General Information**, lalu ganti `APPLICATION_ID` pada URL berikut:

```text
https://discord.com/oauth2/authorize?client_id=APPLICATION_ID&scope=bot%20applications.commands&permissions=0
```

Scope yang wajib digunakan:

- `bot`
- `applications.commands`

Bot tidak membutuhkan permission khusus untuk command ini, sehingga `permissions=0` cukup.

## Format Bulan dan Tahun

Semua command yang menerima bulan menggunakan angka:

```text
1  Januari
2  Februari
3  Maret
4  April
5  Mei
6  Juni
7  Juli
8  Agustus
9  September
10 Oktober
11 November
12 Desember
```

Parameter `bulan` dan `tahun` biasanya bersifat opsional.

- Tanpa bulan/tahun: memakai bulan dan tahun saat ini.
- Dengan `bulan` dan `tahun`: melihat periode tertentu.
- Dengan hanya `tahun`: melihat seluruh bulan pada tahun tersebut, jika command mendukungnya.

Contoh tanggal tertentu:

```text
bulan:8 tahun:2025
```

Artinya Agustus 2025, bukan tahun berjalan.

## Panduan Semua Command

### `/pemasukan`

Mencatat pemasukan baru.

```text
/pemasukan nominal:150000 deskripsi:uang freelance
```

Keterangan:

- `nominal` ditulis dalam rupiah tanpa titik atau koma.
- `deskripsi` adalah sumber pemasukan.
- Tanggal otomatis memakai tanggal saat command dijalankan.

Contoh lain:

```text
/pemasukan nominal:500000 deskripsi:gaji
/pemasukan nominal:75000 deskripsi:jualan barang
```

### `/pengeluaran`

```text
/pengeluaran nominal:25000 barang:makan
```

Contoh:

```text
/pengeluaran nominal:50000 barang:bensin
/pengeluaran nominal:30000 barang:data
/pengeluaran nominal:25000 barang:cukur
```

Nominal harus lebih besar dari 0.

### `/ringkasan`

Melihat total pemasukan, total pengeluaran, jumlah transaksi, dan saldo.

Bulan berjalan:

```text
/ringkasan
```

Agustus 2025:

```text
/ringkasan bulan:8 tahun:2025
```

September 2024:

```text
/ringkasan bulan:9 tahun:2024
```

Saldo dihitung dengan rumus:

```text
saldo = total pemasukan - total pengeluaran
```

### `/total`

Menghitung total pengeluaran berdasarkan teks yang terdapat di deskripsi barang. Pencarian tidak membedakan huruf besar dan kecil.

```text
/total barang:cukur
```

Command tersebut dapat menemukan deskripsi seperti:

```text
cukur
Cukur
cukur rambut
biaya cukur
```

Contoh lain:

```text
/total barang:bensin
/total barang:jajan
```

`/total barang:bensin` dapat menemukan `bensin`, `Bensin`, `bensin motor`, atau `isi bensin`.

Hasil command juga menampilkan daftar lengkap semua transaksi yang cocok, termasuk ID, tanggal, nominal, dan deskripsi. Jika hasilnya panjang, daftar dibagi menjadi beberapa pesan ephemeral.

Sepanjang seluruh riwayat:

```text
/total barang:bensin
```

Untuk tahun tertentu:

```text
/total barang:bensin tahun:2025
```

Untuk bulan dan tahun tertentu:

```text
/total barang:bensin bulan:8 tahun:2025
```

Catatan: sistem saat ini mencari berdasarkan kata di deskripsi. Sistem belum otomatis menganggap `bensin`, `transport`, dan `ojek` sebagai satu kategori.

### `/analisis`

Menganalisis seluruh bulan yang tersedia di database.

```text
/analisis
```

Hasilnya mencakup:

- Bulan dengan pemasukan terbesar.
- Bulan dengan pengeluaran terbesar.
- Bulan dengan saldo terbaik.
- Bulan dengan saldo terburuk.
- Detail pemasukan setiap bulan.
- Detail pengeluaran setiap bulan.
- Detail saldo setiap bulan.

Jika detailnya panjang, bot membaginya menjadi beberapa pesan ephemeral agar tidak melewati batas panjang pesan Discord.

### `/tahunan`

Melihat total pemasukan dan pengeluaran dalam satu tahun, termasuk jumlah transaksi dan saldo tahunan.

Tahun berjalan:

```text
/tahunan
```

Tahun historis:

```text
/tahunan tahun:2025
/tahunan tahun:2024
```

Saldo tahunan dihitung dengan rumus:

```text
saldo tahunan = total pemasukan setahun - total pengeluaran setahun
```

### `/riwayat`

Tanpa filter, melihat maksimal 15 transaksi terakhir beserta ID transaksi:

```text
/riwayat
```

Dengan filter bulan dan tahun, semua transaksi pada bulan tersebut ditampilkan, termasuk pemasukan, pengeluaran, total, dan saldo:

```text
/riwayat bulan:8 tahun:2025
```

Contoh melihat semua transaksi Agustus 2025:

```text
/riwayat bulan:8 tahun:2025
```

Filter berdasarkan tahun untuk melihat semua transaksi dalam satu tahun:

```text
/riwayat tahun:2025
```

Jika detail terlalu panjang, bot membaginya menjadi beberapa pesan ephemeral.

Setiap baris transaksi juga menampilkan saldo berjalan setelah transaksi tersebut.

Contoh hasil:

```text
#518 2026-09-23 | keluar | Rp25.000 | makan
```

ID tersebut dapat digunakan untuk `/ubah` atau `/hapus`.

### `/ubah`

Mengubah nominal dan deskripsi transaksi berdasarkan ID dari `/riwayat`.

```text
/ubah id_transaksi:518 nominal:30000 deskripsi:makan siang
```

Tanggal dan jenis transaksi tetap sama. Hanya nominal dan deskripsi yang diubah.

### `/hapus`

Menghapus transaksi berdasarkan ID.

```text
/hapus id_transaksi:518
```

Gunakan `/riwayat` terlebih dahulu untuk memastikan ID yang benar.

Bot akan meminta konfirmasi tombol sebelum penghapusan dilakukan.

### `/export`

Mengunduh transaksi dalam file CSV. Tanpa parameter, command ini mengekspor bulan berjalan:

```text
/export
```

Untuk bulan tertentu:

```text
/export bulan:5 tahun:2026
```

Untuk satu tahun:

```text
/export tahun:2025
```

File berisi ID, tanggal, tipe transaksi, nominal, deskripsi, dan saldo berjalan.

### Backup database

Bot membuat backup database otomatis setiap kali container mulai dan menyimpan maksimal 30 backup terbaru di folder `backups/`. Folder tersebut dipasang sebagai volume Docker agar backup tetap ada saat image dibuat ulang.

### `/budget`

Menetapkan batas pengeluaran bulanan.

Budget bulan berjalan:

```text
/budget nominal:1000000
```

Budget Agustus 2025:

```text
/budget nominal:1500000 bulan:8 tahun:2025
```

Jika budget untuk bulan yang sama sudah ada, command ini akan memperbarui nilainya.

### `/cekbudget`

Melihat budget, jumlah pengeluaran, dan sisa atau kelebihan budget.

Bulan berjalan:

```text
/cekbudget
```

Bulan tertentu:

```text
/cekbudget bulan:8 tahun:2025
```

Contoh hasil:

```text
Batas: Rp1.000.000
Terpakai: Rp750.000
Tersisa: Rp250.000
```

Budget tersimpan berdasarkan `tahun-bulan`, sehingga budget bulan baru tidak tercampur dengan bulan sebelumnya.

## Import Data Historis

Seeder membaca file Markdown transaksi dari folder lampiran. Format yang didukung antara lain:

```text
pemasukan:
50K
150K

pengeluaran:
 bensin: 40K
 jajan: 25K
```

Seeder juga menangani:

- Nama bulan Indonesia dan `December`.
- Nominal `K` atau `k`.
- Nominal desimal seperti `22,5K`.
- Tag HTML sederhana seperti `<br/>` dan `&nbsp;`.
- Typo label `pengeluran`.

Jalankan dari Windows PowerShell:

```powershell
python seed_db.py --source-dir "C:\Users\BEST LAPTOP\Downloads\pengeluaran uang"
```

Jalankan dari WSL:

```bash
python seed_db.py --source-dir "/mnt/c/Users/BEST LAPTOP/Downloads/pengeluaran uang"
```

**Penting:** seeder menghapus isi tabel `transactions` lalu mengimpor ulang semua file. Jangan menjalankannya setelah bot sudah memiliki transaksi baru kecuali memang ingin membangun ulang database dari file Markdown.

## Local Development di WSL

```bash
cd /mnt/c/tracefund
python3.11 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Jika muncul `Bot online sebagai ...`, bot berhasil terhubung ke Discord.

Untuk keluar dari virtual environment:

```bash
deactivate
```

## Docker Local

Pastikan Docker Desktop atau Docker Engine aktif.

Build image:

```bash
docker compose build
```

Jalankan bot:

```bash
docker compose up -d
```

Cek status:

```bash
docker compose ps
```

Lihat log langsung:

```bash
docker compose logs -f tracefund
```

Restart bot:

```bash
docker compose restart tracefund
```

Stop container tanpa menghapus database:

```bash
docker compose down
```

Build ulang setelah perubahan kode:

```bash
docker compose up -d --build
```

Log startup yang benar akan berisi kira-kira:

```text
Berhasil sync 10 slash command
Bot online sebagai TraceFund#0891
```

Database dipersistenkan melalui mapping:

```text
./tracefund.db:/app/tracefund.db
```

## Deploy ke VPS Ubuntu

Install Docker:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Login ulang setelah menambahkan user ke group Docker, lalu clone dan jalankan:

```bash
git clone https://github.com/Psr354/TraceFund.git
cd TraceFund
nano .env
chmod 600 .env
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 tracefund
```

Jangan commit `.env` ke Git. Jika ingin membawa database historis, salin `tracefund.db` ke folder project VPS sebelum container dijalankan.

## Update dari Laptop ke VPS

Di laptop:

```bash
git add Dockerfile docker-compose.yml main.py seed_db.py requirements.txt README.md .gitignore
git commit -m "Update TraceFund"
git push origin main
```

Di VPS:

```bash
cd ~/TraceFund
git pull origin main
docker compose up -d --build
docker compose logs --tail=100 tracefund
```

Alternatif tanpa registry: source code di-pull di VPS lalu image dibuild langsung di VPS.

## File yang Boleh dan Tidak Boleh Dipush

Boleh dipush:

```text
Dockerfile
docker-compose.yml
main.py
seed_db.py
requirements.txt
README.md
.gitignore
```

Jangan dipush:

```text
.env
tracefund.db
venv/
__pycache__/
*.pyc
```

Periksa sebelum commit:

```bash
git status --short
git check-ignore .env tracefund.db
```

Jika `.env` atau `tracefund.db` muncul sebagai file yang akan di-commit, hentikan proses dan periksa `.gitignore`.

## Troubleshooting

### Command tidak muncul

1. Pastikan bot di-invite dengan scope `applications.commands`.
2. Refresh Discord dengan `Ctrl + R`.
3. Restart container:

```bash
docker compose restart tracefund
```

4. Periksa log:

```bash
docker compose logs --tail=100 tracefund
```

### Command terkirim sebagai teks biasa

Ketik `/`, lalu pilih command TraceFund dari autocomplete Discord. Jangan hanya mengetik `/ringkasan` sebagai teks lalu mengirimnya.

### Bot online tetapi akses ditolak

Pastikan `ALLOWED_USER_ID` sama dengan User ID akun yang menjalankan command.

### Bot tidak online

Periksa:

```bash
docker compose ps
docker compose logs --tail=100 tracefund
```

Kemungkinan penyebab:

- `DISCORD_TOKEN` salah atau sudah di-reset.
- `.env` tidak berada di root project.
- Docker Engine belum aktif.
- Container terus restart karena error konfigurasi.

### Data hilang setelah restart

Pastikan volume berikut masih ada di `docker-compose.yml`:

```yaml
volumes:
  - ./tracefund.db:/app/tracefund.db
```

Jangan menghapus `tracefund.db` jika ingin mempertahankan transaksi.

### Import data gagal

Gunakan path absolut dan tanda kutip:

```bash
python seed_db.py --source-dir "/path/ke/pengeluaran uang"
```

## Status Project

Validasi yang sudah dilakukan:

- Python syntax check berhasil.
- Docker image berhasil dibuild.
- Container berhasil berjalan.
- Bot berhasil login ke Discord.
- Slash command berhasil di-sync ke server.
- Database historis berhasil diimpor dari file Markdown.
