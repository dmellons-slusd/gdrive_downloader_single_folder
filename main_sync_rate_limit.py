import gspread
import json
import gdown
import shutil
import os
from os import path
from oauth2client.service_account import ServiceAccountCredentials
import time
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime

# Configure logging with date-based log files
LOG_DIR = '/home/administrator/gdrive_downloader/log'
os.makedirs(LOG_DIR, exist_ok=True)  # Create log directory if it doesn't exist

today_date = datetime.now().strftime('%Y-%m-%d')
LOG_FILE = os.path.join(LOG_DIR, '{}.log'.format(today_date))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # This keeps console output
    ]
)
logger = logging.getLogger(__name__)

# Your sheet URLs
sheet_urls = {
    'adult': 'https://docs.google.com/spreadsheets/d/1_xj63pU1Jg0NTBx0OwfOED4f--QitiYmGCFadaHvfd8/edit?usp=sharing',
    'bancroft': 'https://docs.google.com/spreadsheets/d/1JUrvpPWN7-I0qNPMNlZQtVsMsHQgwtLpbyLco1qDTtg/edit?usp=sharing',
    'garfield': 'https://docs.google.com/spreadsheets/d/1helB1s9Ffw55kunhsE7YVqxQXTsK98c1u4KQz6zL_dw/edit?usp=sharing',
    'halkin': 'https://docs.google.com/spreadsheets/d/1KouJ3M5TDdnd0CHsvjQi6RDj6a4kXqvLoexXA55LPCo/edit?usp=sharing',
    'jefferson':'https://docs.google.com/spreadsheets/d/1LYA0097njxt58udNwTohsTJTcGB4fK34o4XOv9B_8qk/edit?usp=sharing',
    'lincoln': 'https://docs.google.com/spreadsheets/d/1hloCf_7G-IEi2fPHKoajc2c6YE2d4vW8YqWL3JVPSjY/edit?usp=sharing',
    'madison': 'https://docs.google.com/spreadsheets/d/1rv9istdWf97vKupj7nqrc81rR6Bz4_EsicNw8AxsCFk/edit?usp=sharing',
    'mckinley': 'https://docs.google.com/spreadsheets/d/17a6eMTRKBDODcZHjNqgTBeiw9mVYXsFWPENwYx5T360/edit?usp=sharing',
    'monroe': 'https://docs.google.com/spreadsheets/d/1Kkq0lMLJpGizkKva9lgLiljQDJrF1TRnlaSk2NyxrEg/edit?usp=sharing',
    'muir': 'https://docs.google.com/spreadsheets/d/1Kkq0lMLJpGizkKva9lgLiljQDJrF1TRnlaSk2NyxrEg/edit#gid=0',
    'roosevelt': 'https://docs.google.com/spreadsheets/d/1gfqkEjxWpmQVlxDcGubEtAIHZNyU2MlsSudfSPto9Io/edit?usp=sharing',
    'slhs': 'https://docs.google.com/spreadsheets/d/1dI_GiYOry4M-XTMcuh25uZlC4EXRXWWOR4jHD3nc4Rk/edit?usp=sharing',
    'slusd':'https://docs.google.com/spreadsheets/d/1lgXm6YQTCR3AHIjVrSDkgvkVX9cwx-2O-taeP_ss2zw/edit?usp=sharing',
    'slva': 'https://docs.google.com/spreadsheets/d/1GQodWj-qsV4jW-kbXnGAlGHTBWLwRRxm0ySm_DFvBaI/edit?usp=sharing',
    'washington': 'https://docs.google.com/spreadsheets/d/1n093HqhKGnXmUnEhWcsgBwKT1NRwj_6QR0_Z4ABwOXg/edit?usp=sharing',
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

# Tracking for summary
SCHOOL_STATS = {}

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

def get_local_files(folder_path, ignore_subdirs=True):
    """Get all files in local folder - optionally only from root"""
    if not os.path.exists(folder_path):
        return set()
    
    local_files = set()
    
    if ignore_subdirs:
        # Only get files directly in the folder (no subdirectories)
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    # Only count allowed image extensions
                    if any(item.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                        local_files.add(item)
            return local_files
        except Exception as e:
            logger.error("Error getting local files: {}".format(e))
            return set()
    else:
        # Get all files recursively
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Only count allowed image extensions
                if any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                    local_files.add(rel_path)
        return local_files

def get_remote_files(folder_id, credentials_file='/home/administrator/gdrive_downloader/creds.json', ignore_subdirs=True):
    """Get all files in Google Drive folder - SHARED DRIVE SAFE"""
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        remote_files = set()
        
        if ignore_subdirs:
            # Only get files from root level (direct children)
            query = "'{0}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed=false".format(folder_id)
        else:
            # Get all files recursively (existing behavior)
            query = "'{0}' in parents and trashed=false".format(folder_id)
        
        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType, parents)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        items = results.get('files', [])
        
        for item in items:
            if item['mimeType'] != 'application/vnd.google-apps.folder':
                # Only count allowed image extensions
                if any(item['name'].endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    remote_files.add(item['name'])
        
        return remote_files
        
    except Exception as e:
        logger.error("Error getting remote files: {}".format(e))
        return set()

def sync_folder(folder_url, folder_path, folder_id, school_name, folder_name):
    """Sync folder with intelligent rate limiting - IGNORES SUBDIRECTORIES"""
    global DOWNLOAD_ATTEMPTS, SCHOOL_STATS
    
    logger.info("Syncing {}".format(folder_path))
    logger.info("NOTE: Subdirectories will be ignored - only root-level files will be synced")
    
    # Initialize stats for this folder
    stats = {
        'local_files_count': 0,
        'remote_files_count': 0,
        'files_deleted': 0,
        'files_downloaded': 0,
        'status': 'unknown',
        'folder_name': folder_name
    }
    
    # Get file counts - only from root level
    local_files = get_local_files(folder_path, ignore_subdirs=True)
    remote_files = get_remote_files(folder_id, ignore_subdirs=True)
    
    stats['local_files_count'] = len(local_files)
    stats['remote_files_count'] = len(remote_files)
    
    logger.info("Local files (root only): {} | Remote files (root only): {}".format(len(local_files), len(remote_files)))
    
    if len(remote_files) == 0:
        logger.info("No remote files found - falling back to simple download")
        result = sync_folder_simple(folder_url, folder_path, stats)
        
        # Update school stats
        if school_name not in SCHOOL_STATS:
            SCHOOL_STATS[school_name] = []
        SCHOOL_STATS[school_name].append(stats)
        
        return result
    
    # Calculate differences
    files_to_delete = local_files - remote_files
    files_to_download = remote_files - local_files
    
    logger.info("Files to delete: {} | Files to download: {}".format(len(files_to_delete), len(files_to_download)))
    
    # Delete outdated files
    for file_name in files_to_delete:
        full_path = os.path.join(folder_path, file_name)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            logger.info("Deleting: {}".format(file_name))
            os.remove(full_path)
            stats['files_deleted'] += 1
    
    # Handle downloads with rate limiting
    if files_to_download:
        if DOWNLOAD_ATTEMPTS >= MAX_DOWNLOADS_PER_HOUR:
            logger.warning("Rate limit reached ({} downloads). Skipping download for now.".format(MAX_DOWNLOADS_PER_HOUR))
            logger.info("   Files needed: {}".format(list(files_to_download)[:3]))
            stats['status'] = 'rate_limited'
            
            # Update school stats
            if school_name not in SCHOOL_STATS:
                SCHOOL_STATS[school_name] = []
            SCHOOL_STATS[school_name].append(stats)
            
            return 5  # Short sleep, no download attempted
        
        logger.info("Downloading {} new files via gdown...".format(len(files_to_download)))
        DOWNLOAD_ATTEMPTS += 1
        
        temp_path = "{}_temp".format(folder_path)
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
            
        try:
            # Attempt download
            gdown.download_folder(folder_url, output=temp_path, quiet=False)
            
            # Copy only new files FROM ROOT DIRECTORY ONLY
            copied_count = 0
            skipped_subdir_count = 0
            
            for file_name in files_to_download:
                # Skip if the file path contains subdirectories
                if os.sep in file_name or '/' in file_name:
                    logger.info("Skipping subdirectory file: {}".format(file_name))
                    skipped_subdir_count += 1
                    continue
                
                src = os.path.join(temp_path, file_name)
                dst = os.path.join(folder_path, file_name)
                
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    copied_count += 1
                    logger.info("Copied: {}".format(file_name))
            
            stats['files_downloaded'] = copied_count
            stats['status'] = 'downloaded'
            
            logger.info("Successfully copied {} files".format(copied_count))
            if skipped_subdir_count > 0:
                logger.info("Skipped {} files in subdirectories".format(skipped_subdir_count))
            
            shutil.rmtree(temp_path)
            
            # Update school stats
            if school_name not in SCHOOL_STATS:
                SCHOOL_STATS[school_name] = []
            SCHOOL_STATS[school_name].append(stats)
            
            # Return longer sleep time after successful download
            return RATE_LIMIT_SLEEP
            
        except Exception as e:
            logger.error('folder_url: {}'.format(folder_url))
            logger.error("Download failed: {}".format(str(e)[:100]))
            stats['status'] = 'error'
            
            # Check if it's a rate limit error
            if "Cannot retrieve the public link" in str(e) or "many accesses" in str(e):
                logger.warning("Rate limit detected. Increasing download counter.")
                DOWNLOAD_ATTEMPTS += 2  # Penalize rate limit errors more
                if os.path.exists(temp_path):
                    shutil.rmtree(temp_path)
                
                # Update school stats
                if school_name not in SCHOOL_STATS:
                    SCHOOL_STATS[school_name] = []
                SCHOOL_STATS[school_name].append(stats)
                
                return RATE_LIMIT_SLEEP
            else:
                # Other error, clean up and try shorter sleep
                if os.path.exists(temp_path):
                    shutil.rmtree(temp_path)
                
                # Update school stats
                if school_name not in SCHOOL_STATS:
                    SCHOOL_STATS[school_name] = []
                SCHOOL_STATS[school_name].append(stats)
                
                return 60  # 1 minute for other errors
    else:
        logger.info("No new files to download, folder is up to date!")
        stats['status'] = 'up_to_date'
        
        # Update school stats
        if school_name not in SCHOOL_STATS:
            SCHOOL_STATS[school_name] = []
        SCHOOL_STATS[school_name].append(stats)
        
        return 5  # Short sleep for up-to-date folders

def sync_folder_simple(folder_url, folder_path, stats):
    """Simple fallback with rate limiting - IGNORES SUBDIRECTORIES"""
    global DOWNLOAD_ATTEMPTS
    
    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        if DOWNLOAD_ATTEMPTS >= MAX_DOWNLOADS_PER_HOUR:
            logger.warning("Rate limit reached. Skipping simple download.")
            stats['status'] = 'rate_limited'
            return 5
            
        logger.info("Folder empty, downloading: {}".format(folder_path))
        logger.info("NOTE: Only root-level files will be kept - subdirectories will be removed")
        DOWNLOAD_ATTEMPTS += 1
        
        temp_path = "{}_temp".format(folder_path)
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
        
        try:
            # Download to temp location
            gdown.download_folder(folder_url, output=temp_path, quiet=False)
            
            # Create target folder if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)
            
            # Copy only root-level files (ignore subdirectories)
            copied_count = 0
            skipped_subdir_count = 0
            
            if os.path.exists(temp_path):
                for item in os.listdir(temp_path):
                    src_path = os.path.join(temp_path, item)
                    
                    # Only copy files (not directories)
                    if os.path.isfile(src_path):
                        # Check if file has allowed extension
                        if any(item.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                            dst_path = os.path.join(folder_path, item)
                            shutil.copy2(src_path, dst_path)
                            copied_count += 1
                            logger.info("Copied: {}".format(item))
                    elif os.path.isdir(src_path):
                        # Count files in subdirectory that we're skipping
                        for root, dirs, files in os.walk(src_path):
                            skipped_subdir_count += len(files)
            
            stats['files_downloaded'] = copied_count
            stats['status'] = 'downloaded'
            
            logger.info("Simple download successful - copied {} root-level files".format(copied_count))
            if skipped_subdir_count > 0:
                logger.info("Skipped {} files in subdirectories".format(skipped_subdir_count))
            
            # Clean up temp directory
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
            
            return RATE_LIMIT_SLEEP
            
        except Exception as e:
            logger.error("Simple download failed: {}".format(str(e)[:100]))
            stats['status'] = 'error'
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
            return 60
    else:
        logger.info("Folder exists and not empty, skipping")
        stats['status'] = 'skipped'
        return 5

def log_school_summary(school_name):
    """Log a summary of actions taken for a school"""
    if school_name not in SCHOOL_STATS:
        logger.info("No stats collected for {}".format(school_name))
        return
    
    stats_list = SCHOOL_STATS[school_name]
    
    total_folders = len(stats_list)
    total_deleted = sum(s['files_deleted'] for s in stats_list)
    total_downloaded = sum(s['files_downloaded'] for s in stats_list)
    total_local = sum(s['local_files_count'] for s in stats_list)
    total_remote = sum(s['remote_files_count'] for s in stats_list)
    
    up_to_date = sum(1 for s in stats_list if s['status'] == 'up_to_date')
    downloaded = sum(1 for s in stats_list if s['status'] == 'downloaded')
    rate_limited = sum(1 for s in stats_list if s['status'] == 'rate_limited')
    errors = sum(1 for s in stats_list if s['status'] == 'error')
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY FOR SCHOOL: {}".format(school_name.upper()))
    logger.info("=" * 60)
    logger.info("Total folders processed: {}".format(total_folders))
    logger.info("Total local files (before): {}".format(total_local))
    logger.info("Total remote files: {}".format(total_remote))
    logger.info("Files deleted: {}".format(total_deleted))
    logger.info("Files downloaded: {}".format(total_downloaded))
    logger.info("")
    logger.info("Folder status breakdown:")
    logger.info("  - Up to date: {}".format(up_to_date))
    logger.info("  - Downloaded: {}".format(downloaded))
    logger.info("  - Rate limited: {}".format(rate_limited))
    logger.info("  - Errors: {}".format(errors))
    logger.info("=" * 60)
    logger.info("")

if __name__ == "__main__":
    """Main sync with intelligent rate limiting"""
    
    logger.info("")
    logger.info("#" * 70)
    logger.info("# STARTING IMAGE SYNC")
    logger.info("#" * 70)
    logger.info("Start time: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    logger.info("Max downloads per session: {}".format(MAX_DOWNLOADS_PER_HOUR))
    logger.info("Allowed image extensions: {}".format(', '.join(sorted(ALLOWED_EXTENSIONS))))
    logger.info("SUBDIRECTORIES WILL BE IGNORED - Only root-level files will be synced")
    logger.info("")
    
    creds = json.load(open('creds.json'))
    image_folder_home = '/var/www/html/images'
    
    for school, sheet_url in sheet_urls.items():
        if sheet_url == None:
            continue
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("PROCESSING SCHOOL: {}".format(school.upper()))
        logger.info("=" * 60)
        
        try:
            google_drive_folder_info = read_gsheet(sheet_url, '/home/administrator/gdrive_downloader/creds.json')
            logger.info("Found {} folders for {}".format(len(google_drive_folder_info), school))
            
            for download_info in google_drive_folder_info:
                folder_url = "https://drive.google.com/drive/folders/{}".format(download_info['Folder ID'])
                folder_path = "{}/{}/{}".format(image_folder_home, school, download_info['name'])
                folder_id = download_info['Folder ID']
                
                logger.info("")
                logger.info("Processing: {}/{}".format(school, download_info['name']))
                
                # Sync and get recommended sleep time
                sleep_time = sync_folder(folder_url, folder_path, folder_id, school, download_info['name'])
                
                logger.info("Downloads attempted: {} | Sleeping for {} seconds".format(DOWNLOAD_ATTEMPTS, sleep_time))
                time.sleep(sleep_time)
            
            # Log summary for this school
            log_school_summary(school)
                
        except Exception as e:
            logger.error("Error processing school {}: {}".format(school, e))
    
    logger.info("")
    logger.info("#" * 70)
    logger.info("# SYNC COMPLETE")
    logger.info("#" * 70)
    logger.info("End time: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    logger.info("Total downloads attempted: {}".format(DOWNLOAD_ATTEMPTS))
    logger.info("")
    logger.info("OVERALL SUMMARY:")
    logger.info("-" * 70)
    
    # Calculate overall totals
    total_schools = len(SCHOOL_STATS)
    total_folders = sum(len(stats) for stats in SCHOOL_STATS.values())
    total_deleted = sum(sum(s['files_deleted'] for s in stats) for stats in SCHOOL_STATS.values())
    total_downloaded = sum(sum(s['files_downloaded'] for s in stats) for stats in SCHOOL_STATS.values())
    
    logger.info("Schools processed: {}".format(total_schools))
    logger.info("Total folders processed: {}".format(total_folders))
    logger.info("Total files deleted: {}".format(total_deleted))
    logger.info("Total files downloaded: {}".format(total_downloaded))
    logger.info("")
    logger.info("~" * 70)
    logger.info("")