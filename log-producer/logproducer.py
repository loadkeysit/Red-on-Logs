import json
import time
import random
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import socket

def wait_kafka(host='redpanda', port=9092, timeout=60):
    print(f"⏳ Attendo che Kafka sia disponibile su {host}:{port} (timeout {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("✅ Kafka disponibile.")
                return
        except OSError:
            print(".", end="", flush=True)
            time.sleep(2)
    raise RuntimeError(f"❌ Timeout: Kafka non disponibile su {host}:{port} dopo {timeout}s.")


class AppLogProducer:
    def __init__(self, max_retries=10, retry_delay=5):
        self.apps = [
            {'name': 'web-frontend', 'env': 'prod'},
            {'name': 'api-gateway', 'env': 'prod'},
            {'name': 'user-service', 'env': 'prod'},
            {'name': 'order-service', 'env': 'staging'},
            {'name': 'payment-service', 'env': 'prod'}
        ]
        self.levels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']

        self.producer = self._connect_kafka_with_retry(max_retries, retry_delay)

    def _connect_kafka_with_retry(self, max_retries, retry_delay):
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔌 Tentativo {attempt} di connessione a Kafka...")
                producer = KafkaProducer(
                    bootstrap_servers=['redpanda:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8'),
                    acks='all',
                    compression_type='gzip'
                )
                print("✅ Connessione a Kafka riuscita.")
                return producer
            except NoBrokersAvailable:
                print(f"⚠️  Nessun broker disponibile. Riprovo tra {retry_delay} secondi...")
                time.sleep(retry_delay)
        print("❌ Impossibile connettersi a Kafka dopo vari tentativi. Esco.")
        exit(1)

    def generate_log(self):
        app = random.choice(self.apps)
        level = random.choices(self.levels, weights=[5, 60, 25, 8, 2])[0]

        messages = {
            'DEBUG': ['Debugging connection', 'Cache hit for key', 'Entered function X'],
            'INFO': ['User login successful', 'Processed request', 'Service started'],
            'WARN': ['High memory usage detected', 'Slow response', 'Rate limit near'],
            'ERROR': ['DB connection failed', 'Authentication failed', 'Timeout error'],
            'FATAL': ['Out of memory', 'System crash', 'Service shutdown unexpectedly']
        }

        message = random.choice(messages[level])

        log = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'application': {
                'name': app['name'],
                'environment': app['env'],
                'version': f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
                'instance_id': f"instance-{random.randint(1,5):02d}"
            },
            'message': message,
            'trace_id': uuid.uuid4().hex,
            'user_id': random.randint(1000, 9999) if random.random() > 0.3 else None,
            'response_time_ms': random.randint(10, 2000),
            'memory_usage_mb': random.randint(50, 500),
            'cpu_percent': round(random.uniform(5, 85), 2)
        }
        return log

    def send_log(self, log):
        level = log['level']
        app_name = log['application']['name']

        topic_map = {
            'DEBUG': f'logs.debug.{app_name}',
            'INFO': f'logs.info.{app_name}',
            'WARN': f'logs.warn.{app_name}',
            'ERROR': f'logs.error.{app_name}',
            'FATAL': 'logs.fatal'
        }
        topic = topic_map.get(level, 'logs.unknown')
        key = f"{app_name}:{log['trace_id'][:8]}"

        try:
            self.producer.send(topic, key=key, value=log)
            print(f"📤 [{level}] {app_name:15} -> {topic:25} | {log['message']}")
            self.producer.flush()
        except Exception as e:
            print(f"❌ Errore invio: {e}")

    def run(self, interval=1.0):
        print(f"🚀 Avvio produzione log su Kafka (Redpanda) - intervallo {interval}s")
        try:
            while True:
                logs_to_send = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
                for _ in range(logs_to_send):
                    log = self.generate_log()
                    self.send_log(log)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Interrotto dall'utente")
        finally:
            self.producer.close()
            print("✅ Producer chiuso")


if __name__ == "__main__":
    producer = AppLogProducer()
    producer.run(interval=2)
