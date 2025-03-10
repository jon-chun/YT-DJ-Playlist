# Project Description

## YouTube Channel

* [Postmodern Jukebox: 40s channel](https://www.youtube.com/watch?v=EptPiz-ZYvM&list=PLJZH8sevmMq6Ao3BUvP3FDOq1CrUxP9-r&index=50)

## PROMPT

###CODE:
import yt_dlp
import os
import sys
import logging
from datetime import datetime

def setup_logging(log_level):
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_levels = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "NONE": logging.CRITICAL}
    logging.basicConfig(level=log_levels.get(log_level, logging.INFO), format=log_format)

def get_youtube(url, type='video', size='760', language='en', video='mp4', audio='mp3', log_level='INFO'):
    setup_logging(log_level)
    
    if type not in ['video', 'audio']:
        logging.error("Invalid type. Choose 'video' or 'audio'.")
        return
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
    }
    
    logging.info(f"Checking if URL is a single video or playlist: {url}")
    url_ls = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                url_ls = [entry['url'] for entry in info['entries'] if entry]
                logging.info(f"Playlist detected with {len(url_ls)} videos.")
            else:
                url_ls.append(url)
                logging.info("Single video detected.")
    except Exception as e:
        logging.error(f"Error fetching video info: {e}")
        return
    
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_path = os.path.join(output_dir, report_filename)
    
    success_count, fail_count = 0, 0
    report_lines = ["YouTube Download Report\n", "="*50 + "\n"]
    
    for video_url in url_ls:
        logging.info(f"Processing {video_url}")
        
        download_opts = {
            'format': f'bestvideo[ext={video}][height={size}]+bestaudio[ext={audio}]' if type == 'video' else f'bestaudio[ext={audio}]',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': audio}] if type == 'audio' else [],
        }
        
        try:
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                result = ydl.download([video_url])
                if result == 0:
                    logging.info(f"Successfully downloaded: {video_url}")
                    report_lines.append(f"SUCCESS: {video_url}\n")
                    success_count += 1
                else:
                    raise Exception("Download failed")
        except Exception as e:
            logging.error(f"Failed to download {video_url}: {e}")
            report_lines.append(f"FAILED: {video_url} - {e}\n")
            fail_count += 1
    
    report_lines.append("="*50 + "\n")
    report_lines.append(f"Total Success: {success_count}\n")
    report_lines.append(f"Total Failures: {fail_count}\n")
    
    with open(report_path, "w") as report_file:
        report_file.writelines(report_lines)
    
    logging.info(f"Report saved: {report_path}")
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <youtube_url> [type] [size] [language] [video] [audio] [log_level]")
        sys.exit(1)
    
    get_youtube(*sys.argv[1:])

###INSTRUCTIONS:
Create a python program /src/step1_get_yt-videos.py improving/revising ###CODE that:
1. Define the globals in config.yaml as:
1.a. YT_CHANNEL = "https://www.youtube.com/watch?v=EptPiz-ZYvM&list=PLJZH8sevmMq6Ao3BUvP3FDOq1CrUxP9-r&index=50"
2.b. DOWNLOADS= use Path so the program can be executed from root or /src or any subdir using .__parent__ / .. / downloads
2. /src/step1_get_yt-videos.py that
2.a. downloads all the videos 
write a python program get_youtube(url, type='video', size='760', language='en', video='mp4', audio='mp3') where type in ['video','audio'] and if type=='video' downloads videos else if type=='audio' downloads audio tracks (else quit) the program:
1. first checks if the URL is a single video or a playlist and creates a list url_ls that contains the urls to each individual item to download
2. then checks to see if the requested url_ls exist in the specificed (or default) size, language, video or audio formats) and skips/quits if not available
3. one by one downloads the requested url_ls
- NOTE: has robust try/catch to gracefully catch/continue in case of missing file/misconfiguration
- NOTE: provides flexible parameterized log_level in ['DEBUG','INFO','NONE', etc] and informative terminal print/logging before and after each successful/failed downlods
- NOTE: generates a final report_{datetime_stamp}.txt with concise, logical and well organized human readable reports