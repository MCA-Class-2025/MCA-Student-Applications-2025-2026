package com.openapi.weather_project.Controller;

import com.openapi.weather_project.Exception.NotFoundException;
import com.openapi.weather_project.Model.GetResponseDTO;
import com.openapi.weather_project.Service.WheatherService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/weather")
@CrossOrigin(origins = "*")
public class WheatherController {

    private final WheatherService serv;

    public WheatherController(WheatherService serv) {
        this.serv = serv;
    }

    // =========================================================
    // API 1 - Current Weather
    // Example:
    // GET http://localhost:8090/weather/Mumbai
    // =========================================================
    @GetMapping("/{name}")
    public GetResponseDTO getWheatherByCity(
            @PathVariable("name") String name) throws NotFoundException {

        return serv.weatherByName(name);
    }


    // =========================================================
    // API 2 - 5 Day Weather Forecast
    // Example:
    // GET http://localhost:8090/weather/forecast/Mumbai
    // =========================================================
    @GetMapping("/forecast/{name}")
    public Object getForecast(
            @PathVariable("name") String name) {

        return serv.getForecast(name);
    }


    // =========================================================
    // API 3 - Air Quality
    // Example:
    // GET http://localhost:8090/weather/air-quality/Mumbai
    // =========================================================
    @GetMapping("/air-quality/{name}")
    public Object getAirQuality(
            @PathVariable("name") String name) {

        return serv.getAirQuality(name);
    }


    // =========================================================
    // API 4 - Geocoding
    // City Name -> Latitude + Longitude
    //
    // Example:
    // GET http://localhost:8090/weather/location/Mumbai
    // =========================================================
    @GetMapping("/location/{name}")
    public Object getLocation(
            @PathVariable("name") String name) throws NotFoundException {

        return serv.getLocation(name);
    }


    // =========================================================
    // API 5 - Reverse Geocoding
    // Latitude + Longitude -> Location
    //
    // Example:
    // GET http://localhost:8090/weather/location/19.0760/72.8777
    // =========================================================
    @GetMapping("/location/{lat}/{lon}")
    public Object getLocationByCoordinates(
            @PathVariable("lat") double lat,
            @PathVariable("lon") double lon) throws NotFoundException {

        return serv.getLocationByCoordinates(lat, lon);
    }
}