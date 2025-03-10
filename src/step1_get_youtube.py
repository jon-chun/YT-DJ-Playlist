import yt_dlp
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import yaml

def load_config():
    """
    Load configuration from config.yaml file.
    Searches for the file in the current directory and parent directories.
    """
    # Find the project root directory
    current_path = Path(__file__).resolve()
    
    # Start with script's parent directory
    script_dir = current_path.parent
    
    # Project root should be one level up from script directory
    root_dir = script_dir.parent
    
    # Try to find config.yaml in the root directory
    config_path = root_dir / "config.yaml"
    
    # Load configuration from config.yaml
    try:
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
            print(f"Loaded config from: {config_path}")
            return config, root_dir
    except Exception as e:
        print(f"Error loading config: {e}")
        # Create default configuration
        config = {
            "YT_CHANNEL": "https://www.youtube.com/watch?v=EptPiz-ZYvM&list=PLJZH8sevmMq6Ao3BUvP3FDOq1CrUxP9-r&index=50",
            "DOWNLOADS": "downloads",
            "MAX_DOWNLOADS": 5
        }
        print(f"Using default config: {config}")
        return config, root_dir

def setup_logging(log_level, output_dir=None):
    """
    Set up logging with the specified log level and file output.
    
    Args:
        log_level (str): Logging level - DEBUG, INFO, NONE, etc.
        output_dir (Path, optional): Directory to save log file
    """
    # Reset handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_levels = {
        "DEBUG": logging.DEBUG, 
        "INFO": logging.INFO, 
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "NONE": logging.CRITICAL + 1  # Higher than any defined level
    }
    
    # Configure console logging
    logging.basicConfig(
        level=log_levels.get(log_level, logging.INFO), 
        format=log_format
    )
    
    # Add file handler if output directory is provided
    if output_dir:
        # Make sure the output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create and add the file handler
        log_file = output_dir / f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
        
        # Log the file path
        print(f"Logging to file: {log_file}")
        logging.info(f"Logging to file: {log_file}")
    
    # If NONE is selected, disable all logging
    if log_level == "NONE":
        logging.disable(logging.CRITICAL)

def get_video_url(url_with_playlist):
    """
    Extract the video URL from a URL that might contain playlist information.
    
    Args:
        url_with_playlist (str): URL that might contain playlist information
        
    Returns:
        str: Clean video URL without playlist parameters
    """
    if '&list=' in url_with_playlist and 'v=' in url_with_playlist:
        video_id = url_with_playlist.split('v=')[1].split('&')[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url_with_playlist

def extract_urls_from_playlist(url, max_downloads):
    """
    Extract individual video URLs from a playlist URL.
    
    Args:
        url (str): YouTube playlist URL
        max_downloads (int): Maximum number of videos to extract
        
    Returns:
        list: List of video URLs
    """
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'playlistend': max_downloads,
        'ignoreerrors': True,
    }
    
    # First, try to get the actual video URL if this is a video within a playlist
    if 'watch?v=' in url and 'list=' in url:
        video_id = url.split('watch?v=')[1].split('&')[0]
        url_list = [f"https://www.youtube.com/watch?v={video_id}"]
        logging.info(f"Found video in playlist URL: {url_list[0]}")
        
        # If max_downloads is 1, just return this single video
        if max_downloads == 1:
            return url_list
    else:
        url_list = []
    
    # Then extract the playlist
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # If this is a video in a playlist, extract just the playlist ID
            if 'list=' in url:
                playlist_id = url.split('list=')[1].split('&')[0]
                playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
                logging.info(f"Extracting playlist: {playlist_url}")
            else:
                playlist_url = url
            
            playlist_info = ydl.extract_info(playlist_url, download=False)
            if 'entries' in playlist_info:
                for entry in playlist_info['entries']:
                    if entry and len(url_list) < max_downloads:
                        video_id = entry.get('id')
                        if video_id:
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            # Only add if not already present
                            if video_url not in url_list:
                                url_list.append(video_url)
                                logging.info(f"Found video in playlist: {video_url}")
    except Exception as e:
        logging.error(f"Failed to extract playlist: {e}")
    
    # Ensure we don't exceed max_downloads
    return url_list[:max_downloads]

def is_playlist(url):
    """
    Check if the URL is a playlist.
    
    Args:
        url (str): YouTube URL
        
    Returns:
        bool: True if URL is a playlist, False otherwise
    """
    return 'list=' in url

def download_video(video_url, output_dir, type, size, language, video_format, audio_format, log_level):
    """
    Download a single video from YouTube.
    
    Args:
        video_url (str): YouTube video URL
        output_dir (Path): Directory to save the video
        type (str): 'video' or 'audio'
        size (str): Video height in pixels
        language (str): Preferred language code
        video_format (str): Video format extension
        audio_format (str): Audio format extension
        log_level (str): Logging level
        
    Returns:
        tuple: (success, title)
    """
    # Make sure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Format specification - enforce requested format
    if type == 'video':
        # Explicitly specify format with extension
        format_spec = f'bestvideo[ext={video_format}][height<={size}]+bestaudio[ext={audio_format}]/best[ext={video_format}]'
    else:  # audio
        format_spec = f'bestaudio[ext={audio_format}]'
    
    # Download options
    download_opts = {
        'format': format_spec,
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'quiet': log_level == "NONE",
        'noplaylist': True,
        'merge_output_format': video_format if type == 'video' else audio_format,
        'ignoreerrors': True,
        'no_warnings': False,
        'verbose': log_level == "DEBUG",
    }
    
    # Add postprocessors for audio extraction if type is 'audio'
    if type == 'audio':
        download_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': '192',
        }]
    elif type == 'video':
        # For video, ensure the output format is correct
        download_opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': video_format,
        }]
    
    # Print download options for debugging
    logging.debug(f"Download options: {download_opts}")
    logging.info(f"Downloading to: {output_dir}")
    logging.info(f"Format spec: {format_spec}")
    
    try:
        # Simplify the download process to increase reliability
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            # First get info to get the title
            info_dict = ydl.extract_info(video_url, download=False)
            if info_dict is None:
                logging.error(f"Could not extract info for {video_url}")
                return False, "Unknown (Info extraction failed)"
            
            # Get the title before download
            title = info_dict.get('title', 'Unknown Title')
            logging.info(f"Downloading: {title}")
            
            # Now download
            ydl.download([video_url])
            
            # Prepare the expected filename
            filename = ydl.prepare_filename(info_dict)
            base_filename = Path(filename).stem
            
            # Check if any file with this base name exists in the output directory
            matching_files = list(output_dir.glob(f"{base_filename}.*"))
            
            if matching_files:
                logging.info(f"Successfully downloaded: {title}")
                logging.info(f"File saved as: {matching_files[0]}")
                
                # Verify format
                file_ext = matching_files[0].suffix.lower()[1:]  # Remove the dot
                expected_ext = video_format if type == 'video' else audio_format
                
                if file_ext != expected_ext:
                    logging.warning(f"File format is {file_ext}, expected {expected_ext}")
                
                return True, title
            else:
                logging.error(f"File not found after download: {base_filename}.*")
                # List all files in the directory for debugging
                all_files = list(output_dir.glob("*"))
                logging.debug(f"Files in directory: {[f.name for f in all_files]}")
                return False, title
    except Exception as e:
        logging.error(f"Failed to download {video_url}: {e}")
        return False, f"Unknown (Error: {str(e)})"

def get_youtube(url=None, type='video', size='760', language='en', video='mp4', audio='mp3', log_level='INFO'):
    """
    Download YouTube videos or audio tracks.
    
    Args:
        url (str): YouTube URL (single video or playlist)
        type (str): 'video' or 'audio'
        size (str): Video height in pixels
        language (str): Preferred language code
        video (str): Video format extension
        audio (str): Audio format extension
        log_level (str): Logging level
        
    Returns:
        tuple: (success_count, fail_count, report_path)
    """
    # Load configuration
    config, root_dir = load_config()
    
    # Use URL from config if not provided
    if url is None:
        url = config.get("YT_CHANNEL")
    
    # Set up output directory at project root (parent of src)
    downloads_dir = config.get("DOWNLOADS", "downloads")
    output_dir = root_dir / downloads_dir
    
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Download directory set to: {output_dir}")
    
    # Set up logging with file output
    setup_logging(log_level, output_dir)
    
    logging.info(f"Using URL from config: {url}")
    logging.info(f"Download directory: {output_dir}")
    
    # Validate type parameter
    if type not in ['video', 'audio']:
        logging.error("Invalid type. Choose 'video' or 'audio'.")
        return 0, 0, None
    
    # Get maximum downloads limit
    max_downloads = config.get("MAX_DOWNLOADS", 5)
    logging.info(f"Maximum downloads limit set to: {max_downloads}")
    logging.info(f"Video format specified: {video}")
    logging.info(f"Audio format specified: {audio}")
    
    # Determine if URL is a playlist or single video
    url_ls = []
    
    # Use direct download approach for any URL
    if 'list=' in url:
        logging.info(f"Playlist detected: {url}")
        # First try to extract the playlist
        url_ls = extract_urls_from_playlist(url, max_downloads)
        logging.info(f"Found {len(url_ls)} videos in playlist (limited to {max_downloads})")
        
        # If no videos found but it's a video in a playlist, try to get just the video
        if not url_ls and 'watch?v=' in url:
            video_id = url.split('watch?v=')[1].split('&')[0]
            clean_url = f"https://www.youtube.com/watch?v={video_id}"
            url_ls.append(clean_url)
            logging.info(f"Falling back to single video: {clean_url}")
    else:
        # Single video
        clean_url = get_video_url(url)
        url_ls.append(clean_url)
        logging.info(f"Single video detected: {clean_url}")
    
    if not url_ls:
        # Last resort - try direct download
        logging.warning("No videos found in playlist - trying direct download")
        url_ls.append(url)
        
    if not url_ls:
        logging.error("No valid URLs found to download")
        return 0, 0, None
    
    # Create report file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"report_{timestamp}.txt"
    report_path = output_dir / report_filename
    
    # Initialize counters and report
    success_count, fail_count = 0, 0
    report_lines = [
        "YouTube Download Report\n", 
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"Download Type: {type}\n",
        f"Max Downloads: {max_downloads}\n",
        "="*50 + "\n\n"
    ]
    
    # Process each video URL
    for idx, video_url in enumerate(url_ls, 1):
        logging.info(f"Processing video {idx}/{len(url_ls)}: {video_url}")
        
        success, title = download_video(
            video_url, 
            output_dir, 
            type, 
            size, 
            language, 
            video, 
            audio, 
            log_level
        )
        
        if success:
            report_lines.append(f"SUCCESS: {title} - {video_url}\n")
            success_count += 1
        else:
            report_lines.append(f"FAILED: {video_url} - Unable to download\n")
            fail_count += 1
    
    # Add summary to report
    report_lines.append("\n" + "="*50 + "\n")
    report_lines.append(f"Download Summary:\n")
    report_lines.append(f"Total Processed: {len(url_ls)}\n")
    report_lines.append(f"Total Success: {success_count}\n")
    report_lines.append(f"Total Failures: {fail_count}\n")
    
    if len(url_ls) > 0:
        report_lines.append(f"Success Rate: {(success_count/len(url_ls))*100:.1f}%\n")
    
    # Write report to file
    with open(report_path, "w") as report_file:
        report_file.writelines(report_lines)
    
    logging.info(f"Report saved: {report_path}")
    return success_count, fail_count, report_path

def main():
    """
    Main function to handle command line arguments.
    """
    # Get the root directory
    config, root_dir = load_config()
    print(f"Project root: {root_dir}")
    print(f"Downloads directory: {root_dir}/{config.get('DOWNLOADS', 'downloads')}")
    
    if len(sys.argv) < 2:
        # No arguments provided, use defaults from config
        get_youtube()
    else:
        # Use command line arguments
        get_youtube(*sys.argv[1:])

if __name__ == "__main__":
    main()