package com.nexra.console.dto;

import java.util.List;

public record DashboardResponse(
        int totalIndexedSkills,
        int approvedSkills,
        int pendingSkills,
        int averageTrust,
        int averageRecommendation,
        int searchableFunctions,
        int popularSkills,
        int averageSuccessRate,
        int averageLatencyP95,
        int averageCostEfficiency,
        List<SkillResponse> topSkills
) {
}
