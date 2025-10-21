log_file="/home/administrator/gdrive_downloader/log.log"
start=$(date)
echo "$start - Started Downloading images" >> $log_file
sudo python3 /home/administrator/gdrive_downloader/main_sync_rate_limit.py
end=$(date)
echo "$end - Completed downloading images" >> $log_file
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~" >> $log_file


