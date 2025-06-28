#!/usr/bin/env python3
"""
Backup and Versioning System for MatYouAI
Handles safe backup and restoration of configuration files
"""

import json
import logging
import shutil
import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class ConfigBackupManager:
    """Manages backups and versioning of configuration files"""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        self.home_dir = Path.home()
        self.backup_dir = backup_dir or (self.home_dir / ".config" / "matyouai" / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load backup metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading backup metadata: {e}")
        
        return {
            "backups": {},
            "current_theme": None,
            "theme_history": []
        }
    
    def _save_metadata(self):
        """Save backup metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving backup metadata: {e}")
    
    def create_backup(self, file_path: str, app_name: str, reason: str = "auto") -> Optional[str]:
        """Create a backup of a configuration file"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                logger.error(f"Source file not found: {file_path}")
                return None
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{app_name}_{timestamp}_{reason}.backup"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(source_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return f"{app_name}_{timestamp}"
            
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return None
    
    def restore_backup(self, backup_id: str, create_current_backup: bool = True) -> bool:
        """Restore a configuration file from backup"""
        try:
            if backup_id not in self.metadata["backups"]:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            backup_info = self.metadata["backups"][backup_id]
            backup_path = Path(backup_info["backup_path"])
            original_path = Path(backup_info["original_path"])
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create backup of current file before restoring
            if create_current_backup and original_path.exists():
                self.create_backup(str(original_path), backup_info["app"], "pre_restore")
            
            # Restore the backup
            shutil.copy2(backup_path, original_path)
            
            # Verify integrity
            restored_hash = self._calculate_file_hash(original_path)
            if restored_hash == backup_info["file_hash"]:
                logger.info(f"Successfully restored backup: {backup_id}")
                return True
            else:
                logger.warning(f"Hash mismatch after restore: {backup_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring backup {backup_id}: {e}")
            return False
    
    def list_backups(self, app_name: Optional[str] = None) -> List[Dict]:
        """List available backups"""
        backups = []
        
        for backup_id, backup_info in self.metadata["backups"].items():
            if app_name is None or backup_info["app"] == app_name:
                backup_info_copy = backup_info.copy()
                backup_info_copy["backup_id"] = backup_id
                
                # Add human-readable timestamp
                try:
                    dt = datetime.datetime.strptime(backup_info["timestamp"], "%Y%m%d_%H%M%S")
                    backup_info_copy["readable_time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    backup_info_copy["readable_time"] = backup_info["timestamp"]
                
                backups.append(backup_info_copy)
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10, keep_days: int = 30) -> int:
        """Clean up old backups based on count and age"""
        removed_count = 0
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        
        # Group backups by app
        app_backups = {}
        for backup_id, backup_info in self.metadata["backups"].items():
            app = backup_info["app"]
            if app not in app_backups:
                app_backups[app] = []
            app_backups[app].append((backup_id, backup_info))
        
        # Process each app's backups
        for app, backups in app_backups.items():
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x[1]["timestamp"], reverse=True)
            
            # Keep specified number of newest backups
            to_remove = backups[keep_count:]
            
            # Also remove old backups beyond the day threshold
            for backup_id, backup_info in backups:
                try:
                    backup_dt = datetime.datetime.strptime(backup_info["timestamp"], "%Y%m%d_%H%M%S")
                    if backup_dt < cutoff_date and (backup_id, backup_info) not in to_remove:
                        to_remove.append((backup_id, backup_info))
                except:
                    continue
            
            # Remove the selected backups
            for backup_id, backup_info in to_remove:
                if self._remove_backup(backup_id):
                    removed_count += 1
        
        self._save_metadata()
        logger.info(f"Cleaned up {removed_count} old backups")
        return removed_count
    
    def _remove_backup(self, backup_id: str) -> bool:
        """Remove a specific backup"""
        try:
            if backup_id not in self.metadata["backups"]:
                return False
            
            backup_info = self.metadata["backups"][backup_id]
            backup_path = Path(backup_info["backup_path"])
            
            if backup_path.exists():
                backup_path.unlink()
            
            del self.metadata["backups"][backup_id]
            return True
            
        except Exception as e:
            logger.error(f"Error removing backup {backup_id}: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def create_theme_snapshot(self, theme_name: str, color_palette: Dict, applied_configs: Dict) -> str:
        """Create a snapshot of the current theme configuration"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_id = f"theme_{theme_name}_{timestamp}"
            
            # Create backups of all modified files
            backup_ids = []
            for app_name, config_files in applied_configs.items():
                for config_file in config_files:
                    backup_id = self.create_backup(config_file, app_name, f"theme_{theme_name}")
                    if backup_id:
                        backup_ids.append(backup_id)
            
            # Store theme information
            theme_info = {
                "snapshot_id": snapshot_id,
                "theme_name": theme_name,
                "timestamp": timestamp,
                "color_palette": color_palette,
                "applied_configs": applied_configs,
                "backup_ids": backup_ids,
                "readable_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.metadata["theme_history"].append(theme_info)
            self.metadata["current_theme"] = theme_info
            self._save_metadata()
            
            logger.info(f"Created theme snapshot: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Error creating theme snapshot: {e}")
            return ""
    
    def restore_theme_snapshot(self, snapshot_id: str) -> bool:
        """Restore a complete theme snapshot"""
        try:
            theme_info = None
            for theme in self.metadata["theme_history"]:
                if theme["snapshot_id"] == snapshot_id:
                    theme_info = theme
                    break
            
            if not theme_info:
                logger.error(f"Theme snapshot not found: {snapshot_id}")
                return False
            
            # Restore all backup files
            success_count = 0
            for backup_id in theme_info["backup_ids"]:
                if self.restore_backup(backup_id, create_current_backup=False):
                    success_count += 1
            
            if success_count == len(theme_info["backup_ids"]):
                self.metadata["current_theme"] = theme_info
                self._save_metadata()
                logger.info(f"Successfully restored theme snapshot: {snapshot_id}")
                return True
            else:
                logger.warning(f"Partially restored theme snapshot: {success_count}/{len(theme_info['backup_ids'])} files")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring theme snapshot {snapshot_id}: {e}")
            return False
    
    def list_theme_snapshots(self) -> List[Dict]:
        """List all theme snapshots"""
        return sorted(self.metadata.get("theme_history", []), 
                     key=lambda x: x["timestamp"], reverse=True)
    
    def get_current_theme(self) -> Optional[Dict]:
        """Get information about the current theme"""
        return self.metadata.get("current_theme")
    
    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verify the integrity of a backup file"""
        try:
            if backup_id not in self.metadata["backups"]:
                return False
            
            backup_info = self.metadata["backups"][backup_id]
            backup_path = Path(backup_info["backup_path"])
            
            if not backup_path.exists():
                return False
            
            # Check file size
            current_size = backup_path.stat().st_size
            if current_size != backup_info["file_size"]:
                logger.warning(f"Size mismatch for backup {backup_id}")
                return False
            
            # Check hash if available
            if "file_hash" in backup_info:
                current_hash = self._calculate_file_hash(backup_path)
                if current_hash != backup_info["file_hash"]:
                    logger.warning(f"Hash mismatch for backup {backup_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying backup {backup_id}: {e}")
            return False
    
    def get_backup_statistics(self) -> Dict:
        """Get statistics about backups"""
        total_backups = len(self.metadata["backups"])
        total_size = 0
        apps = set()
        
        for backup_info in self.metadata["backups"].values():
            total_size += backup_info.get("file_size", 0)
            apps.add(backup_info["app"])
        
        return {
            "total_backups": total_backups,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "apps_with_backups": len(apps),
            "backup_directory": str(self.backup_dir),
            "theme_snapshots": len(self.metadata.get("theme_history", []))
        } 