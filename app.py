import streamlit as st
import yt_dlp
import os
import tempfile
import time
import re

st.set_page_config(page_title="🎬 MP4 Downloader", layout="centered")

st.markdown("""
<h2 style="text-align:center;">🎞️ MP4 Downloader with All Qualities</h2>
<p style="text-align:center;">Shows all MP4 formats up to 1080p (auto-merge video+audio if needed).</p>
<hr>
""", unsafe_allow_html=True)

url = st.text_input("🔗 Paste Video URL", placeholder="https://www.youtube.com/watch?v=xyz")

if url:
    with st.spinner("🔍 Fetching formats..."):
        try:
            ydl_opts = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get("formats", [])
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

    allowed_qualities = [144, 240, 360, 480, 720, 1080]
    format_options = []
    format_map = {}

    best_video_formats = {}

    for f in formats:
        if f.get("ext") == "mp4" and f.get("vcodec") != "none":
            height = f.get("height")
            if height in allowed_qualities:
                if height not in best_video_formats or (f.get("filesize", 0) > best_video_formats[height].get("filesize", 0)):
                    best_video_formats[height] = f

    max_available_height = max(best_video_formats.keys(), default=0)
    max_height = min(max_available_height, 1080)

    for h in allowed_qualities:
        if h <= max_height and h in best_video_formats:
            f = best_video_formats[h]
            size = f.get("filesize", 0)
            size_mb = f"{round(size / (1024 * 1024), 1)} MB" if size else "Unknown size"
            label = f"{f['format_id']} - {h}p - {f.get('fps', 'N/A')}fps - {size_mb}"
            format_options.append(label)
            format_map[label] = f["format_id"]

    if not format_options:
        st.warning("⚠️ No MP4 formats found up to 1080p.")
        st.stop()

    selected = st.selectbox("🎞 Select Quality", format_options)

    if st.button("⬇️ Download"):
        format_id = format_map[selected]
        progress_text = st.empty()
        progress_bar = st.progress(0)

        temp_dir = tempfile.mkdtemp()
        outtmpl = os.path.join(temp_dir, "%(title)s.%(ext)s")

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        def progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').strip()
                downloaded = d.get('_downloaded_bytes_str', '0B')
                total = d.get('_total_bytes_str', '0B')
                speed = d.get('_speed_str', '0B/s')

                # Remove ANSI color codes
                downloaded = ansi_escape.sub('', downloaded)
                total = ansi_escape.sub('', total)
                speed = ansi_escape.sub('', speed)
                percent_num = float(percent.replace('%', '').strip() or 0)

                progress_bar.progress(int(percent_num))
                progress_text.text(f"📦 {percent} downloaded: {downloaded} / {total} at {speed}")

        ydl_opts = {
            'format': f"{format_id}+bestaudio",
            'merge_output_format': 'mp4',
            'outtmpl': outtmpl,
            'ffmpeg_location': '',  # Leave empty for auto detection (Render friendly)
            'quiet': True,
            'progress_hooks': [progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            files = os.listdir(temp_dir)
            video_file = [f for f in files if f.endswith(".mp4")]
            if not video_file:
                st.error("❌ Download failed.")
                st.stop()

            path = os.path.join(temp_dir, video_file[0])
            with open(path, "rb") as f:
                st.success("✅ Video downloaded!")
                st.download_button("📥 Save MP4", f, file_name=os.path.basename(path), mime="video/mp4")
        except Exception as e:
            st.error(f"❌ Download error: {e}")
