from pytube import YouTube

def download_highest_resolution(url: str, output_path: str = "."):
    """
    Downloads the highest resolution video available from the given YouTube URL.
    
    :param url: The YouTube video URL.
    :param output_path: The directory path where the video will be saved.
    """
    try:
        # Create a YouTube object
        yt = YouTube(url)
        
        # Get the highest resolution stream available
        stream = yt.streams.get_highest_resolution()
        
        # Download the stream to the specified output path
        stream.download(output_path)
        
        print(f"Video downloaded successfully: {yt.title}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage:
if __name__ == "__main__":
    video_url = input("Enter YouTube video URL: ")
    download_highest_resolution(video_url)