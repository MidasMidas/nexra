package com.nexra.console.model;

import java.util.ArrayList;
import java.util.List;

public class Skill {
    private String id;
    private String name;
    private String category;
    private String description;
    private double pricePerCall;
    private String status;
    private int successRate;
    private int latencyP95;
    private int costEfficiency;
    private double userRatingAvg;
    private int userRatingCount;
    private int recentCalls;
    private List<String> functions = new ArrayList<>();
    private String invocationMethod;
    private String submittedBy;
    private String approvalStatus;
    private String source;
    private String sourceUrl;
    private String sourceAuthor;
    private String license;
    private String operatingSystem;

    public Skill() {
    }

    public Skill(String id, String name, String category, String description, double pricePerCall, String status,
                 int successRate, int latencyP95, int costEfficiency, double userRatingAvg, int userRatingCount,
                 int recentCalls, List<String> functions, String invocationMethod, String submittedBy,
                 String approvalStatus, String source, String sourceUrl, String sourceAuthor, String license,
                 String operatingSystem) {
        this.id = id;
        this.name = name;
        this.category = category;
        this.description = description;
        this.pricePerCall = pricePerCall;
        this.status = status;
        this.successRate = successRate;
        this.latencyP95 = latencyP95;
        this.costEfficiency = costEfficiency;
        this.userRatingAvg = userRatingAvg;
        this.userRatingCount = userRatingCount;
        this.recentCalls = recentCalls;
        this.functions = new ArrayList<>(functions);
        this.invocationMethod = invocationMethod;
        this.submittedBy = submittedBy;
        this.approvalStatus = approvalStatus;
        this.source = source;
        this.sourceUrl = sourceUrl;
        this.sourceAuthor = sourceAuthor;
        this.license = license;
        this.operatingSystem = operatingSystem;
    }

    public void applyUserRating(int rating) {
        double totalScore = this.userRatingAvg * this.userRatingCount + rating;
        this.userRatingCount += 1;
        this.userRatingAvg = totalScore / this.userRatingCount;
    }

    public void update(String name, String category, String description, double pricePerCall, String status,
                       int successRate, int latencyP95, int costEfficiency, double userRatingAvg,
                       int userRatingCount, int recentCalls, List<String> functions, String invocationMethod,
                       String approvalStatus, String source, String sourceUrl, String sourceAuthor, String license,
                       String operatingSystem) {
        this.name = name;
        this.category = category;
        this.description = description;
        this.pricePerCall = pricePerCall;
        this.status = status;
        this.successRate = successRate;
        this.latencyP95 = latencyP95;
        this.costEfficiency = costEfficiency;
        this.userRatingAvg = userRatingAvg;
        this.userRatingCount = userRatingCount;
        this.recentCalls = recentCalls;
        this.functions = new ArrayList<>(functions);
        this.invocationMethod = invocationMethod;
        this.approvalStatus = approvalStatus;
        this.source = source;
        this.sourceUrl = sourceUrl;
        this.sourceAuthor = sourceAuthor;
        this.license = license;
        this.operatingSystem = operatingSystem;
    }

    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getCategory() {
        return category;
    }

    public String getDescription() {
        return description;
    }

    public double getPricePerCall() {
        return pricePerCall;
    }

    public String getStatus() {
        return status;
    }

    public int getSuccessRate() {
        return successRate;
    }

    public int getLatencyP95() {
        return latencyP95;
    }

    public int getCostEfficiency() {
        return costEfficiency;
    }

    public double getUserRatingAvg() {
        return userRatingAvg;
    }

    public int getUserRatingCount() {
        return userRatingCount;
    }

    public int getRecentCalls() {
        return recentCalls;
    }

    public List<String> getFunctions() {
        return functions;
    }

    public String getInvocationMethod() {
        return invocationMethod;
    }

    public String getSubmittedBy() {
        return submittedBy;
    }

    public String getApprovalStatus() {
        return approvalStatus;
    }

    public void setApprovalStatus(String approvalStatus) {
        this.approvalStatus = approvalStatus;
    }

    public String getSource() {
        return source;
    }

    public String getSourceUrl() {
        return sourceUrl;
    }

    public String getSourceAuthor() {
        return sourceAuthor;
    }

    public String getLicense() {
        return license;
    }

    public String getOperatingSystem() {
        return operatingSystem;
    }
}
