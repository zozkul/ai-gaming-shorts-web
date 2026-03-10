"""
Google Drive'dan gameplay videolarını indir
"""
import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_drive():
    """Google Drive authentication"""
    creds = None

    # Token varsa yükle
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Token yoksa veya geçersizse yeni al
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', 'credentials.json'),
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Token'ı kaydet
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def list_videos_in_folder(service, folder_id):
    """Klasördeki videoları listele"""
    query = f"'{folder_id}' in parents and (mimeType contains 'video/' or name contains '.mp4' or name contains '.mov' or name contains '.avi')"

    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, size)",
        orderBy="modifiedTime desc"
    ).execute()

    return results.get('files', [])

def download_video(service, file_id, file_name, output_dir='input'):
    """Video dosyasını indir"""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, file_name)

    # Eğer zaten indirilmişse atla
    if os.path.exists(output_path):
        print(f"✓ Zaten mevcut: {file_name}")
        return output_path

    request = service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    print(f"📥 İndiriliyor: {file_name}")

    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"   {int(status.progress() * 100)}%", end='\r')

    # Dosyayı kaydet
    with open(output_path, 'wb') as f:
        f.write(fh.getvalue())

    print(f"✓ İndirildi: {file_name}")
    return output_path

def main():
    """Ana fonksiyon"""
    folder_id = os.getenv('DRIVE_FOLDER_ID')

    if not folder_id:
        print("❌ Hata: DRIVE_FOLDER_ID .env dosyasında ayarlanmamış!")
        return

    print("🔐 Google Drive'a bağlanılıyor...")
    service = authenticate_drive()

    print(f"📂 Klasördeki videolar getiriliyor...")
    videos = list_videos_in_folder(service, folder_id)

    if not videos:
        print("❌ Klasörde video bulunamadı!")
        return

    print(f"\n✓ {len(videos)} video bulundu\n")

    downloaded = []
    for video in videos:
        try:
            path = download_video(service, video['id'], video['name'])
            downloaded.append(path)
        except Exception as e:
            print(f"❌ Hata: {video['name']} - {str(e)}")

    print(f"\n✅ {len(downloaded)} video başarıyla indirildi!")
    print(f"📁 Konum: {os.path.abspath('input')}")

if __name__ == '__main__':
    main()
