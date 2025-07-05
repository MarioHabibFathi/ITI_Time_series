from prometheus_client import Histogram, Counter, Gauge, Summary
import psutil
import time
import threading

INFERENCE_TIME_HISTOGRAM = Histogram(
    "inference_latency_seconds",
    "Time spent processing prediction requests"
)
MODEL_PREDICTION_TYPES = Counter(
    "model_prediction_counts", 
    "Count of predictions by gesture type", 
    ["gesture"]
)   



INVALID_LANDMARK_ERRORS = Counter(
    "invalid_landmark_errors",                               
    "Count of invalid landmark submissions", 
    ["error_type"]
)




REQUEST_COUNT = Counter("api_request_count", "Total number of API requests")
REQUEST_ERRORS = Counter("api_request_errors", "Number of failed API predictions")
REQUEST_LATENCY = Summary(
    "api_request_latency_seconds",
    "End-to-end API request processing time"
)

CPU_USAGE = Gauge("cpu_usage_percent", "CPU usage percentage")
RAM_USAGE = Gauge("ram_usage_percent", "RAM usage percentage")

UPTIME = Gauge("total_app_uptime_seconds", "App uptime in seconds")
APP_UPTIME = Gauge("app_uptime_seconds", "Application uptime in seconds", ["status"])

START_TIME = time.time()
LAST_ACTIVE_TIME = time.time()

def update_system_metrics():
    while True:
        try:
            CPU_USAGE.set(psutil.cpu_percent(interval=1))
            RAM_USAGE.set(psutil.virtual_memory().percent)
            
            
            total_uptime = time.time() - START_TIME
            active_uptime = time.time() - LAST_ACTIVE_TIME

            UPTIME.set(total_uptime)
            APP_UPTIME.labels("total").set(total_uptime)
            APP_UPTIME.labels("active").set(active_uptime)
       
            time.sleep(5)
        except Exception:
            continue

def start_metrics_collection():
    thread = threading.Thread(target=update_system_metrics, daemon=True)
    thread.start()
