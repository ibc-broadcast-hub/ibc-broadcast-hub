import os
import csv
import requests
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# The high-speed live export link to your Google Sheet
GSHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/1F1uwpkUmbBQGr6u0qfAiWkfnyPs4FxwIG6MvbjK9k-o/export?format=csv'
DEFAULT_FAILOVER = 'https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4' # Temporary valid raw file for testing

def get_row_index_by_time():
    hour = datetime.now().hour
    if 0 <= hour < 4:   return 1  # Slot 1
    if 4 <= hour < 8:   return 2  # Slot 2
    if 8 <= hour < 12:  return 3  # Slot 3
    if 12 <= hour < 16: return 4  # Slot 4
    if 16 <= hour < 20: return 5  # Slot 5
    return 6                      # Slot 6

@app.route('/roku-feed', methods=['GET'])
def generate_roku_feed():
    try:
        # Fetch the live spreadsheet data
        response = requests.get(GSHEET_CSV_URL, timeout=10)
        if response.status_code != 200:
            raise Exception("Unable to reach Google Sheets")
            
        lines = response.text.splitlines()
        reader = list(csv.reader(lines))
        
        target_row = get_row_index_by_time()
        
        # Pull Column D (Index 3)
        stream_link = DEFAULT_FAILOVER
        if len(reader) > target_row and len(reader[target_row]) > 3:
            grid_value = reader[target_row][3].strip()
            if grid_value:
                # If it's a raw video format link, use it. Otherwise, use failover for testing.
                if grid_value.startswith('http') or '.m3u8' in grid_value or '.mp4' in grid_value:
                    stream_link = grid_value
                else:
                    # If it's still a YouTube ID, we pass it out so you can see it working, 
                    # but remember Roku needs an http link to play natively!
                    stream_link = grid_value 

    except Exception as e:
        print(f"Error parsing sheet: {e}")
        stream_link = DEFAULT_FAILOVER

    # Build the official Roku Direct Publisher JSON Structure
    roku_feed = {
        "providerName": "IBC/TTWDI NEWS Network",
        "lastUpdated": datetime.utcnow().isoformat() + "Z",
        "liveFeeds": [
            {
                "id": "ibc-master-control-live",
                "title": "IBC Master Control Live",
                "description": "Live breaking news, investigative reporting, and weather updates.",
                "thumbnail": "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=500", # Placeholder channel graphic
                "branding": {
                    "playlistColor": "#ef4444",
                    "backgroundColor": "#0f172a"
                },
                "content": {
                    "dateAdded": "2026-01-01T00:00:00Z",
                    "videos": [
                        {
                            "url": stream_link,
                            "quality": "HD",
                            "videoType": "hls" if ".m3u8" in stream_link else "mp4"
                        }
                    ],
                    "duration": 0,
                    "isLive": True
                }
            }
        ]
    }
    
    return jsonify(roku_feed)

if __name__ == '__main__':
    # Bind to port assigned by hosting platform
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
