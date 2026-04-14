package com.nexra.console.dto;

public record ReviewResponse(
        String id,
        String skillId,
        String author,
        int rating,
        String comment,
        String timestamp
) {
}
