import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from icecream import ic

def read_gsheet(sheet_url, credentials_file='creds.json', sheet_name='Sheet1',columns=['name','Folder ID']):
    """Your existing read_gsheet function - unchanged"""
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

# Test just one school first
sheet_url = 'https://docs.google.com/spreadsheets/d/1lgXm6YQTCR3AHIjVrSDkgvkVX9cwx-2O-taeP_ss2zw/edit?usp=sharing'

print("Reading Google Sheet data...")
try:
    google_drive_folder_info = read_gsheet(sheet_url, '/home/administrator/gdrive_downloader/creds.json')
    
    print("Found {} folders".format(len(google_drive_folder_info)))
    
    for i, folder_info in enumerate(google_drive_folder_info):
        print("Folder {}: Name='{}', ID='{}'".format(i+1, folder_info.get('name', 'NO NAME'), folder_info.get('Folder ID', 'NO ID')))
        
        # Check if folder ID looks valid (should be around 33 characters)
        folder_id = folder_info.get('Folder ID', '')
        if len(folder_id) < 20:
            print("WARNING: Folder ID '{}' looks too short".format(folder_id))
        elif len(folder_id) > 50:
            print("WARNING: Folder ID '{}' looks too long".format(folder_id))

except Exception as e:
    print("Error reading sheet: {}".format(e))