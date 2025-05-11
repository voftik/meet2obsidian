"""
>4C;L 4;O C?@02;5=8O :>=D83C@0F859 ?@8;>65=8O.
>72>;O5B 703@C60BL, A>E@0=OBL 8 87<5=OBL =0AB@>9:8 ?@8;>65=8O.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union

class ConfigError(Exception):
    """A:;NG5=85 4;O >H81>: :>=D83C@0F88."""
    pass

class ConfigManager:
    """
    #?@02;5=85 :>=D83C@0F859 ?@8;>65=8O.
    15A?5G8205B 703@C7:C, A>E@0=5=85 8 4>ABC? : =0AB@>9:0<.
    """
    
    def __init__(self, config_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        =8F80;870F8O <5=5465@0 :>=D83C@0F88.
        
        Args:
            config_path: CBL : D09;C :>=D83C@0F88. A;8 =5 C:070=, 8A?>;L7C5BAO
                        7=0G5=85 ?> C<>;G0=8N (~/.config/meet2obsidian/config.json).
            logger: 1J5:B ;>335@0. A;8 =5 C:070=, A>7405BAO =>2K9.
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # 0AB@>9:0 ?CB8 : :>=D83C@0F8>==><C D09;C
        if config_path:
            self.config_path = config_path
        else:
            # CBL ?> C<>;G0=8N
            home_dir = os.path.expanduser("~")
            config_dir = os.path.join(home_dir, ".config", "meet2obsidian")
            self.config_path = os.path.join(config_dir, "config.json")
            
        # 03@C7:0 :>=D83C@0F88 8;8 A>740=85 45D>;B=>9
        self.config = self._load_or_create_default()

    def _load_or_create_default(self) -> Dict[str, Any]:
        """
        03@C605B :>=D83C@0F8N 87 D09;0 8;8 A>7405B 45D>;B=CN.
        
        Returns:
            !;>20@L A :>=D83C@0F859.
        """
        # A;8 D09; ACI5AB2C5B, 703@C605< 87 =53>
        if os.path.exists(self.config_path):
            try:
                return self.load_config()
            except Exception as e:
                self.logger.error(f"H81:0 ?@8 703@C7:5 :>=D83C@0F88: {str(e)}")
                return self._get_default_config()
        
        # =0G5 A>7405< 45D>;B=CN :>=D83C@0F8N
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        >72@0I05B :>=D83C@0F8N ?> C<>;G0=8N.
        
        Returns:
            !;>20@L A 45D>;B=>9 :>=D83C@0F859.
        """
        return {
            "paths": {
                "video_directory": os.path.join(os.path.expanduser("~"), "Documents", "meet_records"),
                "obsidian_vault": os.path.join(os.path.expanduser("~"), "Documents", "Obsidian", "Vault"),
                "log_directory": os.path.join(os.path.expanduser("~"), "Library", "Logs", "meet2obsidian")
            },
            "api": {
                "rev_ai": {
                    "job_timeout": 3600,
                    "max_retries": 3
                },
                "claude": {
                    "model": "claude-3-opus-20240229",
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
            },
            "processing": {
                "delete_video_files": True,
                "delete_audio_files": True,
                "process_interval": 60
            },
            "system": {
                "autostart": False,
                "loglevel": "info",
                "notifications": True,
                "max_concurrent_jobs": 1
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """
        03@C605B :>=D83C@0F8N 87 D09;0.
        
        Returns:
            !;>20@L A :>=D83C@0F859.
            
        Raises:
            ConfigError: A;8 D09; :>=D83C@0F88 =5 ACI5AB2C5B 8;8 =5 <>65B 1KBL ?@>G8B0=.
        """
        try:
            if not os.path.exists(self.config_path):
                raise ConfigError(f"$09; :>=D83C@0F88 =5 ACI5AB2C5B: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.debug(f">=D83C@0F8O CA?5H=> 703@C65=0 87 {self.config_path}")
            self.config = config
            return config
        except json.JSONDecodeError as e:
            raise ConfigError(f"H81:0 ?@8 @071>@5 JSON: {str(e)}")
        except Exception as e:
            raise ConfigError(f"H81:0 ?@8 703@C7:5 :>=D83C@0F88: {str(e)}")
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        !>E@0=O5B :>=D83C@0F8N 2 D09;.
        
        Args:
            config: !;>20@L A :>=D83C@0F859 4;O A>E@0=5=8O. A;8 =5 C:070=,
                  A>E@0=O5BAO B5:CI0O :>=D83C@0F8O.
                  
        Returns:
            True 5A;8 A>E@0=5=85 CA?5H=>, 8=0G5 False.
        """
        config_to_save = config if config is not None else self.config
        
        try:
            # !>7405< 48@5:B>@8N, 5A;8 >=0 =5 ACI5AB2C5B
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            
            if config is not None:
                self.config = config
                
            self.logger.debug(f">=D83C@0F8O CA?5H=> A>E@0=5=0 2 {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"H81:0 ?@8 A>E@0=5=88 :>=D83C@0F88: {str(e)}")
            return False
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        >;CG05B 7=0G5=85 87 :>=D83C@0F88 ?> :;NGC.
        >445@68205B 2;>65==K5 :;NG8 G5@57 B>G:C (=0?@8<5@, "api.claude.model").
        
        Args:
            key: ;NG 4;O ?>;CG5=8O 7=0G5=8O.
            default: =0G5=85 ?> C<>;G0=8N, 5A;8 :;NG =5 =0945=.
            
        Returns:
            =0G5=85 87 :>=D83C@0F88 8;8 7=0G5=85 ?> C<>;G0=8N.
        """
        if "." in key:
            # ;>65==K5 :;NG8
            keys = key.split(".")
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        
        # @>AB>9 :;NG
        return self.config.get(key, default)
    
    def set_value(self, key: str, value: Any) -> bool:
        """
        #AB0=02;8205B 7=0G5=85 2 :>=D83C@0F88 ?> :;NGC.
        >445@68205B 2;>65==K5 :;NG8 G5@57 B>G:C (=0?@8<5@, "api.claude.model").
        
        Args:
            key: ;NG 4;O CAB0=>2:8 7=0G5=8O.
            value: =0G5=85 4;O CAB0=>2:8.
            
        Returns:
            True 5A;8 CAB0=>2:0 CA?5H=0, 8=0G5 False.
        """
        try:
            if "." in key:
                # ;>65==K5 :;NG8
                keys = key.split(".")
                config_part = self.config
                
                # @>E>48< ?> 2A5< :;NG0< :@><5 ?>A;54=53>
                for k in keys[:-1]:
                    if k not in config_part:
                        config_part[k] = {}
                    
                    if not isinstance(config_part[k], dict):
                        config_part[k] = {}
                        
                    config_part = config_part[k]
                
                # #AB0=02;8205< 7=0G5=85 =0 ?>A;54=5< C@>2=5
                config_part[keys[-1]] = value
            else:
                # @>AB>9 :;NG
                self.config[key] = value
                
            self.logger.debug(f"#AB0=>2;5=> 7=0G5=85 4;O :;NG0 {key}")
            return True
        except Exception as e:
            self.logger.error(f"H81:0 ?@8 CAB0=>2:5 7=0G5=8O 4;O :;NG0 {key}: {str(e)}")
            return False
    
    def validate_config(self) -> List[str]:
        """
        @>25@O5B :>=D83C@0F8N =0 :>@@5:B=>ABL.
        
        Returns:
            !?8A>: >H81>: 20;840F88. CAB>9 A?8A>:, 5A;8 >H81>: =5B.
        """
        errors = []
        
        # @>25@:0 =0;8G8O >1O70B5;L=KE @0745;>2
        required_sections = ["paths", "api", "processing", "system"]
        for section in required_sections:
            if section not in self.config:
                errors.append(f"BACBAB2C5B >1O70B5;L=K9 @0745;: {section}")
        
        # @>25@:0 =0;8G8O >1O70B5;L=KE ?0@0<5B@>2 2 @0745;5 paths
        if "paths" in self.config:
            required_paths = ["video_directory", "obsidian_vault"]
            for path in required_paths:
                if path not in self.config["paths"]:
                    errors.append(f"BACBAB2C5B >1O70B5;L=K9 ?0@0<5B@ paths.{path}")
        
        # @>25@:0 =0;8G8O >1O70B5;L=KE ?0@0<5B@>2 2 @0745;5 api
        if "api" in self.config:
            required_api_sections = ["rev_ai", "claude"]
            for section in required_api_sections:
                if section not in self.config["api"]:
                    errors.append(f"BACBAB2C5B >1O70B5;L=K9 @0745; api.{section}")
        
        # @>25@:0 B8?>2 40==KE
        if "processing" in self.config:
            processing = self.config["processing"]
            if "delete_video_files" in processing and not isinstance(processing["delete_video_files"], bool):
                errors.append("processing.delete_video_files 4>;65= 1KBL ;>38G5A:8< 7=0G5=85<")
            if "delete_audio_files" in processing and not isinstance(processing["delete_audio_files"], bool):
                errors.append("processing.delete_audio_files 4>;65= 1KBL ;>38G5A:8< 7=0G5=85<")
            if "process_interval" in processing and not isinstance(processing["process_interval"], int):
                errors.append("processing.process_interval 4>;65= 1KBL F5;K< G8A;><")
        
        # @>25@:0 7=0G5=89
        if "api" in self.config and "claude" in self.config["api"]:
            claude = self.config["api"]["claude"]
            if "temperature" in claude:
                temp = claude["temperature"]
                if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
                    errors.append("api.claude.temperature 4>;65= 1KBL G8A;>< >B 0 4> 1")
        
        return errors