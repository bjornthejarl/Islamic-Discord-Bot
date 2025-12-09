"""
Audio Re-Compression Script (Ultra Mode)
Compresses existing OGG files to ultra-low bitrate Opus (8k).
"""

import os
import subprocess
import logging
import shutil
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AudioCompressor")

def compress_audio_file(input_path, output_path):
    """
    Compress audio to Ultra-Low Opus format using FFmpeg.
    Target: 8k bitrate, 12000Hz, Mono.
    """
    try:
        # Check if output is the same as input (in-place replacement)
        # We need a temp file for in-place
        temp_output = str(Path(output_path).with_suffix('.temp.ogg'))
        
        # FFmpeg command
        # -c:a libopus : Use Opus codec
        # -b:a 6k : 6kbps bitrate (Extreme compression)
        # -vbr on : Variable bitrate
        # -ac 1 : Mono
        # -ar 8000 : Narrowband (Walkie-talkie quality)
        # -frame_duration 60 : 60ms frames for less overhead
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:a', 'libopus',
            '-b:a', '6k',
            '-vbr', 'on',
            '-compression_level', '10',
            '-frame_duration', '60',
            '-application', 'voip',
            '-ac', '1',
            '-ar', '8000',
            '-map_metadata', '-1',
            '-y',
            temp_output
        ]
        
        # Suppress FFmpeg output unless error
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(temp_output)
            
            # If temp is smaller, replace original
            if output_size < input_size:
                shutil.move(temp_output, output_path)
                ratio = (1 - (output_size / input_size)) * 100
                logger.info(f"✅ {os.path.basename(input_path)}: {input_size/1024/1024:.2f}MB -> {output_size/1024/1024:.2f}MB ({ratio:.1f}%)")
                return True, (input_size - output_size)
            else:
                logger.info(f"⚠️ {os.path.basename(input_path)}: New file not smaller, keeping original.")
                os.remove(temp_output)
                return True, 0
        else:
            logger.error(f"❌ FFmpeg error for {input_path}: {result.stderr}")
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return False, 0
            
    except Exception as e:
        logger.error(f"❌ Exception compressing {input_path}: {e}")
        return False, 0

def process_directory(base_dir='src/audio'):
    """
    Process all OGG files in directory, re-compressing them.
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        logger.error(f"Directory {base_dir} not found.")
        return

    logger.info(f"Scanning {base_dir} for re-compression...")
    
    total_space_saved = 0
    file_count = 0
    
    # Iterate through all subdirectories
    for file_path in base_path.rglob('*.ogg'):
        # Output is same file
        success, saved = compress_audio_file(str(file_path), str(file_path))
        if success:
            file_count += 1
            total_space_saved += saved
                
    logger.info("-" * 40)
    logger.info(f"🎉 Re-Compression Complete!")
    logger.info(f"Files processed: {file_count}")
    logger.info(f"Total space saved: {total_space_saved / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    process_directory()