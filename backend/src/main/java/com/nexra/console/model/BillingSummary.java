package com.nexra.console.model;

public record BillingSummary(double currentBalance, double spend30d, double avgCallPrice) {
}
