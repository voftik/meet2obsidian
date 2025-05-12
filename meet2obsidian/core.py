"""
A=>2=>9 <>4C;L meet2obsidian.

-B>B <>4C;L A>45@68B :;NG52K5 :;0AAK 4;O @01>BK ?@8;>65=8O, 2:;NG0O C?@02;5=85
A>AB>O=85< ?@8;>65=8O, <>=8B>@8=3 D09;>2 8 >A=>2=>9 ?>B>: >1@01>B:8.
"""

import os
import sys
import time
import json
import subprocess
import datetime
import logging
from typing import Dict, List, Any, Optional

from meet2obsidian.utils.logging import get_logger


class ApplicationManager:
    """
    #?@02;5=85 A>AB>O=85< ?@8;>65=8O meet2obsidian.
    
    -B>B :;0AA >B25G05B 70 70?CA: 8 >AB0=>2:C >A=>2=KE ?@>F5AA>2 ?@8;>65=8O,
    0 B0:65 70 >BA;56820=85 53> A>AB>O=8O 8 C?@02;5=85 02B>70?CA:><.
    """
    
    def __init__(self, logger=None):
        """
        =8F80;870F8O <5=5465@0 ?@8;>65=8O.
        
        Args:
            logger: ?F8>=0;L=K9 ;>335@. A;8 =5 C:070=, 1C45B A>740= =>2K9.
        """
        self.logger = logger or get_logger('core.app_manager')
        self._pid_file = os.path.expanduser('~/Library/Application Support/meet2obsidian/meet2obsidian.pid')
        self._start_time = None
        
        # @>25@O5< ACI5AB2>20=85 48@5:B>@88 4;O PID D09;0
        os.makedirs(os.path.dirname(self._pid_file), exist_ok=True)
    
    def is_running(self) -> bool:
        """
        @>25@:0, 70?CI5=> ;8 ?@8;>65=85.
        
        Returns:
            bool: True 5A;8 ?@8;>65=85 70?CI5=>, 8=0G5 False
        """
        if not os.path.exists(self._pid_file):
            return False
        
        try:
            with open(self._pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # @>25@O5< ACI5AB2>20=85 ?@>F5AA0 A MB8< PID
            return self._check_process_exists(pid)
        except Exception as e:
            self.logger.error(f"H81:0 ?@8 ?@>25@:5 AB0BCA0 ?@8;>65=8O: {str(e)}")
            return False
    
    def start(self) -> bool:
        """
        0?CA: ?@8;>65=8O.
        
        Returns:
            bool: True 5A;8 ?@8;>65=85 CA?5H=> 70?CI5=>, 8=0G5 False
        """
        if self.is_running():
            self.logger.warning("@8;>65=85 C65 70?CI5=>")
            return True
        
        # TODO:  50;87>20BL @50;L=K9 70?CA: ?@8;>65=8O
        #  40==>9 25@A88 ?@>AB> A>7405< PID D09; A B5:CI8< PID
        
        try:
            # 0?8AK205< B5:CI89 PID 2 D09;
            with open(self._pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            self._start_time = datetime.datetime.now()
            self.logger.info("@8;>65=85 CA?5H=> 70?CI5=>")
            return True
        except Exception as e:
            self.logger.error(f"H81:0 ?@8 70?CA:5 ?@8;>65=8O: {str(e)}")
            return False
    
    def stop(self, force=False) -> bool:
        """
        AB0=>2:0 ?@8;>65=8O.
        
        Args:
            force: @8=C48B5;L=0O >AB0=>2:0
            
        Returns:
            bool: True 5A;8 ?@8;>65=85 CA?5H=> >AB0=>2;5=>, 8=0G5 False
        """
        if not self.is_running():
            self.logger.warning("@8;>65=85 =5 70?CI5=>")
            return True
        
        try:
            # >;CG05< PID ?@>F5AA0
            with open(self._pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # TODO:  50;87>20BL @50;L=CN >AB0=>2:C ?@8;>65=8O
            #  40==>9 25@A88 ?@>AB> C40;O5< PID D09;
            
            # #40;O5< PID D09;
            os.remove(self._pid_file)
            
            self._start_time = None
            self.logger.info("@8;>65=85 CA?5H=> >AB0=>2;5=>")
            return True
        except Exception as e:
            self.logger.error(f"H81:0 ?@8 >AB0=>2:5 ?@8;>65=8O: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        >;CG5=85 ?>;=>9 8=D>@<0F88 > AB0BCA5 ?@8;>65=8O.
        
        Returns:
            dict: !;>20@L A 8=D>@<0F859 > AB0BCA5
        """
        status = {
            "running": self.is_running(),
            "processed_files": 0,
            "pending_files": 0,
            "active_jobs": [],
            "last_errors": []
        }
        
        if status["running"] and self._start_time:
            #  0AG5B 2@5<5=8 @01>BK
            uptime = datetime.datetime.now() - self._start_time
            hours, remainder = divmod(uptime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            status["uptime"] = f"{int(hours)}G {int(minutes)}< {int(seconds)}A"
            
            # TODO: >1028BL @50;L=CN AB0B8AB8:C > D09;0E 8 7040G0E
        
        return status
    
    def setup_autostart(self, enable=True) -> bool:
        """
        0AB@>9:0 02B>70?CA:0 G5@57 LaunchAgent.
        
        Args:
            enable: True 4;O 2:;NG5=8O 02B>70?CA:0, False 4;O >B:;NG5=8O
            
        Returns:
            bool: True 5A;8 =0AB@>9:0 2K?>;=5=0 CA?5H=>, 8=0G5 False
        """
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.user.meet2obsidian.plist")
        
        if enable:
            # (01;>= plist D09;0
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.meet2obsidian</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>meet2obsidian</string>
        <string>service</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>~/Library/Logs/meet2obsidian/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>~/Library/Logs/meet2obsidian/stderr.log</string>
</dict>
</plist>
"""
            # !>7405< 48@5:B>@88 4;O ;>3>2
            os.makedirs(os.path.expanduser("~/Library/Logs/meet2obsidian"), exist_ok=True)
            
            # 0?8AK205< plist D09;
            try:
                with open(plist_path, "w") as f:
                    f.write(plist_content)
                    
                # 03@C605< 035=B
                result = subprocess.run(["launchctl", "load", plist_path], capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"H81:0 ?@8 703@C7:5 LaunchAgent: {result.stderr}")
                    return False
                    
                self.logger.info(f"LaunchAgent CAB0=>2;5= 8 703@C65=: {plist_path}")
                return True
            except Exception as e:
                self.logger.error(f"H81:0 ?@8 =0AB@>9:5 02B>70?CA:0: {str(e)}")
                return False
        else:
            # K3@C605< 8 C40;O5< 035=B
            if os.path.exists(plist_path):
                try:
                    # K3@C605< 035=B
                    result = subprocess.run(["launchctl", "unload", plist_path], capture_output=True, text=True)
                    if result.returncode != 0:
                        self.logger.error(f"H81:0 ?@8 2K3@C7:5 LaunchAgent: {result.stderr}")
                        return False
                    
                    # #40;O5< D09;
                    os.remove(plist_path)
                    self.logger.info(f"LaunchAgent 2K3@C65= 8 C40;5=: {plist_path}")
                    return True
                except Exception as e:
                    self.logger.error(f"H81:0 ?@8 >B:;NG5=88 02B>70?CA:0: {str(e)}")
                    return False
            return True  # A;8 D09;0 =5B, AG8B05< GB> 02B>70?CA: C65 >B:;NG5=
    
    def _check_process_exists(self, pid: int) -> bool:
        """
        @>25@:0 ACI5AB2>20=8O ?@>F5AA0 A C:070==K< PID.
        
        Args:
            pid: 45=B8D8:0B>@ ?@>F5AA0
            
        Returns:
            bool: True 5A;8 ?@>F5AA ACI5AB2C5B, 8=0G5 False
        """
        try:
            #  Unix A8AB5<0E, 5A;8 ?@>F5AA =5 ACI5AB2C5B, 1C45B 2K1@>H5=> 8A:;NG5=85
            os.kill(pid, 0)
            return True
        except OSError:
            return False
        except Exception:
            return False