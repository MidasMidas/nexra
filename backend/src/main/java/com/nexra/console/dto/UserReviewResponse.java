package com.nexra.console.dto;

public record UserReviewResponse(
        String id,
        String skillId,
        String skillName,
        int rating,
        String comment,
        String timestamp
) {
}
