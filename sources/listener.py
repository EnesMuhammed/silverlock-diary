import requests
import os
import time
import subprocess
import shutil

# --- YAPILANDIRMA AYARLARI ---
# GitHub depo bilgileri
GITHUB_USERNAME = "EnesMuhammed"  # Kendi GitHub kullanıcı adınız
GITHUB_REPO_NAME = "silverlock-diary" # Kendi depo adınız

# Ana uygulamanızın adı (örneğin silverlock.py)
# ÖNEMLİ: Eğer uygulamanız direkt .py dosyası olarak çalışacaksa
# bu ismi kullanın. Eğer bunu EXE'ye çevirecekseniz, o zaman yine .exe adını kullanmanız gerekir.
MAIN_APP_NAME = "silverlock.py" # <--- Burası değişti!

# Ana uygulamanızın ham (raw) GitHub URL'i
# Sizin verdiğiniz linke göre güncellendi.
GITHUB_RAW_APP_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/main/{MAIN_APP_NAME}" # <--- Burası değişti!


# Sürüm dosyasının adı
VERSION_FILE_NAME = "versiyon.txt"
# Sürüm dosyasının ham (raw) GitHub URL'i
# Bu önceki verdiğiniz linke göre doğru kalıyor.
GITHUB_RAW_VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/main/{VERSION_FILE_NAME}"


# Kontrol etme aralığı (saniye cinsinden)
CHECK_INTERVAL_SECONDS = 3600 # 1 saat (3600 saniye)

# Listener'ın kendi konumu
LISTENER_DIR = os.path.dirname(os.path.abspath(__file__))

# Ana uygulamanın tam yolu
MAIN_APP_PATH = os.path.join(LISTENER_DIR, MAIN_APP_NAME)
# Yerel sürüm dosyasının tam yolu
LOCAL_VERSION_PATH = os.path.join(LISTENER_DIR, VERSION_FILE_NAME)

# --- Fonksiyonlar ---

def get_remote_version():
    """Doğrudan ham GitHub URL'sinden sürüm dosyasının içeriğini alır."""
    url = GITHUB_RAW_VERSION_URL
    try:
        print(f"Uzak sürüm {url} adresinden kontrol ediliyor...")
        response = requests.get(url, timeout=10)
        response.raise_for_status() # HTTP hatalarını kontrol et (örn: 404 Not Found)
        return response.text.strip()
    except requests.exceptions.RequestException as e:
        print(f"Hata: Uzak sürüm kontrol edilemedi (Raw URL): {e}")
        return None

def get_local_version():
    """Yerel sürüm dosyasından sürüm numarasını alır."""
    if not os.path.exists(LOCAL_VERSION_PATH):
        print(f"Yerel sürüm dosyası ({LOCAL_VERSION_PATH}) bulunamadı. Varsayılan '0.0' olarak ayarlandı.")
        return "0.0" # Dosya yoksa başlangıç sürümü olarak kabul et
    try:
        with open(LOCAL_VERSION_PATH, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Hata: Yerel sürüm okunurken hata oluştu: {e}")
        return "0.0"

def save_local_version(version):
    """Yerel sürüm dosyasını günceller."""
    try:
        with open(LOCAL_VERSION_PATH, 'w') as f:
            f.write(version)
        print(f"Yerel sürüm güncellendi: {version}")
    except Exception as e:
        print(f"Hata: Yerel sürüm kaydedilirken hata oluştu: {e}")

def download_new_app(target_path):
    """Yeni EXE dosyasını doğrudan ham GitHub URL'sinden indirir."""
    url = GITHUB_RAW_APP_URL
    temp_download_path = target_path + ".tmp" # Geçici dosya adı

    try:
        print(f"Yeni uygulama {url} adresinden indiriliyor...")
        response = requests.get(url, stream=True, timeout=60) # Büyük dosyalar için timeout artırıldı
        response.raise_for_status()

        with open(temp_download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: # chunk'lar boş olmasın
                    f.write(chunk)
        print(f"Yeni uygulama geçici olarak {temp_download_path} adresine indirildi.")
        return temp_download_path
    except requests.exceptions.RequestException as e:
        print(f"Hata: Uygulama indirilirken sorun oluştu: {e}")
        if os.path.exists(temp_download_path):
            os.remove(temp_download_path)
        return None

def is_app_running(app_name):
    """Ana uygulamanın çalışıp çalışmadığını kontrol eder (Windows için)."""
    # tasklist komutunu kullanarak çalışan uygulamaları listele
    try:
        output = subprocess.check_output(['tasklist', '/fi', f'imagename eq {app_name}'], creationflags=subprocess.CREATE_NO_WINDOW).decode('utf-8')
        return app_name.lower() in output.lower()
    except subprocess.CalledProcessError:
        return False # tasklist komutu bulunamazsa veya hata olursa

def terminate_app(app_name):
    """Çalışan ana uygulamayı sonlandırır (Windows için)."""
    print(f"{app_name} uygulaması sonlandırılıyor...")
    try:
        subprocess.run(['taskkill', '/f', '/im', app_name], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        print(f"{app_name} başarıyla sonlandırıldı.")
        time.sleep(2) # Uygulamanın kapanması için biraz bekle
        return True
    except subprocess.CalledProcessError as e:
        print(f"Hata: {app_name} sonlandırılamadı: {e}")
        return False

def start_app(app_path):
    """Ana uygulamayı yeniden başlatır."""
    print(f"Uygulama yeniden başlatılıyor: {app_path}")
    try:
        # Popen kullanarak uygulamayı arka planda başlat
        subprocess.Popen([app_path], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        print("Uygulama başarıyla başlatıldı.")
        return True
    except Exception as e:
        print(f"Hata: Uygulama başlatılamadı: {e}")
        return False

def update_process():
    """Güncelleme sürecini yönetir."""
    remote_version = get_remote_version()
    if remote_version is None:
        return # Uzak sürüm alınamadı, tekrar dene

    local_version = get_local_version()

    # Sürüm karşılaştırmasını doğrudan string olarak yapıyoruz.
    # Eğer 1.10 ve 1.2 gibi sürümleriniz varsa, semver kütüphanesi kullanmanız gerekebilir.
    # Basit sayısal veya X.Y.Z formatları için string karşılaştırma yeterli olabilir.
    if remote_version > local_version:
        print(f"Yeni sürüm bulundu! Uzak: {remote_version}, Yerel: {local_version}")

        # Eğer uygulama çalışıyorsa sonlandır
        if is_app_running(MAIN_APP_NAME):
            print("Ana uygulama çalışıyor, güncelleyici bitene kadar kapatılıyor...")
            if not terminate_app(MAIN_APP_NAME):
                print("Uygulama sonlandırılamadı, güncelleme iptal ediliyor.")
                return

        # Yeni EXE dosyasını indir
        temp_exe_path = download_new_app(MAIN_APP_PATH)
        if temp_exe_path is None:
            print("Yeni uygulama indirilemedi, güncelleme iptal ediliyor.")
            # Eğer ana uygulama kapatıldıysa, yeniden başlatmayı düşünebilirsiniz
            # start_app(MAIN_APP_PATH) # Riskli, eski bozuk haliyle başlayabilir

def main():
    print("Update Listener başlatıldı...")
    while True:
        update_process()
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()