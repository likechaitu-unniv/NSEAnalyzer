"""
Trend Data Storage - Write and Read methods for UI trend analysis
Stores historical trend data (PCR, Greeks, Market sentiment, etc.) to a JSON file
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class TrendStorage:
    """Handle writing and reading trend data for UI visualization"""
    
    def __init__(self, expiry: str = None, base_filename: str = "trend_history"):
        """
        Initialize TrendStorage
        
        Args:
            expiry: Expiry date (e.g., '06-Jan-2026'). If provided, creates expiry-specific file
            base_filename: Base name for the JSON file (default: trend_history)
        """
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Create filename based on expiry date
        if expiry:
            # Convert expiry format to filename format (e.g., '06-Jan-2026' -> 'trend_06Jan2026.json')
            expiry_clean = expiry.replace('-', '').replace(' ', '')
            self.filename = f"{base_filename}_{expiry_clean}.json"
            self.expiry = expiry
        else:
            self.filename = f"{base_filename}.json"
            self.expiry = None
        
        self.filepath = self.data_dir / self.filename
        
        # Initialize file if it doesn't exist
        if not self.filepath.exists():
            self._initialize_file()
    
    def _initialize_file(self):
        """Create initial trend file structure"""
        initial_data = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "expiry": self.expiry,
            "trends": []
        }
        self.write_to_file(initial_data)
        print(f"[INFO] Initialized trend storage for expiry {self.expiry}: {self.filepath}")
    
    def write_trend(self, trend_data: Dict[str, Any]) -> bool:
        """
        Write a single trend entry to the file
        
        Args:
            trend_data: Dictionary containing trend information
                       Must include keys like: timestamp, nifty_value, pcr, sentiment, etc.
        
        Returns:
            bool: True if successful, False otherwise
        
        Example:
            trend_data = {
                'timestamp': '2025-01-05 14:30:00',
                'nifty_value': 23456.50,
                'pcr_oi': 1.15,
                'pcr_volume': 1.08,
                'sentiment': 'bullish',
                'iv_rank': 65,
                'call_oi': 234567,
                'put_oi': 245678
            }
        """
        try:
            data = self.read_from_file()
            
            # Add metadata
            trend_data['timestamp'] = trend_data.get('timestamp', datetime.now().isoformat())
            trend_data['recorded_at'] = datetime.now().isoformat()
            
            # Append new trend
            data['trends'].append(trend_data)
            data['last_updated'] = datetime.now().isoformat()
            
            self.write_to_file(data)
            print(f"[INFO] Trend recorded: {trend_data.get('timestamp')}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write trend: {e}")
            return False
    
    def write_multiple_trends(self, trends_list: List[Dict[str, Any]]) -> bool:
        """
        Write multiple trend entries at once
        
        Args:
            trends_list: List of trend dictionaries
        
        Returns:
            bool: True if all successful
        """
        try:
            data = self.read_from_file()
            
            for trend_data in trends_list:
                trend_data['timestamp'] = trend_data.get('timestamp', datetime.now().isoformat())
                trend_data['recorded_at'] = datetime.now().isoformat()
                data['trends'].append(trend_data)
            
            data['last_updated'] = datetime.now().isoformat()
            self.write_to_file(data)
            print(f"[INFO] Recorded {len(trends_list)} trends")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write multiple trends: {e}")
            return False
    
    def read_all_trends(self) -> List[Dict[str, Any]]:
        """
        Read all trend entries from the file
        
        Returns:
            List of all trend dictionaries
        """
        try:
            data = self.read_from_file()
            print(f"[INFO] Retrieved {len(data['trends'])} trends")
            return data['trends']
        except Exception as e:
            print(f"[ERROR] Failed to read trends: {e}")
            return []
    
    def read_recent_trends(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Read the most recent trend entries
        
        Args:
            limit: Number of recent trends to retrieve
        
        Returns:
            List of recent trend dictionaries
        """
        try:
            trends = self.read_all_trends()
            print(f"[DEBUG] read_recent_trends: got {len(trends)} total trends, returning last {limit}")
            return trends[-limit:] if trends else []
        except Exception as e:
            print(f"[ERROR] Failed to read recent trends: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def read_trends_by_timerange(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """
        Read trends within a specific time range
        
        Args:
            start_time: Start time in ISO format (e.g., '2025-01-05T10:00:00')
            end_time: End time in ISO format (e.g., '2025-01-05T16:00:00')
        
        Returns:
            List of trends within the time range
        """
        try:
            all_trends = self.read_all_trends()
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            
            filtered_trends = [
                t for t in all_trends
                if start_dt <= datetime.fromisoformat(t.get('timestamp', '')) <= end_dt
            ]
            print(f"[INFO] Retrieved {len(filtered_trends)} trends in time range")
            return filtered_trends
        except Exception as e:
            print(f"[ERROR] Failed to read trends by time range: {e}")
            return []
    
    def read_trends_by_sentiment(self, sentiment: str) -> List[Dict[str, Any]]:
        """
        Read trends filtered by sentiment
        
        Args:
            sentiment: 'bullish', 'bearish', or 'neutral'
        
        Returns:
            List of trends with matching sentiment
        """
        try:
            all_trends = self.read_all_trends()
            filtered_trends = [t for t in all_trends if t.get('sentiment') == sentiment]
            print(f"[INFO] Retrieved {len(filtered_trends)} {sentiment} trends")
            return filtered_trends
        except Exception as e:
            print(f"[ERROR] Failed to read trends by sentiment: {e}")
            return []
    
    def get_pcr_analysis(self) -> Dict[str, Any]:
        """
        Analyze PCR (Put-Call Ratio) data of the day
        
        Returns:
            Dictionary with PCR statistics including:
            - highest_pcr: Highest PCR value of the day
            - lowest_pcr: Lowest PCR value of the day
            - current_pcr: Latest PCR value
            - pcr_direction: Direction PCR is moving ('up', 'down', 'neutral')
            - pcr_change: Change from lowest to current
            - pcr_trend: Trend description
        """
        try:
            trends = self.read_all_trends()
            if not trends:
                return {
                    "highest_pcr": None,
                    "lowest_pcr": None,
                    "current_pcr": None,
                    "pcr_direction": "N/A",
                    "pcr_change": 0,
                    "pcr_trend": "No data available"
                }
            
            # Extract PCR OI values
            pcr_values = []
            for trend in trends:
                pcr_oi = trend.get('pcr_oi')
                if pcr_oi is not None:
                    pcr_values.append({
                        'timestamp': trend.get('timestamp'),
                        'pcr_oi': pcr_oi,
                        'pcr_volume': trend.get('pcr_volume')
                    })
            
            if not pcr_values:
                return {
                    "highest_pcr": None,
                    "lowest_pcr": None,
                    "current_pcr": None,
                    "pcr_direction": "N/A",
                    "pcr_change": 0,
                    "pcr_trend": "No PCR data available"
                }
            
            # Calculate statistics
            pcr_oi_list = [v['pcr_oi'] for v in pcr_values]
            highest_pcr = round(max(pcr_oi_list), 3)
            lowest_pcr = round(min(pcr_oi_list), 3)
            current_pcr = round(pcr_oi_list[-1], 3)
            
            # Determine direction and track previous PCR
            previous_pcr = pcr_oi_list[-2] if len(pcr_oi_list) >= 2 else current_pcr
            
            if len(pcr_oi_list) >= 2:
                if current_pcr > previous_pcr:
                    direction = "up"
                    pcr_change = round(current_pcr - previous_pcr, 3)
                elif current_pcr < previous_pcr:
                    direction = "down"
                    pcr_change = round(current_pcr - previous_pcr, 3)
                else:
                    direction = "neutral"
                    pcr_change = 0.0
            else:
                direction = "neutral"
                pcr_change = 0.0
            
            # Determine trend description
            if current_pcr > 1.2:
                trend_desc = "STRONG BULLISH - Moving up from support"
            elif current_pcr > 1.0:
                trend_desc = "BULLISH - Strong put support"
            elif current_pcr > 0.8:
                trend_desc = "NEUTRAL - Balanced sentiment"
            elif current_pcr > 0.5:
                trend_desc = "BEARISH - Call buying dominance"
            else:
                trend_desc = "STRONG BEARISH - Call heavy"
            
            if direction == "down" and current_pcr < lowest_pcr * 1.05:
                trend_desc += " - Near day's low"
            elif direction == "up" and current_pcr > highest_pcr * 0.95:
                trend_desc += " - Near day's high"
            
            stats = {
                "highest_pcr": highest_pcr,
                "lowest_pcr": lowest_pcr,
                "current_pcr": current_pcr,
                "pcr_range": round(highest_pcr - lowest_pcr, 3),
                "pcr_direction": direction,
                "pcr_change": pcr_change,
                "pcr_change_percent": round((pcr_change / previous_pcr * 100) if len(pcr_oi_list) >= 2 and previous_pcr != 0 else 0, 2),
                "pcr_trend": trend_desc,
                "data_points": len(pcr_values),
                "high_timestamp": pcr_values[pcr_oi_list.index(max(pcr_oi_list))]['timestamp'],
                "low_timestamp": pcr_values[pcr_oi_list.index(min(pcr_oi_list))]['timestamp']
            }
            return stats
        except Exception as e:
            print(f"[ERROR] Failed to analyze PCR: {e}")
            return {
                "highest_pcr": None,
                "lowest_pcr": None,
                "current_pcr": None,
                "pcr_direction": "error",
                "pcr_change": 0,
                "pcr_trend": f"Error: {str(e)}"
            }
    
    def get_pcr_change_2min(self) -> Dict[str, Any]:
        """
        Calculate PCR change over the last 2 minutes
        
        Returns:
            Dictionary with:
            - pcr_change_2min: Change value
            - pcr_change_direction: 'positive', 'negative', or 'neutral'
            - pcr_change_percent: Percentage change
            - current_pcr: Latest PCR value
            - previous_pcr: PCR value from ~2 minutes ago
            - timestamp_current: Current timestamp
            - timestamp_previous: Previous timestamp
        """
        try:
            trends = self.read_all_trends()
            if len(trends) < 2:
                return {
                    "pcr_change_2min": 0,
                    "pcr_change_direction": "neutral",
                    "pcr_change_percent": 0,
                    "current_pcr": trends[-1].get('pcr_oi', 0) if trends else 0,
                    "previous_pcr": None,
                    "timestamp_current": trends[-1].get('timestamp') if trends else None,
                    "timestamp_previous": None,
                    "data_insufficient": True
                }
            
            # Get current PCR
            current_trend = trends[-1]
            current_pcr = current_trend.get('pcr_oi', 0)
            current_timestamp = current_trend.get('timestamp')
            
            # Find trend from ~2 minutes ago (120 seconds)
            from datetime import timedelta
            current_time = datetime.fromisoformat(current_timestamp)
            target_time = current_time - timedelta(minutes=2)
            
            # Find the closest trend within the 2-minute window
            previous_trend = None
            min_time_diff = float('inf')
            
            for trend in reversed(trends[:-1]):  # Exclude the current trend
                trend_time = datetime.fromisoformat(trend.get('timestamp'))
                time_diff = abs((current_time - trend_time).total_seconds())
                
                # Find trend closest to 120 seconds ago
                if 100 <= time_diff <= 140:  # Allow 20 second tolerance
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        previous_trend = trend
            
            # If exact 2-min window not found, use the oldest available trend
            if previous_trend is None and len(trends) > 1:
                previous_trend = trends[-2]
            
            if previous_trend is None:
                return {
                    "pcr_change_2min": 0,
                    "pcr_change_direction": "neutral",
                    "pcr_change_percent": 0,
                    "current_pcr": current_pcr,
                    "previous_pcr": None,
                    "timestamp_current": current_timestamp,
                    "timestamp_previous": None,
                    "data_insufficient": True
                }
            
            previous_pcr = previous_trend.get('pcr_oi', 0)
            previous_timestamp = previous_trend.get('timestamp')
            
            # Calculate change
            pcr_change = round(current_pcr - previous_pcr, 4)
            
            # Determine direction
            if pcr_change > 0:
                direction = "positive"
            elif pcr_change < 0:
                direction = "negative"
            else:
                direction = "neutral"
            
            # Calculate percentage change
            pcr_change_percent = round((pcr_change / previous_pcr * 100) if previous_pcr != 0 else 0, 2)
            
            return {
                "pcr_change_2min": pcr_change,
                "pcr_change_direction": direction,
                "pcr_change_percent": pcr_change_percent,
                "current_pcr": current_pcr,
                "previous_pcr": previous_pcr,
                "timestamp_current": current_timestamp,
                "timestamp_previous": previous_timestamp,
                "data_insufficient": False
            }
        except Exception as e:
            print(f"[ERROR] Failed to calculate PCR 2min change: {e}")
            import traceback
            traceback.print_exc()
            return {
                "pcr_change_2min": 0,
                "pcr_change_direction": "neutral",
                "pcr_change_percent": 0,
                "current_pcr": 0,
                "previous_pcr": None,
                "timestamp_current": None,
                "timestamp_previous": None,
                "error": str(e)
            }
    
    def get_pcr_changes_multiple_timeframes(self) -> Dict[str, Any]:
        """
        Calculate PCR changes for multiple timeframes (1 min, 2 min, 5 min, 10 min)
        
        Returns:
            Dictionary with PCR changes for each timeframe:
            {
                '1min': { pcr_change_1min, pcr_change_direction, pcr_change_percent, ... },
                '2min': { pcr_change_2min, pcr_change_direction, pcr_change_percent, ... },
                '5min': { pcr_change_5min, pcr_change_direction, pcr_change_percent, ... },
                '10min': { pcr_change_10min, pcr_change_direction, pcr_change_percent, ... },
                'current_pcr': current value,
                'data_insufficient': bool
            }
        """
        try:
            trends = self.read_all_trends()
            if len(trends) < 2:
                return {
                    "1min": {
                        "pcr_change": 0,
                        "pcr_change_direction": "neutral",
                        "pcr_change_percent": 0,
                        "data_insufficient": True
                    },
                    "2min": {
                        "pcr_change": 0,
                        "pcr_change_direction": "neutral",
                        "pcr_change_percent": 0,
                        "data_insufficient": True
                    },
                    "5min": {
                        "pcr_change": 0,
                        "pcr_change_direction": "neutral",
                        "pcr_change_percent": 0,
                        "data_insufficient": True
                    },
                    "10min": {
                        "pcr_change": 0,
                        "pcr_change_direction": "neutral",
                        "pcr_change_percent": 0,
                        "data_insufficient": True
                    },
                    "current_pcr": trends[-1].get('pcr_oi', 0) if trends else 0,
                    "data_insufficient": True
                }
            
            # Get current trend
            current_trend = trends[-1]
            current_pcr = current_trend.get('pcr_oi', 0)
            current_timestamp = current_trend.get('timestamp')
            current_time = datetime.fromisoformat(current_timestamp)
            
            from datetime import timedelta
            
            # Define timeframes
            timeframes = {
                '1min': {'seconds': 60, 'tolerance': 15},
                '2min': {'seconds': 120, 'tolerance': 20},
                '5min': {'seconds': 300, 'tolerance': 30},
                '10min': {'seconds': 600, 'tolerance': 45}
            }
            
            result = {
                'current_pcr': current_pcr,
                'current_timestamp': current_timestamp,
                'data_insufficient': False
            }
            
            for tf_name, tf_config in timeframes.items():
                target_seconds = tf_config['seconds']
                tolerance = tf_config['tolerance']
                
                target_time = current_time - timedelta(seconds=target_seconds)
                
                # Find the closest trend within the timeframe window
                previous_trend = None
                min_time_diff = float('inf')
                
                for trend in reversed(trends[:-1]):  # Exclude current trend
                    trend_time = datetime.fromisoformat(trend.get('timestamp'))
                    time_diff = abs((current_time - trend_time).total_seconds())
                    
                    # Find trend closest to target time
                    if (target_seconds - tolerance) <= time_diff <= (target_seconds + tolerance):
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            previous_trend = trend
                
                # If exact window not found, use oldest available if less than 2x timeframe
                if previous_trend is None and len(trends) > 1:
                    oldest_trend = trends[0]
                    oldest_time = datetime.fromisoformat(oldest_trend.get('timestamp'))
                    oldest_diff = (current_time - oldest_time).total_seconds()
                    if oldest_diff <= target_seconds * 2:  # Within 2x the timeframe
                        previous_trend = oldest_trend
                
                if previous_trend is None:
                    result[tf_name] = {
                        "pcr_change": 0,
                        "pcr_change_direction": "neutral",
                        "pcr_change_percent": 0,
                        "data_insufficient": True,
                        "previous_pcr": None,
                        "timestamp": None
                    }
                    continue
                
                previous_pcr = previous_trend.get('pcr_oi', 0)
                previous_timestamp = previous_trend.get('timestamp')
                
                # Calculate change
                pcr_change = round(current_pcr - previous_pcr, 4)
                
                # Determine direction
                if pcr_change > 0:
                    direction = "positive"
                elif pcr_change < 0:
                    direction = "negative"
                else:
                    direction = "neutral"
                
                # Calculate percentage change
                pcr_change_percent = round((pcr_change / previous_pcr * 100) if previous_pcr != 0 else 0, 2)
                
                result[tf_name] = {
                    "pcr_change": pcr_change,
                    "pcr_change_direction": direction,
                    "pcr_change_percent": pcr_change_percent,
                    "previous_pcr": previous_pcr,
                    "timestamp": previous_timestamp,
                    "data_insufficient": False
                }
            
            return result
        except Exception as e:
            print(f"[ERROR] Failed to calculate PCR multiple timeframes: {e}")
            import traceback
            traceback.print_exc()
            return {
                "1min": {
                    "pcr_change": 0,
                    "pcr_change_direction": "neutral",
                    "pcr_change_percent": 0,
                    "error": str(e)
                },
                "2min": {
                    "pcr_change": 0,
                    "pcr_change_direction": "neutral",
                    "pcr_change_percent": 0,
                    "error": str(e)
                },
                "5min": {
                    "pcr_change": 0,
                    "pcr_change_direction": "neutral",
                    "pcr_change_percent": 0,
                    "error": str(e)
                },
                "current_pcr": 0,
                "error": str(e)
            }
    
    def get_trend_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored trends
        
        Returns:
            Dictionary with statistics like count, date range, sentiment breakdown
        """
        try:
            trends = self.read_all_trends()
            if not trends:
                return {
                    "total_trends": 0,
                    "sentiment_breakdown": {},
                    "pcr_analysis": {
                        "highest_pcr": None,
                        "lowest_pcr": None,
                        "current_pcr": None,
                        "pcr_direction": "N/A",
                        "pcr_change": 0,
                        "pcr_trend": "No data available"
                    }
                }
            
            sentiments = {}
            for trend in trends:
                sentiment = trend.get('sentiment', 'unknown')
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            # Include PCR analysis
            pcr_analysis = self.get_pcr_analysis()
            
            stats = {
                "total_trends": len(trends),
                "first_trend": trends[0].get('timestamp'),
                "last_trend": trends[-1].get('timestamp'),
                "sentiment_breakdown": sentiments,
                "file_path": str(self.filepath),
                "file_size_kb": round(os.path.getsize(self.filepath) / 1024, 2),
                "pcr_analysis": pcr_analysis
            }
            return stats
        except Exception as e:
            print(f"[ERROR] Failed to get statistics: {e}")
            import traceback
            traceback.print_exc()
            return {
                "total_trends": 0,
                "sentiment_breakdown": {},
                "pcr_analysis": {
                    "highest_pcr": None,
                    "lowest_pcr": None,
                    "current_pcr": None,
                    "pcr_direction": "error",
                    "pcr_change": 0,
                    "pcr_trend": f"Error: {str(e)}"
                }
            }
    
    def clear_old_trends(self, keep_last_n: int = 500) -> bool:
        """
        Delete old trends keeping only the most recent N
        
        Args:
            keep_last_n: Number of recent trends to keep
        
        Returns:
            bool: True if successful
        """
        try:
            data = self.read_from_file()
            original_count = len(data['trends'])
            
            if original_count > keep_last_n:
                data['trends'] = data['trends'][-keep_last_n:]
                self.write_to_file(data)
                removed = original_count - keep_last_n
                print(f"[INFO] Removed {removed} old trends, kept {keep_last_n}")
                return True
            return True
        except Exception as e:
            print(f"[ERROR] Failed to clear old trends: {e}")
            return False
    
    def export_to_csv(self, output_filename: str = "trends_export.csv") -> bool:
        """
        Export trends to CSV file
        
        Args:
            output_filename: Name of CSV file to create
        
        Returns:
            bool: True if successful
        """
        try:
            import csv
            trends = self.read_all_trends()
            if not trends:
                print("[WARNING] No trends to export")
                return False
            
            output_path = self.data_dir / output_filename
            
            # Get all keys from all trends
            all_keys = set()
            for trend in trends:
                all_keys.update(trend.keys())
            
            fieldnames = sorted(list(all_keys))
            
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(trends)
            
            print(f"[INFO] Exported {len(trends)} trends to {output_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to export to CSV: {e}")
            return False
    
    def write_to_file(self, data: Dict[str, Any]):
        """Internal method to write data to JSON file"""
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def read_from_file(self) -> Dict[str, Any]:
        """Internal method to read data from JSON file"""
        if not self.filepath.exists():
            self._initialize_file()
        
        with open(self.filepath, 'r') as f:
            return json.load(f)


# Convenience function for quick access
def get_trend_storage(filename: str = "trend_history.json") -> TrendStorage:
    """Get a TrendStorage instance"""
    return TrendStorage(filename)


if __name__ == "__main__":
    # Example usage
    storage = TrendStorage()
    
    # Write sample trend
    sample_trend = {
        'nifty_value': 23456.50,
        'pcr_oi': 1.15,
        'pcr_volume': 1.08,
        'sentiment': 'bullish',
        'iv_rank': 65,
        'call_oi': 234567,
        'put_oi': 245678
    }
    storage.write_trend(sample_trend)
    
    # Read trends
    trends = storage.read_recent_trends(10)
    print(f"\nRecent trends: {trends}")
    
    # Get statistics
    stats = storage.get_trend_statistics()
    print(f"\nTrend statistics: {stats}")
