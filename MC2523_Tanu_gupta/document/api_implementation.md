# Spring Boot API Implementation

The Spring Boot application provides current weather, forecast, air-quality,
and geocoding endpoints, along with its browser UI and static assets. All of
its source and Maven configuration are grouped in
[`api_implementation/`](../api_implementation/).

## Project layout

- `api_implementation/src/main/java/`: controllers, service, response models,
  and application entry point.
- `api_implementation/src/main/resources/static/`: browser UI, styles, and
  weather icons.
- `api_implementation/src/main/resources/application.properties`: Spring
  configuration.
- `api_implementation/.mvn/`, `mvnw`, `mvnw.cmd`, and `pom.xml`: Maven wrapper
  and build configuration.
- `llm_implementation/`: separate Python weather assistant and RAG service.

## Requirements

- Java 17 and the included Maven wrapper.
- An OpenWeather API key for live weather requests.
- Do not commit credentials; configure the key using local, secret-safe
  properties before sharing or deployment.

## Run the Spring Boot application

From the repository folder in PowerShell:

```powershell
cd api_implementation
.\mvnw.cmd spring-boot:run
```

The server uses port `8090`. Example endpoints include:

- `GET /weather/{city}`
- `GET /weather/forecast/{city}`
- `GET /weather/air-quality/{city}`
- `GET /weather/location/{city}`
- `GET /weather/location/{latitude}/{longitude}`

Run the tests from `api_implementation/`:

```powershell
.\mvnw.cmd test
```

For the Python assistant and dashboard, follow the
[LLM implementation guide](./llm_implementation.md) and
[dashboard guide](./dashboard.md).
