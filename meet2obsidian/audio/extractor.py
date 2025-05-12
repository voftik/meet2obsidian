"""
>4C;L 4;O 872;5G5=8O 0C48> 87 2845>D09;>2.

-B>B <>4C;L A>45@68B DC=:F88 8 :;0AAK 4;O >1@01>B:8 2845>D09;>2,
872;5G5=8O 0C48>4>@>65: 8 ?>43>B>2:8 8E 4;O ?>A;54CNI59 B@0=A:@8?F88.
"""

import os
import subprocess
import json
import logging
from typing import Optional, Dict, Any, Tuple

from meet2obsidian.utils.logging import get_logger


class AudioExtractor:
    """
    ;0AA 4;O 872;5G5=8O 0C48> 87 2845>D09;>2.
    
    A?>;L7C5B ffmpeg 4;O 872;5G5=8O 0C48>4>@>65: 87 2845>D09;>2
    8 ?>43>B>2:8 8E : B@0=A:@8?F88.
    """
    
    def __init__(self, logger=None):
        """
        =8F80;870F8O M:AB@0:B>@0 0C48>.
        
        Args:
            logger: ?F8>=0;L=K9 ;>335@. A;8 =5 C:070=, 1C45B A>740= =>2K9.
        """
        self.logger = logger or get_logger('audio.extractor')
        
    def check_video_file(self, video_path: str) -> Tuple[bool, Optional[str]]:
        """
        @>25@O5B 2845>D09; =0 G8B05<>ABL 8 :>@@5:B=>ABL.
        
        Args:
            video_path: CBL : 2845>D09;C
            
        Returns:
            Tuple[bool, Optional[str]]: (CA?5E, A>>1I5=85 >1 >H81:5)
        """
        if not os.path.exists(video_path):
            return False, f"$09; =5 ACI5AB2C5B: {video_path}"
            
        if not os.access(video_path, os.R_OK):
            return False, f"5B ?@02 =0 GB5=85 D09;0: {video_path}"
        
        # @>25@O5< D09; A ?><>ILN ffprobe
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return False, f"H81:0 ?@8 ?@>25@:5 D09;0: {result.stderr}"
                
            data = json.loads(result.stdout)
            
            # @>25@O5<, 5ABL ;8 8=D>@<0F8O > 4;8B5;L=>AB8
            if 'format' not in data or 'duration' not in data['format']:
                return False, "5 C40;>AL >?@545;8BL 4;8B5;L=>ABL 2845>"
                
            duration = float(data['format']['duration'])
            if duration <= 0:
                return False, f"5:>@@5:B=0O 4;8B5;L=>ABL 2845>: {duration} A5:C=4"
                
            return True, None
            
        except Exception as e:
            self.logger.exception(f"H81:0 ?@8 ?@>25@:5 2845>D09;0 {video_path}")
            return False, f"H81:0 ?@8 ?@>25@:5 D09;0: {str(e)}"
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None, 
                     format: str = 'wav', bitrate: str = '128k',
                     channels: int = 1, sample_rate: int = 16000) -> Tuple[bool, Optional[str]]:
        """
        72;5:05B 0C48>4>@>6:C 87 2845>D09;0.
        
        Args:
            video_path: CBL : 2845>D09;C
            output_path: CBL 4;O A>E@0=5=8O 0C48>. A;8 =5 C:070=, 1C45B 8A?>;L7>20=
                         ?CBL 2845> A 87<5=5==K< @0AH8@5=85<.
            format: $>@<0B 2KE>4=>3> 0C48>D09;0 (wav, mp3, etc.)
            bitrate: 8B@59B 2KE>4=>3> 0C48>
            channels: >;8G5AB2> :0=0;>2 (1 4;O <>=>, 2 4;O AB5@5>)
            sample_rate: '0AB>B0 48A:@5B870F88 2 F
            
        Returns:
            Tuple[bool, Optional[str]]: (CA?5E, ?CBL : 0C48>D09;C 8;8 A>>1I5=85 >1 >H81:5)
        """
        # @>25@O5< 2845>D09; ?5@54 >1@01>B:>9
        is_valid, error_msg = self.check_video_file(video_path)
        if not is_valid:
            self.logger.error(f"52>7<>6=> 872;5GL 0C48> 87 =520;84=>3> 2845>D09;0: {error_msg}")
            return False, error_msg
        
        # A;8 ?CBL 2K2>40 =5 C:070=, A>7405< 53> =0 >A=>25 ?CB8 : 2845>
        if output_path is None:
            base_path = os.path.splitext(video_path)[0]
            output_path = f"{base_path}.{format}"
        
        self.logger.info(f"72;5G5=85 0C48> 87 {video_path} 2 {output_path}")
        
        try:
            # ><0=40 ffmpeg 4;O 872;5G5=8O 0C48>
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # B:;NG05< 2845>?>B>:
                '-ar', str(sample_rate),  # '0AB>B0 48A:@5B870F88
                '-ac', str(channels),     # >;8G5AB2> :0=0;>2
                '-b:a', bitrate,          # 8B@59B 0C48>
                '-f', format,             # $>@<0B 2K2>40
                '-y',                     # 5@570?8AK205< D09;, 5A;8 ACI5AB2C5B
                output_path
            ]
            
            # 0?CA:05< ?@>F5AA
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # @>25@O5< @57C;LB0B
            if result.returncode != 0:
                self.logger.error(f"H81:0 ?@8 872;5G5=88 0C48>: {result.stderr}")
                return False, f"H81:0 ?@8 872;5G5=88 0C48>: {result.stderr}"
                
            # @>25@O5<, A>740= ;8 D09;
            if not os.path.exists(output_path):
                return False, "C48>D09; =5 1K; A>740="
                
            self.logger.info(f"C48> CA?5H=> 872;5G5=>: {output_path}")
            return True, output_path
            
        except Exception as e:
            self.logger.exception(f"A:;NG5=85 ?@8 872;5G5=88 0C48> 87 {video_path}")
            return False, f"H81:0 ?@8 872;5G5=88 0C48>: {str(e)}"
    
    def get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        >;CG05B <5B040==K5 2845>D09;0 (4;8B5;L=>ABL, @07@5H5=85, :>45: 8 B.4.).
        
        Args:
            video_path: CBL : 2845>D09;C
            
        Returns:
            Optional[Dict[str, Any]]: !;>20@L A 8=D>@<0F859 > 2845> 8;8 None 2 A;CG05 >H81:8
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"H81:0 ?@8 ?>;CG5=88 8=D>@<0F88 > 2845>: {result.stderr}")
                return None
                
            # 0@A8< JSON->B25B
            info = json.loads(result.stdout)
            
            # 72;5:05< 8 >1@010BK205< =081>;55 206=CN 8=D>@<0F8N
            processed_info = {
                'filename': os.path.basename(video_path),
                'full_path': video_path,
                'format_name': info.get('format', {}).get('format_name', 'unknown'),
                'duration': float(info.get('format', {}).get('duration', 0)),
                'size': int(info.get('format', {}).get('size', 0)),
                'bit_rate': int(info.get('format', {}).get('bit_rate', 0)),
                'streams': []
            }
            
            # 1@010BK205< 8=D>@<0F8N > ?>B>:0E
            for stream in info.get('streams', []):
                stream_info = {
                    'codec_type': stream.get('codec_type'),
                    'codec_name': stream.get('codec_name'),
                }
                
                # >102;O5< 8=D>@<0F8N > 2845>-?>B>:5
                if stream.get('codec_type') == 'video':
                    stream_info.update({
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'display_aspect_ratio': stream.get('display_aspect_ratio'),
                        'fps': stream.get('r_frame_rate')
                    })
                
                # >102;O5< 8=D>@<0F8N > 0C48>-?>B>:5
                elif stream.get('codec_type') == 'audio':
                    stream_info.update({
                        'sample_rate': stream.get('sample_rate'),
                        'channels': stream.get('channels'),
                        'channel_layout': stream.get('channel_layout')
                    })
                
                processed_info['streams'].append(stream_info)
            
            return processed_info
            
        except Exception as e:
            self.logger.exception(f"A:;NG5=85 ?@8 ?>;CG5=88 8=D>@<0F88 > 2845> {video_path}")
            return None