package com.openapi.weather_project.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class getWind {
    private double speed;
    private int deg;
    private double gust;
}
