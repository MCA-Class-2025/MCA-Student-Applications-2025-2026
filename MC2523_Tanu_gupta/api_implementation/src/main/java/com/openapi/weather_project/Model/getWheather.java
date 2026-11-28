package com.openapi.weather_project.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class getWheather {
    private int id;
    private String main;
    private String description;
    private String icon;
}
