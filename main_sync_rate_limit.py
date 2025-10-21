import gspread
import json
import gdown
import shutil
import os
from os import path
from oauth2client.service_account import ServiceAccountCredentials
import time

# Your sheet URLs
sheet_urls = {
    'slusd':'https://docs.google.com/spreadsheets/d/1lgXm6YQTCR3AHIjVrSDkgvkVX9cwx-2O-taeP_ss2zw/edit?usp=sharing',
    'garfield': 'https://docs.google.com/spreadsheets/d/1helB1s9Ffw55kunhsE7YVqxQXTsK98c1u4KQz6zL_dw/edit?usp=sharing',
    'jefferson':'https://docs.google.com/spreadsheets/d/1LYA0097njxt58udNwTohsTJTcGB4fK34o4XOv9B_8qk/edit?usp=sharing',
    'madison': 'https://docs.google.com/spreadsheets/d/1rv9istdWf97vKupj7nqrc81rR6Bz4_EsicNw8AxsCFk/edit?usp=sharing',
    'mckinley': 'https://docs.google.com/spreadsheets/d/17a6eMTRKBDODcZHjNqgTBeiw9mVYXsFWPENwYx5T360/edit?usp=sharing',
    'monroe': 'https://docs.google.com/spreadsheets/d/1Kkq0lMLJpGizkKva9lgLiljQDJrF1TRnlaSk2NyxrEg/edit?usp=sharing',
    'roosevelt': 'https://docs.google.com/spreadsheets/d/1gfqkEjxWpmQVlxDcGubEtAIHZNyU2MlsSudfSPto9Io/edit?usp=sharing',
    'washington': 'https://docs.google.com/spreadsheets/d/1n093HqhKGnXmUnEhWcsgBwKT1NRwj_6QR0_Z4ABwOXg/edit?usp=sharing',
    'halkin': 'https://docs.google.com/spreadsheets/d/1KouJ3M5TDdnd0CHsvjQi6RDj6a4kXqvLoexXA55LPCo/edit?usp=sharing',
    'bancroft': 'https://docs.google.com/spreadsheets/d/1JUrvpPWN7-I0qNPMNlZQtVsMsHQgwtLpbyLco1qDTtg/edit?usp=sharing',
    'muir': 'https://docs.google.com/spreadsheets/d/1Kkq0lMLJpGizkKva9lgLiljQDJrF1TRnlaSk2NyxrEg/edit#gid=0',
    'lincoln': 'https://docs.google.com/spreadsheets/d/1hloCf_7G-IEi2fPHKoajc2c6YE2d4vW8YqWL3JVPSjY/edit?usp=sharing',
    'slhs': 'https://docs.google.com/spreadsheets/d/1dI_GiYOry4M-XTMcuh25uZlC4EXRXWWOR4jHD3nc4Rk/edit?usp=sharing',
    'adult': 'https://docs.google.com/spreadsheets/d/1_xj63pU1Jg0NTBx0OwfOED4f--QitiYmGCFadaHvfd8/edit?usp=sharing',
    'slva': 'https://docs.google.com/spreadsheets/d/1GQodWj-qsV4jW-kbXnGAlGHTBWLwRRxm0ySm_DFvBaI/edit?usp=sharing',
}

ALLOWED_EXTENSIONS = {
        '.jpg', 
        '.jpeg', 
        '.JPG', 
        '.JPEG', 
        '.png', 
        '.PNG', 
        '.gif', 
        '.GIF'
        }

# Rate limiting configuration
DOWNLOAD_ATTEMPTS = 0
MAX_DOWNLOADS_PER_HOUR = 10
RATE_LIMIT_SLEEP = 360  # 6 minutes between downloads when rate limited

def read_gsheet(sheet_url, credentials_file='creds.json', sheet_name='Sheet1', columns=['name','Folder ID']):
    """Read Google Sheet - unchanged"""
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_url)
    sheet = spreadsheet.worksheet(sheet_name)    
    data = sheet.get_all_records()

    folders = []
    for row in data:
        folder = {}
        for column in columns:
            folder[column] = row[column]
        folders.append(folder)
    
    return folders

def get_local_files(folder_path):
    """Get all files in local folder recursively"""
    if not os.path.exists(folder_path):
        return set()
    
    local_files = set()
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), folder_path)
            local_files.add(rel_path)
    
    return local_files

def get_remote_files(folder_id, credentials_file='/home/administrator/gdrive_downloader/creds.json'):
    """Get all files in Google Drive folder recursively - SHARED DRIVE FIXED VERSION"""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        def get_files_recursive(folder_id, current_path=""):
            files_set = set()
            query = "'{0}' in parents and trashed=false".format(folder_id)
            
            try:
                results = service.files().list(
                    q=query, 
                    fields="files(id, name, mimeType)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                
                items = results.get('files', [])
                
                for item in items:
                    item_path = item['name'] if not current_path else "{}/{}".format(current_path, item['name'])
                    
                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        subfolder_files = get_files_recursive(item['id'], item_path)
                        files_set.update(subfolder_files)
                    else:
                        files_set.add(item_path)
                
            except Exception as e:
                print("Error querying folder {}: {}".format(folder_id, e))
                return files_set
            
            return files_set
        
        return get_files_recursive(folder_id)
        
    except ImportError:
        print("ERROR: Google API client libraries not installed!")
        return set()
    except Exception as e:
        print("Error getting remote files: {}".format(e))
        return set()

def sync_folder(folder_url, folder_path, folder_id):
    """Sync folder with intelligent rate limiting"""
    global DOWNLOAD_ATTEMPTS
    
    print("Syncing {}".format(folder_path))
    
    # Get file counts
    local_files = get_local_files(folder_path)
    remote_files = get_remote_files(folder_id)
    
    print("Local files: {} | Remote files: {}".format(len(local_files), len(remote_files)))
    
    if len(remote_files) == 0:
        print("No remote files found - falling back to simple download")
        return sync_folder_simple(folder_url, folder_path)
    
    # Calculate differences
    files_to_delete = local_files - remote_files
    files_to_download = remote_files - local_files
    
    print("Files to delete: {} | Files to download: {}".format(len(files_to_delete), len(files_to_download)))
    
    # Delete outdated files
    for file_path in files_to_delete:
        full_path = os.path.join(folder_path, file_path)
        if os.path.exists(full_path):
            print("Deleting: {}".format(file_path))
            os.remove(full_path)
            
            # Clean up empty directories
            dir_path = os.path.dirname(full_path)
            try:
                if dir_path != folder_path and not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except:
                pass
    
    # Handle downloads with rate limiting
    if files_to_download:
        if DOWNLOAD_ATTEMPTS >= MAX_DOWNLOADS_PER_HOUR:
            print("⚠️  Rate limit reached ({} downloads). Skipping download for now.".format(MAX_DOWNLOADS_PER_HOUR))
            print("   Files needed: {}".format(list(files_to_download)[:3]))
            return 5  # Short sleep, no download attempted
        
        print("Downloading {} new files via gdown...".format(len(files_to_download)))
        DOWNLOAD_ATTEMPTS += 1
        
        temp_path = "{}_temp".format(folder_path)
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
            
        try:
            # Attempt download
            gdown.download_folder(folder_url, output=temp_path, quiet=False)
            
            # Copy only new files
            copied_count = 0
            for file_path in files_to_download:
                src = os.path.join(temp_path, file_path)
                dst = os.path.join(folder_path, file_path)
                
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    copied_count += 1
            
            print("✅ Successfully copied {} files".format(copied_count))
            shutil.rmtree(temp_path)
            
            # Return longer sleep time after successful download
            return RATE_LIMIT_SLEEP
            
        except Exception as e:
            print("❌ Download failed: {}".format(str(e)[:100]))
            
            # Check if it's a rate limit error
            if "Cannot retrieve the public link" in str(e) or "many accesses" in str(e):
                print("⚠️  Rate limit detected. Increasing download counter.")
                DOWNLOAD_ATTEMPTS += 2  # Penalize rate limit errors more
                if os.path.exists(temp_path):
                    shutil.rmtree(temp_path)
                return RATE_LIMIT_SLEEP
            else:
                # Other error, clean up and try shorter sleep
                if os.path.exists(temp_path):
                    shutil.rmtree(temp_path)
                return 60  # 1 minute for other errors
    else:
        print("✅ No new files to download, folder is up to date!")
        return 5  # Short sleep for up-to-date folders

def sync_folder_simple(folder_url, folder_path):
    """Simple fallback with rate limiting"""
    global DOWNLOAD_ATTEMPTS
    
    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        if DOWNLOAD_ATTEMPTS >= MAX_DOWNLOADS_PER_HOUR:
            print("⚠️  Rate limit reached. Skipping simple download.")
            return 5
            
        print("Folder empty, downloading: {}".format(folder_path))
        DOWNLOAD_ATTEMPTS += 1
        
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        
        try:
            gdown.download_folder(folder_url, output=folder_path, quiet=False)
            print("✅ Simple download successful")
            return RATE_LIMIT_SLEEP
        except Exception as e:
            print("❌ Simple download failed: {}".format(str(e)[:100]))
            return 60
    else:
        print("Folder exists and not empty, skipping")
        return 5

if __name__ == "__main__":
    """Main sync with intelligent rate limiting"""
    
    creds = json.load(open('creds.json'))
    image_folder_home = '/var/www/html/images'
    
    print("=== Starting sync with rate limiting and image filtering ===")
    print("Max downloads per session: {}".format(MAX_DOWNLOADS_PER_HOUR))
    print("Allowed image extensions: {}".format(', '.join(sorted(ALLOWED_EXTENSIONS))))
    
    for school, sheet_url in sheet_urls.items():
        if sheet_url == None:
            continue
        
        print("\n=== Processing school: {} ===".format(school))
        
        try:
            google_drive_folder_info = read_gsheet(sheet_url, '/home/administrator/gdrive_downloader/creds.json')
            print("Found {} folders for {}".format(len(google_drive_folder_info), school))
            
            for download_info in google_drive_folder_info:
                folder_url = "https://drive.google.com/drive/folders/{}".format(download_info['Folder ID'])
                folder_path = "{}/{}/{}".format(image_folder_home, school, download_info['name'])
                folder_id = download_info['Folder ID']
                
                print("\nProcessing: {}/{}".format(school, download_info['name']))
                
                # Sync and get recommended sleep time
                sleep_time = sync_folder(folder_url, folder_path, folder_id)
                
                print("Downloads attempted: {} | Sleeping for {} seconds".format(DOWNLOAD_ATTEMPTS, sleep_time))
                time.sleep(sleep_time)
                
        except Exception as e:
            print("Error processing school {}: {}".format(school, e))
    
    print("\n=== Sync complete! ===")
    print("Total downloads attempted: {}".format(DOWNLOAD_ATTEMPTS))