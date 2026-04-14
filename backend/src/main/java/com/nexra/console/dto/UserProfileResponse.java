package com.nexra.console.dto;

import java.util.List;

public record UserProfileResponse(
        UserResponse user,
        List<SkillResponse> submittedSkills,
        List<UserReviewResponse> submittedReviews
) {
}
