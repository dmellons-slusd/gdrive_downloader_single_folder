# Google Drive file downloader

## Summary

Downloads images from hard coded google drive folders for website menu "random image"


## Errors

### I set the permission 'Anyone with Link', but I still can't download.
Google restricts access to a file when the download is concentrated. If you can still access to the file from your browser, downloading cookies file might help. Follow this step: 1) download cookies.txt using browser extensions like [(Get cookies.txt LOCALLY)](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) ; 2) mv the cookies.txt to ~/.cache/gdown/cookies.txt; 3) run download again. If you're using gdown>=5.0.0, it should be able to use the cookies same as your browser.