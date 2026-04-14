package com.nexra.console.model;

public class ApiKeyRecord {
    private String id;
    private String name;
    private String scope;
    private String lastUsed;
    private String status;

    public ApiKeyRecord() {
    }

    public ApiKeyRecord(String id, String name, String scope, String lastUsed, String status) {
        this.id = id;
        this.name = name;
        this.scope = scope;
        this.lastUsed = lastUsed;
        this.status = status;
    }

    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getScope() {
        return scope;
    }

    public String getLastUsed() {
        return lastUsed;
    }

    public String getStatus() {
        return status;
    }
}
