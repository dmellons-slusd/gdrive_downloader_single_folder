import gspread
import gdown
import shutil
from os import path
from oauth2client.service_account import ServiceAccountCredentials
# Unable to install until Python >= 3.8 is installed
# from slusdlib.core import read_gsheet
# Set Sheet URLs here
sheet_urls = {
        'slusd':'https://docs.google.com/spreadsheets/d/1lgXm6YQTCR3AHIjVrSDkgvkVX9cwx-2O-taeP_ss2zw/edit?usp=sharing',
        'garfield': None,
        'jefferson':'https://docs.google.com/spreadsheets/d/1LYA0097njxt58udNwTohsTJTcGB4fK34o4XOv9B_8qk/edit#gid=0',
        'madison': None,
        'mckinley': None,
        'monrow': None,
        'roosevelt': None,
        'washington': None,
        'wilson': None,
        'bancroft': None,
        'muir': None,
        'lincoln': None,
        'slhs': None,
        'adult': None
    } 

def read_gsheet(sheet_url, credentials_file='creds.json', sheet_name='Sheet1',columns=['name','Folder ID']):
    """Reads google sheet information. Sheet MUST be accessable to anyone with the link

    Args:
        sheet_url (str): The full URL of the shared google sheet. Copied when sharing the link.
        credentials_file (str/json): Credentials file to access the google sheets API in JSON format. Defaults to 'creds.json'
        sheet_name (str, optional): The name of the sheet in the workbook. Defaults to 'Sheet1'.
        columns (list, optional): List of column headers you want to return information for. Defaults to ['name','url'].

    Returns:
        folders (object list): Returns list of folder objects containing the information described in "columns" 
    """
    # Set google scope and credential variables
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_url)
    sheet = spreadsheet.worksheet(sheet_name)    
    data = sheet.get_all_records()

    # Initializing folders list to append to
    folders = []

    # Loop though gsheet data
    for row in data:
        # Initiate emply folder object
        folder = {}
        # Loop though columns list to build folder object
        for column in columns:
            folder[column] = row[column]
        # Append folder object to folders list 
        folders.append(folder)
    
    return folders

        
if __name__ == "__main__":
    """
    !NOTICE! All google drives folders must be shared with below account with VIEW access
    gsheets-service@polar-winter-333619.iam.gserviceaccount.com

    """
    
    image_folder_home = '/var/www/html/images'
    for school,sheet_url in sheet_urls.items():
        if sheet_url == None:
            continue
        print('~~~Sheet Exists~~~~: ' ,sheet_url)
        google_drive_folder_info = read_gsheet(sheet_url,'/home/administrator/gdrive_downloader/creds.json')
        for download_info in google_drive_folder_info:
            folder_url = f"https://drive.google.com/drive/folders/{download_info['Folder ID']}"
            folder_path = f"{image_folder_home}/{school}/{download_info['name']}"
            if path.exists(folder_path):
                shutil.rmtree(folder_path)
            gdown.download_folder(folder_url, output=folder_path, quiet=False)

