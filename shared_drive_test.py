from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from icecream import ic

def get_remote_files_shared_drive(folder_id, credentials_file='/home/administrator/gdrive_downloader/creds.json'):
    """Get all files in Google Drive folder recursively - SHARED DRIVE VERSION"""
    try:
        # Set up credentials for Drive API
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        print("Setting up Drive API for Shared Drive access...")
        print("Folder ID: {}".format(folder_id))
        
        def get_files_recursive(folder_id, current_path=""):
            files_set = set()
            
            print("Checking folder: {} (path: {})".format(folder_id, current_path))
            
            # IMPORTANT: Add supportsAllDrives=True for Shared Drive access
            query = "'{0}' in parents and trashed=false".format(folder_id)
            print("Query: {}".format(query))
            
            try:
                # The key difference: supportsAllDrives=True and includeItemsFromAllDrives=True
                results = service.files().list(
                    q=query, 
                    fields="files(id, name, mimeType)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                
                items = results.get('files', [])
                print("Found {} items in folder".format(len(items)))
                
                for item in items:
                    print("Item: {} (type: {})".format(item['name'], item['mimeType']))
                    item_path = item['name'] if not current_path else "{}/{}".format(current_path, item['name'])
                    
                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        # Recursively get files from subfolder
                        print("Entering subfolder: {}".format(item['name']))
                        subfolder_files = get_files_recursive(item['id'], item_path)
                        files_set.update(subfolder_files)
                        print("Got {} files from subfolder {}".format(len(subfolder_files), item['name']))
                    else:
                        # It's a file
                        files_set.add(item_path)
                        print("Added file: {}".format(item_path))
                
            except Exception as e:
                print("Error querying folder {}: {}".format(folder_id, e))
                return files_set
            
            return files_set
        
        result = get_files_recursive(folder_id)
        print("Total files found: {}".format(len(result)))
        return result
        
    except Exception as e:
        print("Error getting remote files: {}".format(e))
        return set()

def test_shared_drive_access(folder_id):
    """Test basic Shared Drive access"""
    try:
        creds = Credentials.from_service_account_file(
            '/home/administrator/gdrive_downloader/creds.json',
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)
        
        print("=== TESTING SHARED DRIVE ACCESS ===")
        
        # Test specific folder access with Shared Drive support
        print("Testing folder access for ID: {}".format(folder_id))
        folder_info = service.files().get(
            fileId=folder_id,
            supportsAllDrives=True
        ).execute()
        
        print("✓ SUCCESS! Folder name: {}".format(folder_info.get('name', 'Unknown')))
        print("Folder parents: {}".format(folder_info.get('parents', [])))
        
        # Check if it's in a Shared Drive
        if 'driveId' in folder_info:
            print("✓ This folder is in a Shared Drive: {}".format(folder_info['driveId']))
        else:
            print("This folder is in regular Google Drive")
            
        return True
        
    except Exception as e:
        print("❌ Shared Drive access failed: {}".format(e))
        
        if "File not found" in str(e):
            print("SOLUTION: Add the service account to the Shared Drive itself")
            print("1. Go to the Shared Drive")
            print("2. Click 'Manage members'")
            print("3. Add: gsheets-service@polar-winter-333619.iam.gserviceaccount.com")
            print("4. Set permission to 'Content manager' or 'Manager'")
        
        return False

def list_accessible_shared_drives():
    """List all Shared Drives the service account can access"""
    try:
        creds = Credentials.from_service_account_file(
            '/home/administrator/gdrive_downloader/creds.json',
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)
        
        print("=== LISTING ACCESSIBLE SHARED DRIVES ===")
        
        # List Shared Drives
        results = service.drives().list().execute()
        drives = results.get('drives', [])
        
        print("Service account can access {} Shared Drives:".format(len(drives)))
        for drive in drives:
            print("  - {} (ID: {})".format(drive['name'], drive['id']))
            
        if len(drives) == 0:
            print("❌ No Shared Drives accessible")
            print("The service account needs to be added to the Shared Drive")
        
        return drives
        
    except Exception as e:
        print("Error listing Shared Drives: {}".format(e))
        return []

if __name__ == "__main__":
    # Test with your folder ID
    folder_id = "1sRJQdhLcmH0jWZuvgaNzCynFOvhGFRSN"
    
    # First, list accessible Shared Drives
    list_accessible_shared_drives()
    
    print("")
    
    # Then test specific folder access
    if test_shared_drive_access(folder_id):
        print("")
        print("=== TESTING FILE LISTING ===")
        files = get_remote_files_shared_drive(folder_id)
        if len(files) > 0:
            print("🎉 SUCCESS! Found {} files".format(len(files)))
            for file in list(files)[:5]:  # Show first 5 files
                print("  - {}".format(file))
        else:
            print("No files found in folder")