package com.openapi.weather_project.Service;

import com.openapi.weather_project.Exception.NotFoundException;
import com.openapi.weather_project.Model.GetResponseDTO;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Service
public class WheatherService {

    // =========================================================
    // API URLs
    // =========================================================

    private final String baseUrl;
    private final String forecastUrl;
    private final String airPollutionUrl;
    private final String geocodingUrl;
    private final String reverseGeocodingUrl;

    // OpenWeather API Key
    private final String token;

    // RestTemplate
    private final RestTemplate rest = new RestTemplate();


    // =========================================================
    // Constructor
    // =========================================================

    public WheatherService(

            @Value("${openWheatherApplication}")
            String baseUrl,

            @Value("${forecastUrl}")
            String forecastUrl,

            @Value("${airPollutionUrl}")
            String airPollutionUrl,

            @Value("${geocodingUrl}")
            String geocodingUrl,

            @Value("${reverseGeocodingUrl}")
            String reverseGeocodingUrl,

            @Value("${app_id}")
            String token) {

        this.baseUrl = baseUrl;
        this.forecastUrl = forecastUrl;
        this.airPollutionUrl = airPollutionUrl;
        this.geocodingUrl = geocodingUrl;
        this.reverseGeocodingUrl = reverseGeocodingUrl;
        this.token = token;
    }


    // =========================================================
    // API 1
    // CURRENT WEATHER
    //
    // Example:
    // /weather/Mumbai
    // =========================================================

    public GetResponseDTO weatherByName(String name) throws NotFoundException {

        String url =
                baseUrl
                        + "?q=" + name
                        + "&appid=" + token
                        + "&units=metric";

        try {

            GetResponseDTO response =
                    rest.getForObject(
                            url,
                            GetResponseDTO.class
                    );

            if (response == null) {

                throw new NotFoundException();
            }

            return response;

        } catch (HttpClientErrorException.NotFound e) {

            throw new NotFoundException();
        } catch (NotFoundException e) {
            throw new RuntimeException(e);
        }
    }


    // =========================================================
    // API 2
    // 5 DAY WEATHER FORECAST
    //
    // Example:
    // /weather/forecast/Mumbai
    // =========================================================

    public Object getForecast(String name) {

        String url =
                forecastUrl
                        + "?q=" + name
                        + "&appid=" + token
                        + "&units=metric";

        try {

            Object response =
                    rest.getForObject(
                            url,
                            Object.class
                    );

            if (response == null) {

                throw new NotFoundException();
            }

            return response;


        } catch (NotFoundException e) {
            throw new RuntimeException(e);
        }
    }


    // =========================================================
    // API 3
    // AIR QUALITY
    //
    // Example:
    // /weather/air-quality/Mumbai
    //
    // First:
    // Mumbai -> latitude + longitude
    //
    // Then:
    // latitude + longitude -> Air Quality
    // =========================================================

    public Object getAirQuality(String name) {

        // -----------------------------------------
        // Step 1: Get latitude and longitude
        // -----------------------------------------

        String geoUrl =
                geocodingUrl
                        + "?q=" + name
                        + "&limit=1"
                        + "&appid=" + token;

        try {

            List<Map<String, Object>> locations =
                    rest.getForObject(
                            geoUrl,
                            List.class
                    );

            if (locations == null || locations.isEmpty()) {

                throw new NotFoundException();
            }


            // -----------------------------------------
            // Step 2: Get first location
            // -----------------------------------------

            Map<String, Object> location =
                    locations.get(0);


            // -----------------------------------------
            // Step 3: Extract latitude
            // -----------------------------------------

            double lat =
                    ((Number) location.get("lat"))
                            .doubleValue();


            // -----------------------------------------
            // Step 4: Extract longitude
            // -----------------------------------------

            double lon =
                    ((Number) location.get("lon"))
                            .doubleValue();


            // -----------------------------------------
            // Step 5: Call Air Pollution API
            // -----------------------------------------

            String url =
                    airPollutionUrl
                            + "?lat=" + lat
                            + "&lon=" + lon
                            + "&appid=" + token;


            Object response =
                    rest.getForObject(
                            url,
                            Object.class
                    );


            if (response == null) {

                throw new NotFoundException();
            }


            return response;

        } catch (NotFoundException e) {
            throw new RuntimeException(e);
        }
    }


    // =========================================================
    // API 4
    // GEOCODING
    //
    // City -> Latitude + Longitude
    //
    // Example:
    // /weather/location/Mumbai
    // =========================================================

    public Object getLocation(String name) throws NotFoundException {

        String url =
                geocodingUrl
                        + "?q=" + name
                        + "&limit=1"
                        + "&appid=" + token;

        try {

            Object response =
                    rest.getForObject(
                            url,
                            Object.class
                    );

            if (response == null) {

                throw new NotFoundException();
            }

            return response;

        } catch (HttpClientErrorException.NotFound | NotFoundException e) {

            throw new NotFoundException();
        }
    }


    // =========================================================
    // API 5
    // REVERSE GEOCODING
    //
    // Latitude + Longitude -> Location
    //
    // Example:
    // /weather/location/19.0760/72.8777
    // =========================================================

    public Object getLocationByCoordinates(
            double lat,
            double lon) throws NotFoundException {

        String url =
                reverseGeocodingUrl
                        + "?lat=" + lat
                        + "&lon=" + lon
                        + "&limit=1"
                        + "&appid=" + token;

        try {

            Object response =
                    rest.getForObject(
                            url,
                            Object.class
                    );

            if (response == null) {

                throw new NotFoundException();
            }

            return response;

        } catch (HttpClientErrorException.NotFound | NotFoundException e) {

            throw new NotFoundException();
        }
    }
}