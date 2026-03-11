import serial
import serial.tools.list_ports
import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WaterQualityBridge:
    def __init__(self, port: str = "COM11", baudrate: int = 115200, api_url: str = "http://localhost:8000/api/ingest"):
        self.port = port
        self.baudrate = baudrate
        self.api_url = api_url
        self.device_id = "unit_001"
        self.serial_conn: Optional[serial.Serial] = None
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def connect_serial(self) -> bool:
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                write_timeout=1
            )
            logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect_serial(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Serial connection closed")
    
    def parse_sensor_line(self, line: str) -> Optional[Dict[str, float]]:
        line = line.strip()
        
        try:
            if line.startswith("TEMP:"):
                return {"temperature": float(line.split(":")[1].strip())}
            
            elif line.startswith("EC:"):
                return {"ec": float(line.split(":")[1].strip())}
            
            elif line.startswith("PH:"):
                return {"ph": float(line.split(":")[1].strip())}
        
        except (ValueError, IndexError):
            return None
        
        return None
    
    def calculate_enriched_data(self, temperature: float, ec: float, ph: float) -> Dict[str, Any]:
        tds = ec * 500
        
        temp_score = max(0, 100 - abs(temperature - 25) * 2)
        ec_score = max(0, 100 - ec * 20)
        ph_score = max(0, 100 - abs(ph - 7) * 15)
        
        wqi = round((temp_score + ec_score + ph_score) / 3, 2)
        
        if ec < 0.7:
            irrigation_index = "Excellent"
        elif ec <= 3.0:
            irrigation_index = "Moderate"
        else:
            irrigation_index = "Unsuitable"
        
        return {
            "tds": tds,
            "wqi": wqi,
            "irrigation_index": irrigation_index
        }
    
    def send_to_cloud(self, payload: Dict[str, Any]) -> bool:
        try:
            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent data to cloud: {payload['timestamp']}")
                return True
            else:
                logger.error(f"Failed to send data. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending data to cloud: {e}")
            return False
    
    def log_failed_upload(self, payload: Dict[str, Any], error: str):
        failed_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "error": error
        }
        
        try:
            with open("failed_uploads.log", "a") as f:
                f.write(json.dumps(failed_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to failed uploads log: {e}")
    
    def process_serial_data(self):
        if not self.connect_serial():
            logger.error("Cannot start processing - serial connection failed")
            return
        
        logger.info("Starting serial data processing...")
        
        current_reading = {}
        final_detected = False
        
        try:
            while True:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    
                    if line == "FINAL":
                        final_detected = True
                        current_reading = {}
                        continue
                    
                    sensor_data = self.parse_sensor_line(line)
                    if sensor_data:
                        current_reading.update(sensor_data)
                    
                    if (
                        final_detected and
                        "temperature" in current_reading and
                        "ec" in current_reading and
                        "ph" in current_reading
                    ):
                        logger.info(
                            f"Processing final reading: "
                            f"TEMP={current_reading['temperature']}, "
                            f"EC={current_reading['ec']}, "
                            f"PH={current_reading['ph']}"
                        )
                        
                        enriched_data = self.calculate_enriched_data(
                            current_reading["temperature"],
                            current_reading["ec"],
                            current_reading["ph"]
                        )
                        
                        payload = {
                            "device_id": self.device_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "temperature": current_reading["temperature"],
                            "ec": current_reading["ec"],
                            "ph": current_reading["ph"],
                            **enriched_data
                        }
                        
                        success = self.send_to_cloud(payload)
                        if not success:
                            self.log_failed_upload(payload, "Cloud upload failed")
                        
                        current_reading = {}
                        final_detected = False
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            logger.info("Stopping serial bridge...")
        except Exception as e:
            logger.error(f"Error in serial processing: {e}")
        finally:
            self.disconnect_serial()
    
    def test_connection(self) -> bool:
        if not self.connect_serial():
            return False
        
        try:
            if '/api/ingest' in self.api_url:
                health_url = self.api_url.replace('/api/ingest', '/health')
            else:
                health_url = self.api_url.replace('/ingest', '/health')

            response = self.session.get(health_url, timeout=5)
            if response.status_code == 200:
                logger.info("API connection test successful")
                return True
            else:
                logger.error(f"API connection test failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"API connection test error: {e}")
            return False
        finally:
            self.disconnect_serial()

def main():
    import os
    
    API_URL = os.getenv("API_URL", "http://localhost:8080/api/ingest")
    SERIAL_PORT = os.getenv("SERIAL_PORT", "COM11")
    
    logger.info("Starting Water Quality Bridge")
    logger.info(f"Serial Port: {SERIAL_PORT}")
    logger.info(f"API URL: {API_URL}")
    
    bridge = WaterQualityBridge(port=SERIAL_PORT, api_url=API_URL)
    
    if bridge.test_connection():
        logger.info("All connections successful. Starting data processing...")
        bridge.process_serial_data()
    else:
        logger.error("Connection tests failed. Exiting.")

if __name__ == "__main__":
    main()
