package com.nexra.console.dto;

import java.util.List;

public record SkillDetailResponse(
        SkillResponse skill,
        List<ReviewResponse> reviews
) {
}
