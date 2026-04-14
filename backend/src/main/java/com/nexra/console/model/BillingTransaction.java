package com.nexra.console.model;

public class BillingTransaction {
    private String id;
    private String type;
    private double amount;
    private String timestamp;

    public BillingTransaction() {
    }

    public BillingTransaction(String id, String type, double amount, String timestamp) {
        this.id = id;
        this.type = type;
        this.amount = amount;
        this.timestamp = timestamp;
    }

    public String getId() {
        return id;
    }

    public String getType() {
        return type;
    }

    public double getAmount() {
        return amount;
    }

    public String getTimestamp() {
        return timestamp;
    }
}
