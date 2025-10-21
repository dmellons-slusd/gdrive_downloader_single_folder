import json
from icecream import ic

def test_credentials_and_api():
    """Comprehensive test of credentials and API access"""
    
    # Test 1: Check if credential file exists and is readable
    try:
        with open('/home/administrator/gdrive_downloader/creds.json', 'r') as f:
            creds_data = json.load(f)
        print("✓ Credentials file found and readable")
        print("Service account email: {}".format(creds_data.get('client_email', 'NOT FOUND')))
    except Exception as e:
        print("✗ Error reading credentials: {}".format(e))
        return False
    
    # Test 2: Try to import required libraries
    try:
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        print("✓ Google API libraries imported successfully")
    except ImportError as e:
        print("✗ Missing libraries: {}".format(e))
        print("Please run: sudo pip3 install google-api-python-client google-auth")
        return False
    
    # Test 3: Test credentials with different scopes
    test_scopes = [
        ['https://www.googleapis.com/auth/drive.readonly'],
        ['https://www.googleapis.com/auth/drive'],
        ['https://www.googleapis.com/auth/drive.file'],
        ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file']
    ]
    
    for i, scopes in enumerate(test_scopes):
        try:
            print("Testing scope set {}: {}".format(i+1, scopes))
            creds = Credentials.from_service_account_file(
                '/home/administrator/gdrive_downloader/creds.json', 
                scopes=scopes
            )
            service = build('drive', 'v3', credentials=creds)
            
            # Test basic API call
            results = service.files().list(pageSize=1).execute()
            print("✓ Scope set {} works for basic API access".format(i+1))
            
            # Test specific folder access
            folder_id = '1sRJQdhLcmH0jWZuvgaNzCynFOvhGFRSN'
            try:
                folder_info = service.files().get(fileId=folder_id).execute()
                print("✓ Scope set {} can access test folder: '{}'".format(i+1, folder_info.get('name', 'Unknown')))
                return True  # Success!
            except Exception as folder_error:
                print("✗ Scope set {} cannot access test folder: {}".format(i+1, folder_error))
                
        except Exception as e:
            print("✗ Scope set {} failed: {}".format(i+1, e))
    
    # Test 4: Try the old oauth2client approach (like your existing code)
    try:
        print("Testing with oauth2client (your existing approach)...")
        from oauth2client.service_account import ServiceAccountCredentials
        import gspread
        
        scope = [
            "https://spreadsheets.google.com/feeds",
            'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            '/home/administrator/gdrive_downloader/creds.json', 
            scope
        )
        
        # Try to use these credentials with the new Google API
        from googleapiclient.discovery import build
        import google.auth
        
        # Convert oauth2client credentials to google-auth credentials
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        
        service = build('drive', 'v3', credentials=creds)
        folder_id = '1sRJQdhLcmH0jWZuvgaNzCynFOvhGFRSN'
        folder_info = service.files().get(fileId=folder_id).execute()
        print("✓ oauth2client credentials work! Folder: '{}'".format(folder_info.get('name', 'Unknown')))
        return True
        
    except Exception as e:
        print("✗ oauth2client approach failed: {}".format(e))
    
    # Test 5: List what files the service account CAN see
    try:
        print("Listing files the service account can access...")
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        
        creds = Credentials.from_service_account_file(
            '/home/administrator/gdrive_downloader/creds.json', 
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(pageSize=10).execute()
        items = results.get('files', [])
        
        print("Service account can see {} files:".format(len(items)))
        for item in items:
            print("  - {} (ID: {}, Type: {})".format(
                item['name'], 
                item['id'], 
                item.get('mimeType', 'unknown')
            ))
            
    except Exception as e:
        print("Error listing accessible files: {}".format(e))
    
    return False

if __name__ == "__main__":
    print("=== COMPREHENSIVE CREDENTIAL AND API TEST ===")
    success = test_credentials_and_api()
    
    if success:
        print("🎉 SUCCESS! Credentials are working properly")
    else:
        print("❌ FAILED! There's an issue with credentials or permissions")
        print("Next steps:")
        print("1. Verify the folders are shared with the EXACT email from the credentials")
        print("2. Try re-sharing the folders")
        print("3. Check if the service account has the right permissions in Google Cloud Console")