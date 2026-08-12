# OntoHarness Spring Boot demo

Runnable Spring AI app that wires `OntologyValidationAdvisor` into a `ChatClient` with a **stub ChatModel** (no OpenAI key required).

## Prerequisites

- Java 17+
- Maven 3.9+
- OntoHarness sidecar on `:8010`

```bash
# Terminal 1 — from ontoharness repo root
py -3 -m uvicorn api.app.main:app --port 8010
```

## Run

```bash
# Install the advisor library into the local Maven repo
cd advisor
mvn -q install

# Start the demo (port 8088)
cd examples/spring-boot-demo
mvn -q spring-boot:run
```

## Try it

```bash
# Valid Turtle — passes vocab + SHACL + competency questions
curl -s -X POST http://localhost:8088/chat \
  -H "Content-Type: application/json" \
  -d "{\"scenario\":\"valid\"}" | jq

# Fabricated predicate — blocked by OntoHarness vocab gate
curl -s -X POST http://localhost:8088/chat \
  -H "Content-Type: application/json" \
  -d "{\"scenario\":\"fabricated\"}" | jq
```

Expected blocked response includes `"conforms": false` and `repair_hints` from the sidecar.

## Library-only walkthrough

Without Spring Boot, run the advisor integration example (sidecar required):

```bash
cd advisor
mvn -q -Dtest=BasicUsageExampleTest test
```

Unit tests (no sidecar):

```bash
cd advisor
mvn -q test
```
