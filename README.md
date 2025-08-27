# Red-on-Logs

**PoC dimostrativo** - Pipeline di logging distribuita basata su Redpanda, Elasticsearch e Logstash.

> ⚠️ **Proof of Concept**: Questo progetto è pensato esclusivamente per dimostrare l'integrazione di questi componenti in un ambiente di sviluppo. Non è uno strumento production-ready.

## Architettura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Log Producer   │───▶│    Redpanda     │───▶│    Logstash     │───▶│  Elasticsearch  │
│   (Python)     │    │   (Kafka API)   │    │   (Processing)  │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                                              │
                                                                              ▼
                                                                    ┌─────────────────┐
                                                                    │     Kibana      │
                                                                    │ (Visualization) │
                                                                    └─────────────────┘
```

## Il problema

Gestire log da più servizi. Serve una soluzione che:
- Raccolga tutto in un posto
- Processi i dati in tempo reale
- Permetta ricerche veloci
- Sia semplice da deployare

## La soluzione

**Redpanda** invece di Kafka perché è più leggero e veloce in container.
**Logstash** per trasformare log grezzi in dati strutturati.
**Elasticsearch** per indicizzazione e ricerca full-text.
**Kibana** per dashboard e analisi visiva.

## Setup rapido

```bash
# Clone
git clone https://github.com/loadkeysit/Red-on-Logs
cd Red-on-Logs

# Start tutto
docker-compose up --build

# Check status
docker-compose ps
```

## Endpoints

- **Redpanda Console**: http://localhost:8080
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

## Configurazione

### Producer
Il producer Python genera log simulati con diversi livelli di severità:
- INFO, WARN, ERROR, DEBUG
- Metadata automatici (timestamp, service_name, etc.)

### Logstash Pipeline
```ruby
input {
          kafka {
            bootstrap_servers => \"redpanda:9092\"
            topics_pattern => \"logs\\..*\"
            codec => json
            consumer_threads => 1
          }
        }
        
        filter {
          if [level] == \"ERROR\" or [level] == \"FATAL\" {
            mutate {
              add_tag => [\"error\"]
            }
          }
          
          if [timestamp] {
            date {
              match => [ \"timestamp\", \"ISO8601\" ]
              target => \"@timestamp\"
            }
          }
        }
        
        output {
          elasticsearch {
            hosts => [\"elasticsearch:9200\"]
            index => \"logs-%{[application][name]}-%{+YYYY.MM.dd}\"
            ilm_enabled => false
            action => "create"  
          }
          
          stdout {
            codec => rubydebug
          }
        }' 
```

## Monitoring

Il sistema genera automaticamente metriche su:
- Throughput messaggi/secondo
- Latenza end-to-end
- Storage utilizzato
- Errori di processing


---

**Scopo**: PoC per testare rapidamente l'integrazione Redpanda + ELK stack. Non sostituisce soluzioni enterprise.
