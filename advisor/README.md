# OntoHarness Spring AI advisor

Post-call `OntologyValidationAdvisor` for Spring AI `ChatClient`. Validates ` ```turtle ` fences in model output via the OntoHarness Python sidecar (`POST /api/v1/validate`).

## Build

```bash
cd advisor
mvn test
mvn install   # required before running the Spring Boot demo
```

## Runnable demo

See [examples/spring-boot-demo/README.md](examples/spring-boot-demo/README.md) — stub ChatModel, no API key, port **8088**.

## Wire into your app

```java
var client = new OntoHarnessClient("http://localhost:8010");
var policy = OntologyValidationAdvisor.builder(client)
    .domain("biomedical")
    .failClosed(true)
    .validateOutput(true)
    .build();
var advisor = OntologyValidationAdvisor.advisor(policy).build();

var chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(advisor)
    .build();
```

On failure the advisor sets `ontoharness.conforms=false` and `ontoharness.repairHints` on the `ChatClientResponse` context.

## Tests

| Test | Sidecar required |
|------|------------------|
| `TurtleBlockExtractorTest`, `OntologyValidationAdvisorTest` | No |
| `BasicUsageExampleTest` | Yes (`:8010`) — skipped when sidecar is down |
