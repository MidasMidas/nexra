package com.nexra.console.dto;

import jakarta.validation.constraints.NotBlank;

public class ApiKeyCreateRequest {
    @NotBlank
    private String name;

    private String scope;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getScope() {
        return scope;
    }

    public void setScope(String scope) {
        this.scope = scope;
    }
}
