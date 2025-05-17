from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
from auth import require_custom_authentication
from dotenv import load_dotenv
import logging
import asyncio
import tiktoken

load_dotenv()

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_youtube_id(url):
    # Extract video ID from YouTube URL
    video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return video_id.group(1) if video_id else None

def process_transcript(video_id):
    proxy_http_address=os.environ.get("PROXY_HTTP")
    proxy_https_address=os.environ.get("PROXY_HTTPS")

    if proxy_http_address is None:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

    else:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies = {"http": proxy_http_address,"https": proxy_https_address})
    
    full_text = ' '.join([entry['text'] for entry in transcript])
    return full_text

@app.route('/transcribe', methods=['POST'])
@require_custom_authentication
def transcribe():
    youtube_url = request.json.get('url')
    if not youtube_url:
        return jsonify({"error": "No YouTube URL provided"}), 400

    video_id = get_youtube_id(youtube_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    try:
        logger.info(f"videoid = {video_id}")
        transcript_text = process_transcript(video_id)
        logger.info(f"text = {transcript_text}")
        return jsonify({"result": transcript_text})
    
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
