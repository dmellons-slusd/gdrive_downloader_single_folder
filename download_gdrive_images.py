import gspread
import json
import requests
import gdown
import shutil
from os import path
from oauth2client.service_account import ServiceAccountCredentials
from icecream import ic
# from slusdlib import core
# # Unable to install until Python >= 3.8 is installed
# from slusdlib.core import read_gsheet

# # Set Sheet URLs of each site's core sheet here
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
    creds = json.load(open('creds.json'))
    ic(creds)
    image_folder_home = '/var/www/html/images'
    for school,sheet_url in sheet_urls.items():
        if sheet_url == None:
            continue
        
        google_drive_folder_info = read_gsheet(sheet_url,'/home/administrator/gdrive_downloader/creds.json')
        for download_info in google_drive_folder_info:
            folder_url = f"https://drive.google.com/drive/folders/{download_info['Folder ID']}"
            folder_path = f"{image_folder_home}/{school}/{download_info['name']}"
            ic(folder_path)
            if path.exists(folder_path): 
                ic(f'File {folder_path} already exists')
                # continue
                # shutil.rmtree(folder_path)
            ic(folder_url)
            try:
                gdown.download_folder(folder_url, output=folder_path, quiet=False)
            except Exception as e:
                ic(e)
                # core.log(e)
            # response = requests.get(folder_url, headers={'Authorization': 'Bearer {0}'.format(creds['token'])})
            # response.raise_for_status()

            # # Write content to file
            # with open(folder_path, 'wb') as f:
            #     f.write(response.content)

