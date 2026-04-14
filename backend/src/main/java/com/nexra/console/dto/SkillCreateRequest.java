package com.nexra.console.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

public class SkillCreateRequest {
    @NotBlank
    private String name;
    @NotBlank
    private String category;
    @NotBlank
    private String description;
    @DecimalMin("0.0")
    private double pricePerCall;
    @NotEmpty
    private List<String> functions;
    @NotBlank
    private String invocationMethod;
    private String source;
    private String sourceUrl;
    private String sourceAuthor;
    private String license;
    private String operatingSystem;
    @Min(0)
    private int successRate;
    @Min(0)
    private int latencyP95;
    @Min(0)
    private int costEfficiency;
    @Min(0)
    private int recentCalls;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public double getPricePerCall() { return pricePerCall; }
    public void setPricePerCall(double pricePerCall) { this.pricePerCall = pricePerCall; }
    public List<String> getFunctions() { return functions; }
    public void setFunctions(List<String> functions) { this.functions = functions; }
    public String getInvocationMethod() { return invocationMethod; }
    public void setInvocationMethod(String invocationMethod) { this.invocationMethod = invocationMethod; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public String getSourceUrl() { return sourceUrl; }
    public void setSourceUrl(String sourceUrl) { this.sourceUrl = sourceUrl; }
    public String getSourceAuthor() { return sourceAuthor; }
    public void setSourceAuthor(String sourceAuthor) { this.sourceAuthor = sourceAuthor; }
    public String getLicense() { return license; }
    public void setLicense(String license) { this.license = license; }
    public String getOperatingSystem() { return operatingSystem; }
    public void setOperatingSystem(String operatingSystem) { this.operatingSystem = operatingSystem; }
    public int getSuccessRate() { return successRate; }
    public void setSuccessRate(int successRate) { this.successRate = successRate; }
    public int getLatencyP95() { return latencyP95; }
    public void setLatencyP95(int latencyP95) { this.latencyP95 = latencyP95; }
    public int getCostEfficiency() { return costEfficiency; }
    public void setCostEfficiency(int costEfficiency) { this.costEfficiency = costEfficiency; }
    public int getRecentCalls() { return recentCalls; }
    public void setRecentCalls(int recentCalls) { this.recentCalls = recentCalls; }
}
