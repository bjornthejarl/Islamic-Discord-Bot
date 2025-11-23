"""
Audio Compression Script
Compresses MP3 files to reduce size while maintaining reasonable quality.
"""

import os
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compress_audio_file(input_path, output_path, bitrate='64k'):
    """
    Compress an audio file using FFmpeg.
    
    Args:
        input_path: Path to input audio file
        output_path: Path for compressed output file
        bitrate: Target bitrate for compression (default: 64k)
    """
    try:
        # FFmpeg command to compress MP3 with optimized settings
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-codec:a', 'libmp3lame',
            '-b:a', bitrate,
            '-ac', '1',  # Convert to mono to reduce size
            '-ar', '22050',  # Reduce sample rate
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Get file sizes for comparison
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            compression_ratio = (1 - (output_size / input_size)) * 100
            
            logger.info(f"Compressed {os.path.basename(input_path)}: "
                       f"{input_size / 1024 / 1024:.2f}MB -> {output_size / 1024 / 1024:.2f}MB "
                       f"({compression_ratio:.1f}% reduction)")
            
            return True
        else:
            logger.error(f"FFmpeg error for {input_path}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error compressing {input_path}: {e}")
        return False

def compress_all_audio_files(audio_dir='src/audio', temp_dir='temp_compressed'):
    """
    Compress all audio files in the audio directory.
    
    Args:
        audio_dir: Directory containing audio files
        temp_dir: Temporary directory for compressed files
    """
    try:
        # Create temporary directory for compressed files
        temp_path = Path(temp_dir)
        temp_path.mkdir(exist_ok=True)
        
        total_files = 0
        successful_compressions = 0
        
        # Walk through all speaker directories
        for speaker_dir in Path(audio_dir).iterdir():
            if speaker_dir.is_dir():
                speaker_name = speaker_dir.name
                logger.info(f"Processing speaker: {speaker_name}")
                
                # Create speaker subdirectory in temp
                speaker_temp_dir = temp_path / speaker_name
                speaker_temp_dir.mkdir(exist_ok=True)
                
                # Process all MP3 files in speaker directory
                for audio_file in speaker_dir.glob('*.mp3'):
                    total_files += 1
                    
                    # Define output path
                    output_file = speaker_temp_dir / audio_file.name
                    
                    # Compress the file
                    if compress_audio_file(str(audio_file), str(output_file)):
                        successful_compressions += 1
        
        logger.info(f"Compression completed: {successful_compressions}/{total_files} files compressed successfully")
        
        # Ask user if they want to replace original files
        if successful_compressions > 0:
            logger.info(f"Compressed files are available in: {temp_dir}")
            logger.info("You can review the compressed files and replace the originals if satisfied.")
            
        return successful_compressions
        
    except Exception as e:
        logger.error(f"Error in compression process: {e}")
        return 0

def replace_original_files(temp_dir='temp_compressed', audio_dir='src/audio'):
    """
    Replace original audio files with compressed versions.
    
    Args:
        temp_dir: Directory containing compressed files
        audio_dir: Directory containing original audio files
    """
    try:
        replaced_count = 0
        
        # Walk through all speaker directories in temp
        for speaker_dir in Path(temp_dir).iterdir():
            if speaker_dir.is_dir():
                speaker_name = speaker_dir.name
                
                # Process all compressed MP3 files
                for compressed_file in speaker_dir.glob('*.mp3'):
                    # Define original file path
                    original_file = Path(audio_dir) / speaker_name / compressed_file.name
                    
                    if original_file.exists():
                        # Backup original file (optional)
                        # backup_file = original_file.with_suffix('.mp3.backup')
                        # original_file.rename(backup_file)
                        
                        # Replace original with compressed
                        compressed_file.replace(original_file)
                        replaced_count += 1
                        logger.info(f"Replaced: {original_file}")
        
        logger.info(f"Replaced {replaced_count} original files with compressed versions")
        return replaced_count
        
    except Exception as e:
        logger.error(f"Error replacing files: {e}")
        return 0

if __name__ == "__main__":
    logger.info("Starting audio compression...")
    
    # First, compress all files to temporary directory
    success_count = compress_all_audio_files()
    
    if success_count > 0:
        logger.info("Compression completed successfully!")
        logger.info("Compressed files are in 'temp_compressed' directory.")
        
        # Ask user if they want to replace originals
        response = input("Do you want to replace original files with compressed versions? (y/n): ")
        if response.lower() in ['y', 'yes']:
            replaced = replace_original_files()
            logger.info(f"Replaced {replaced} files. You can now delete the 'temp_compressed' directory.")
        else:
            logger.info("Original files preserved. Compressed files remain in 'temp_compressed' directory.")
    else:
        logger.error("No files were compressed successfully.")