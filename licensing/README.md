# LED Planner — portal akun dan lisensi

Implementasi backend Python/Flask + SQLite dan portal dark responsif. **Belum aktif di GitHub Pages.** Backend melayani portal pada `/` dan aplikasi pada `/planner` setelah autentikasi. Tidak ada akun produksi atau PIN default. `hdrg / 1945` tidak ditanam ke kode.

## Fitur

- Admin membuat nama pelanggan, username unik, PIN otomatis 8 digit atau manual 6–12 digit.
- PIN ditampilkan sekali setelah pembuatan/reset. Salin akses dan generate ulang tersedia; hash scrypt saja yang disimpan.
- Trial 72 jam, bulanan kalender, tahunan kalender, permanen. Tanggal 31 mengikuti hari terakhir bulan tujuan; 29 Februari mengikuti 28 Februari di tahun nonkabisat.
- Default aktivasi saat login pertama; alternatif tanggal/jam yang ditentukan admin. Tanggal input mengikuti timezone perangkat admin dan dikonversi ke UTC; server menentukan waktu akses.
- Ubah paket mengganti jadwal lama. Perpanjang menambahkan satu periode paket dari tanggal akhir atau sekarang jika sudah habis. Perpanjangan tidak mengaktifkan akun yang dinonaktifkan.
- Aktif/nonaktif, reset PIN, reset sesi. Satu sesi browser per akun, kedaluwarsa login 24 jam. Login baru mengeluarkan sesi lama.
- Akun expired dapat login ke halaman perpanjangan tetapi tidak menerima dokumen `/planner`.
- Pemeriksaan ulang setiap 30 detik dan saat tab aktif. Server gagal/tidak terhubung menutup akses UI sampai verifikasi berhasil. Ini versi online; belum ada lisensi offline.
- Proyek tetap disimpan lokal per akun/browser, bukan di database. Login menggunakan akun lain tidak mengambil proyek akun sebelumnya. Proyek lama harus diekspor JSON dari aplikasi lama kemudian diimpor ke versi ini.
- WhatsApp berisi username dan paket, tidak mengirim PIN. Tombol baru muncul setelah nomor diatur. Tidak ada pesan yang dikirim otomatis.
- Audit perubahan akun tanpa mencatat PIN.

## Pengujian lokal

Dari root repository:

```bash
python -m venv .venv
.venv/bin/pip install -r licensing/requirements.txt pytest
export LED_DEV_HTTP=1
export LED_PUBLIC_ORIGIN=http://127.0.0.1:8000
.venv/bin/flask --app licensing.app:create_app create-admin
.venv/bin/python -m licensing.run
```

CLI meminta username (default `hdrg`) dan PIN admin baru 8–12 digit, dua kali dengan input tersembunyi. PIN admin tidak dikirim melalui GitHub atau ditulis di konfigurasi. Buka `http://127.0.0.1:8000`. Di Windows gunakan `.venv\\Scripts\\python.exe`, `.venv\\Scripts\\flask.exe`, dan atur environment melalui PowerShell.

```bash
.venv/bin/python -m pytest licensing/tests -q
```

## Deployment produksi (hosting Python atau Docker)

Backend dan portal wajib berada pada **origin HTTPS yang sama**. GitHub Pages saja tidak dapat menjalankan Python atau SQLite. Jangan arahkan aplikasi publik ke portal sebelum server, admin, backup, dan URL HTTPS berfungsi.

1. Tentukan domain HTTPS dan hosting yang mendukung Python/Docker serta disk persisten. Salin `licensing/.env.example` ke file konfigurasi **di luar repository**, lalu isi origin dan nomor WhatsApp HDRG (format `62...`). Jangan mengisi PIN pada file konfigurasi.
2. Build dari root repository: `docker build -f licensing/Dockerfile -t ledplanner .`
3. Jalankan dengan disk persisten dan port loopback:

   ```bash
   docker volume create ledplanner-data
   docker run -d --name ledplanner --restart unless-stopped \
     --env-file /secure/ledplanner.env \
     -v ledplanner-data:/data -p 127.0.0.1:8000:8000 ledplanner
   docker exec -it ledplanner flask --app licensing.app:create_app create-admin
   ```

4. Reverse proxy HTTPS mengarah ke port 8000. Konfigurasi IP proxy tunggal yang benar pada `LED_TRUSTED_PROXY` bila memakai forwarded headers. Jangan percaya header IP dari publik; tanpa trusted proxy, pembatasan IP dihitung dari IP proxy bersama. Selain bucket IP (60/15 menit), pembatasan username berlaku 10 percobaan/15 menit. Origin harus cocok persis dengan `LED_PUBLIC_ORIGIN`.
5. Uji admin membuat trial, login pelanggan, export PNG/XML/PDF, nonaktifkan akun, serta backup/restore database sebelum menerima pelanggan.
6. Setelah server siap, ubah URL aplikasi Windows Tauri ke portal baru dan build installer. URL lama pada wrapper saat ini tetap membuka GitHub Pages.
7. Cutover halaman publik lama baru dilakukan setelah memastikan pelanggan memiliki akses baru. Source/client lama yang pernah dipublikasikan tetap bisa disalin; login baru bukan DRM atas versi lama.

SQLite ditujukan untuk satu instance aplikasi dengan volume lokal persisten. Jangan menjalankan banyak replica pada database file ini. Backup memakai SQLite backup API agar konsisten dengan WAL, simpan terenkripsi di luar server, dan uji restore. Jangan menyimpan database, cookie sesi, PIN atau file `.env` ke repository. Produksi memerlukan monitoring, TLS, backup dan akses operator untuk pemulihan admin. Jika lupa PIN admin, lakukan pemulihan lewat operator server; belum tersedia reset PIN admin dari portal.

## Batas perlindungan

Backend mengendalikan autentikasi, administrasi akun, lisensi, dan pengiriman halaman planner. Seluruh mesin mapping/export masih JavaScript di browser. Pengguna yang sudah menerima kode dapat menyalinnya atau mengubah pemeriksaan browser; versi ini **bukan proteksi anti-pembajakan atau DRM**. Jika diperlukan perlindungan lebih tinggi, pindahkan fungsi berbayar kritis ke API terotorisasi dan pertimbangkan distribusi source privat. Frontend lama pada repository/GitHub Pages tidak otomatis terkunci.

Sesi disimpan server; cookie HttpOnly/Secure/SameSite=Strict, semua perubahan memerlukan Origin yang cocok dan token CSRF. CSP masih mengizinkan inline script/style karena planner lama menggunakan event handler inline; refactor terpisah diperlukan sebelum CSP ketat. PIN admin harus acak, bukan PIN pendek yang sudah diketahui publik.

## Referensi implementasi

- https://flask.palletsprojects.com/en/stable/web-security/
- https://flask.palletsprojects.com/en/stable/deploying/
- https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.security.generate_password_hash
