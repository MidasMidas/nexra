const isLocalFrontend =
  typeof window !== "undefined" &&
  (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") &&
  window.location.port === "4173";
const API_BASE =
  (typeof window !== "undefined" && window.__NEXRA_API_BASE__) ||
  (isLocalFrontend ? "http://localhost:8080/api" : `${window.location.origin}/api`);
const API_ORIGIN_DISPLAY = API_BASE.replace(/\/api$/, "");
const copy = {
  en: {
    nav: { welcome: "Welcome", tutorial: "Tutorial", dashboard: "Dashboard", marketplace: "Marketplace", skill: "Skill Detail", profile: "Profile", admin: "Admin" },
    hero: { welcome: "Help your agent find the right external skill", tutorial: "Step-by-step guide for skill discovery and external calling", dashboard: "Recommendation signals for external skills", marketplace: "Search and compare external skills by fit, trust, and cost", skill: "Inspect recommendation signals and calling guidance", profile: "Your skills, ratings, and account details", admin: "Review, approve, and maintain submitted skills" },
    language: "Language",
    role: "Role",
    adminOnly: "Admin only",
    loginTitle: "Sign in to Nexra",
    loginCopy: "Sign in with your Nexra account to continue.",
    loginAction: "Sign in",
    registerAction: "Create account",
    authLoginTab: "Sign in",
    authRegisterTab: "Register",
    authLoginPill: "Login",
    authRegisterPill: "Register",
    loginName: "Full name",
    loginRegisterCopy: "Create your Nexra account with email and a password of at least 6 characters.",
    loginUsername: "Email",
    loginPassword: "Password (min 6 characters)",
    loginFailed: "Sign-in failed: {error}",
    loginSuccess: "Signed in successfully.",
    registerFailed: "Registration failed: {error}",
    registerSuccess: "Account created and signed in.",
    loginRequired: "Please sign in first.",
    logoutSuccess: "Signed out.",
    logoutAction: "Log out",
    profileAction: "Profile",
    profileTitle: "Personal profile",
    profileSubmittedSkills: "Submitted skills",
    profileSubmittedReviews: "Submitted reviews",
    profileNoSkills: "You have not submitted any skills yet.",
    profileNoReviews: "You have not submitted any ratings yet.",
    profileMemberSince: "Signed in as",
    profileEmail: "Email",
    profileSkillStatus: "Status",
    profileReviewFor: "For skill",
    profileReviewCount: "Total ratings",
    welcomeTitle: "How your agent should use Nexra",
    welcomeSteps: "Key steps",
    welcomeCapabilities: "What Nexra gives you",
    agentGuide: "Agent instruction endpoint",
    frontendConsole: "Frontend console",
    tutorialTitle: "How your agent should search and choose skills",
    tutorialStepsTitle: "Integration steps",
    tutorialChecklistTitle: "Before you go live",
    tutorialStep1: "Call GET /api/skills with keywords or capability filters to search the marketplace.",
    tutorialStep2: "Compare recommendationScore, overallTrust, userRatingAvg, systemScore, and pricePerCall.",
    tutorialStep3: "Open GET /api/skills/{id} to inspect calling notes, provider details, and documentation links.",
    tutorialStep4: "Let your own agent call the selected skill provider directly outside Nexra.",
    tutorialStep5: "After a human reviews the result, send feedback to POST /api/skills/{id}/reviews to improve trust data.",
    tutorialCheck1: "Prefer higher recommendationScore when multiple skills can solve the same task.",
    tutorialCheck2: "Treat systemScore as operational quality and userRatingAvg as human satisfaction.",
    tutorialCheck3: "Record which skill your agent selected so you can audit quality later.",
    tutorialCheck4: "Keep a human-in-the-loop for final review when your workflow is sensitive.",
    requestHeadersTitle: "Request headers",
    curlTitle: "curl example",
    pythonTitle: "Python example",
    jsTitle: "JavaScript example",
    dashboardCurrentBalance: "Indexed skills",
    dashboardCurrentBalanceMeta: "Current searchable marketplace inventory",
    dashboardActiveSkills: "Approved skills",
    dashboardActiveSkillsMeta: "Approved and visible to agents",
    dashboardAverageTrust: "Average trust",
    dashboardAverageTrustMeta: "Blended user and system score",
    dashboardInvocations: "Average recommendation",
    dashboardInvocationsMeta: "Search ranking signal across the marketplace",
    dashboardTopTrustedSkills: "Top recommended skills",
    dashboardRanking: "Ranking",
    dashboardTrustSplit: "Recommendation split",
    dashboardDualScoring: "Ranking inputs",
    dashboardUserRatingInfluence: "User rating influence",
    dashboardAgentRatingInfluence: "System rating influence",
    dashboardTopSkill: "Top recommendation",
    dashboardAgentRatingHealth: "Marketplace health",
    dashboardAutoEvaluated: "Auto-evaluated",
    dashboardAvgSuccessRate: "Avg success rate",
    dashboardAvgLatencyP95: "Avg latency p95",
    dashboardAvgCostEfficiency: "Avg cost efficiency",
    marketplaceSearchPlaceholder: "Search skills, categories, or outcomes",
    marketplaceSortTrust: "Sort by overall trust",
    marketplaceSortUser: "Sort by user rating",
    marketplaceSortAgent: "Sort by agent rating",
    marketplaceSortPrice: "Sort by lowest price",
    marketplaceOverallTrust: "Overall trust",
    marketplaceRecommendation: "Recommendation",
    marketplaceDocs: "Docs",
    marketplaceProvider: "Provider",
    marketplaceReadiness: "Readiness",
    marketplaceAllReadiness: "All readiness",
    marketplaceHideTemplates: "Hide templates",
    marketplaceUser: "User",
    marketplaceAgent: "Agent",
    marketplaceOpenDetail: "Open detail",
    marketplaceFunction: "Function",
    marketplaceInvocation: "Invocation",
    marketplaceSearchButton: "Search",
    marketplacePageSize: "Page size",
    marketplacePrev: "Previous",
    marketplaceNext: "Next",
    marketplacePage: "Page",
    marketplaceTotal: "Total",
    skillOverallTrust: "Overall trust",
    skillRecommendation: "Recommendation",
    skillCapabilityMatch: "Capability match",
    skillRecommendationWhy: "Why Nexra recommends it",
    skillReadiness: "Readiness",
    skillUserRating: "User rating",
    skillAgentRating: "Agent rating",
    skillPricePerCall: "Price per call",
    skillProvider: "Provider",
    skillDocumentation: "Documentation",
    skillAuthRequirement: "Auth requirement",
    skillOperatingSystem: "Runtime",
    skillSource: "Source",
    skillCallExample: "Call example",
    skillCallThisDirectly: "Your agent calls this provider directly",
    readinessReady: "Ready to use",
    readinessCreds: "Requires external credentials",
    readinessLocal: "Requires local runtime",
    readinessTemplate: "Template / starter",
    skillReviews: "reviews",
    skillAverageScore: "Average score",
    skillNormalizedScore: "Normalized score",
    skillIntent: "Intent",
    skillHumanUsefulness: "Human usefulness",
    skillSuccessRate: "Success rate",
    skillLatencyP95: "Latency p95",
    skillCostEfficiency: "Cost efficiency",
    skillSubmitFeedback: "Submit user feedback",
    skillManualReview: "Manual review",
    skillYourName: "Your name",
    skillStarRating: "Star rating",
    skillShortReview: "Short review",
    skillReviewPlaceholder: "What did this skill do well, and what should improve?",
    skillSaveRating: "Save rating",
    skillRecentReviews: "Recent reviews",
    skillHumanVoice: "Human voice",
    skillChooseStar: "Choose a star rating first.",
    skillSaved: "User rating saved. Trust score updated.",
    adminPendingTitle: "Pending skill review",
    adminSelectedTitle: "Skill moderation",
    adminEmpty: "No pending skills right now.",
    adminPick: "Select a pending skill to review and edit.",
    adminApprove: "Approve skill",
    adminDelete: "Delete skill",
    adminSave: "Save changes",
    adminFunctions: "Functions",
    adminInvocationMethod: "Invocation method",
    adminApprovalStatus: "Approval status",
    adminSubmittedBy: "Submitted by",
    adminStatus: "Status",
    adminName: "Name",
    adminCategory: "Category",
    adminDescription: "Description",
    adminPrice: "Price per call",
    adminSuccessRate: "Success rate",
    adminLatencyP95: "Latency p95",
    adminCostEfficiency: "Cost efficiency",
    adminRecentCalls: "Recent calls",
    adminUserRatingAvg: "User rating avg",
    adminUserRatingCount: "User rating count",
    adminApproved: "Skill approved.",
    adminSaved: "Skill changes saved.",
    adminDeleted: "Skill deleted.",
    adminNeedRole: "Switch to an admin user to manage reviews.",
    errorsTitle: "Common errors",
    error1: "Backend not running: start Nexra and confirm {apiBase}/api/dashboard returns data.",
    error2: "Skill not found: your agent requested an invalid skill id.",
    error3: "Validation error: review payload must include author and a rating from 1 to 5.",
    error4: "Connection refused: your agent cannot reach the local Nexra API endpoint.",
    connected: "Frontend connected to Spring Boot API at {apiBase}/api.",
    failed: "Unable to reach backend: {error}. Start the Spring Boot app first."
  },
  zh: {
    nav: { welcome: "\u6b22\u8fce", tutorial: "\u6559\u7a0b", dashboard: "\u603b\u89c8", marketplace: "\u6280\u80fd\u5e02\u573a", skill: "\u6280\u80fd\u8be6\u60c5", profile: "\u4e2a\u4eba\u4fe1\u606f", admin: "\u7ba1\u7406\u5458\u540e\u53f0" },
    hero: { welcome: "\u5e2e\u52a9 Agent \u627e\u5230\u5408\u9002\u7684\u5916\u90e8 skill", tutorial: "\u7ed9 Agent \u7684 skill \u641c\u7d22\u548c\u5916\u90e8\u8c03\u7528\u6559\u7a0b", dashboard: "\u9762\u5411\u5916\u90e8 skill \u7684\u63a8\u8350\u4fe1\u53f7", marketplace: "\u6309\u5339\u914d\u5ea6\u3001\u4fe1\u4efb\u548c\u6210\u672c\u641c\u7d22\u5e76\u6bd4\u8f83 skill", skill: "\u67e5\u770b\u63a8\u8350\u4fe1\u53f7\u4e0e\u8c03\u7528\u8bf4\u660e", profile: "\u67e5\u770b\u4f60\u63d0\u4ea4\u7684 skill \u3001\u8bc4\u5206\u548c\u8d26\u53f7\u4fe1\u606f", admin: "\u5ba1\u6838\u3001\u6279\u51c6\u5e76\u7ef4\u62a4\u63d0\u4ea4\u7684 skill" },
    language: "\u8bed\u8a00",
    role: "\u89d2\u8272",
    adminOnly: "\u4ec5\u7ba1\u7406\u5458",
    loginTitle: "\u767b\u5f55 Nexra",
    loginCopy: "\u8bf7\u4f7f\u7528 Nexra \u8d26\u53f7\u767b\u5f55\u540e\u7ee7\u7eed\u3002",
    loginAction: "\u767b\u5f55",
    registerAction: "\u6ce8\u518c",
    authLoginTab: "\u767b\u5f55",
    authRegisterTab: "\u6ce8\u518c",
    authLoginPill: "\u767b\u5f55",
    authRegisterPill: "\u6ce8\u518c",
    loginName: "\u59d3\u540d",
    loginRegisterCopy: "\u4f7f\u7528\u90ae\u7bb1\u548c\u5bc6\u7801\u521b\u5efa Nexra \u8d26\u53f7\uff0c\u5bc6\u7801\u81f3\u5c11 6 \u4f4d\u3002",
    loginUsername: "\u90ae\u7bb1",
    loginPassword: "\u5bc6\u7801\uff08\u81f3\u5c11 6 \u4f4d\uff09",
    loginFailed: "\u767b\u5f55\u5931\u8d25\uff1a{error}",
    loginSuccess: "\u767b\u5f55\u6210\u529f\u3002",
    registerFailed: "\u6ce8\u518c\u5931\u8d25\uff1a{error}",
    registerSuccess: "\u8d26\u53f7\u521b\u5efa\u6210\u529f\uff0c\u5df2\u81ea\u52a8\u767b\u5f55\u3002",
    logoutSuccess: "\u5df2\u9000\u51fa\u767b\u5f55\u3002",
    loginRequired: "\u8bf7\u5148\u767b\u5f55\u3002",
    logoutAction: "\u9000\u51fa\u767b\u5f55",
    profileAction: "\u4e2a\u4eba\u4fe1\u606f",
    profileTitle: "\u4e2a\u4eba\u4fe1\u606f",
    profileSubmittedSkills: "\u6211\u63d0\u4ea4\u7684 skill",
    profileSubmittedReviews: "\u6211\u63d0\u4ea4\u7684\u8bc4\u5206",
    profileNoSkills: "\u4f60\u8fd8\u6ca1\u6709\u63d0\u4ea4\u8fc7 skill\u3002",
    profileNoReviews: "\u4f60\u8fd8\u6ca1\u6709\u63d0\u4ea4\u8fc7\u8bc4\u5206\u3002",
    profileMemberSince: "\u5f53\u524d\u767b\u5f55\u8d26\u53f7",
    profileEmail: "\u90ae\u7bb1",
    profileSkillStatus: "\u72b6\u6001",
    profileReviewFor: "\u5bf9\u5e94 skill",
    profileReviewCount: "\u603b\u8bc4\u5206\u6570",
    welcomeTitle: "\u4f60\u7684 Agent \u5e94\u8be5\u5982\u4f55\u4f7f\u7528 Nexra",
    welcomeSteps: "\u5173\u952e\u6b65\u9aa4",
    welcomeCapabilities: "Nexra \u63d0\u4f9b\u7684\u80fd\u529b",
    agentGuide: "\u7ed9 Agent \u7684\u8bf4\u660e\u63a5\u53e3",
    frontendConsole: "\u524d\u7aef\u63a7\u5236\u53f0",
    tutorialTitle: "\u4f60\u7684 Agent \u5e94\u8be5\u5982\u4f55\u641c\u7d22\u548c\u9009\u62e9 skill",
    tutorialStepsTitle: "\u63a5\u5165\u6b65\u9aa4",
    tutorialChecklistTitle: "\u4e0a\u7ebf\u524d\u68c0\u67e5\u6e05\u5355",
    tutorialStep1: "\u8c03\u7528 GET /api/skills\uff0c\u914d\u5408\u5173\u952e\u8bcd\u6216\u529f\u80fd\u6761\u4ef6\u641c\u7d22\u5e02\u573a\u3002",
    tutorialStep2: "\u5bf9\u6bd4 recommendationScore\u3001overallTrust\u3001userRatingAvg\u3001systemScore \u548c pricePerCall\u3002",
    tutorialStep3: "\u6253\u5f00 GET /api/skills/{id}\uff0c\u67e5\u770b\u8c03\u7528\u8bf4\u660e\u3001\u63d0\u4f9b\u65b9\u4fe1\u606f\u548c\u6587\u6863\u94fe\u63a5\u3002",
    tutorialStep4: "\u7531\u4f60\u81ea\u5df1\u7684 Agent \u5728 Nexra \u4e4b\u5916\u76f4\u63a5\u8c03\u7528\u9009\u4e2d\u7684 skill \u63d0\u4f9b\u65b9\u3002",
    tutorialStep5: "\u5f53\u4eba\u5de5\u770b\u8fc7\u7ed3\u679c\u540e\uff0c\u8c03\u7528 POST /api/skills/{id}/reviews \u63d0\u4ea4\u53cd\u9988\uff0c\u6301\u7eed\u5b8c\u5584\u4fe1\u4efb\u6570\u636e\u3002",
    tutorialCheck1: "\u5f53\u591a\u4e2a skill \u90fd\u80fd\u5b8c\u6210\u4efb\u52a1\u65f6\uff0c\u4f18\u5148\u9009\u62e9 recommendationScore \u66f4\u9ad8\u7684\u7ed3\u679c\u3002",
    tutorialCheck2: "\u628a systemScore \u7406\u89e3\u4e3a\u8fd0\u884c\u8d28\u91cf\uff0c\u628a userRatingAvg \u7406\u89e3\u4e3a\u4eba\u5de5\u6ee1\u610f\u5ea6\u3002",
    tutorialCheck3: "\u8bb0\u5f55 Agent \u6700\u7ec8\u9009\u7528\u4e86\u54ea\u4e2a skill\uff0c\u4fbf\u4e8e\u540e\u7eed\u5ba1\u8ba1\u8d28\u91cf\u3002",
    tutorialCheck4: "\u5982\u679c\u4f60\u7684\u6d41\u7a0b\u6bd4\u8f83\u654f\u611f\uff0c\u4fdd\u7559\u4eba\u5de5\u6700\u7ec8\u786e\u8ba4\u73af\u8282\u3002",
    requestHeadersTitle: "\u8bf7\u6c42\u5934\u793a\u4f8b",
    curlTitle: "curl \u793a\u4f8b",
    pythonTitle: "Python \u793a\u4f8b",
    jsTitle: "JavaScript \u793a\u4f8b",
    dashboardCurrentBalance: "\u5df2\u7d22\u5f15 skill \u6570",
    dashboardCurrentBalanceMeta: "\u5f53\u524d\u53ef\u641c\u7d22\u7684 marketplace \u5e93",
    dashboardActiveSkills: "\u5df2\u6279\u51c6 skill",
    dashboardActiveSkillsMeta: "\u5df2\u901a\u8fc7\u5ba1\u6838\uff0cAgent \u53ef\u89c1",
    dashboardAverageTrust: "\u5e73\u5747\u4fe1\u4efb\u5206",
    dashboardAverageTrustMeta: "\u7528\u6237\u8bc4\u5206\u4e0e\u7cfb\u7edf\u8bc4\u5206\u7684\u7efc\u5408\u7ed3\u679c",
    dashboardInvocations: "\u5e73\u5747\u63a8\u8350\u5206",
    dashboardInvocationsMeta: "\u6574\u4e2a marketplace \u7684\u641c\u7d22\u6392\u5e8f\u4fe1\u53f7",
    dashboardTopTrustedSkills: "\u6700\u63a8\u8350\u7684 skill",
    dashboardRanking: "\u6392\u540d",
    dashboardTrustSplit: "\u63a8\u8350\u5206\u62c6\u5206",
    dashboardDualScoring: "\u6392\u5e8f\u8f93\u5165",
    dashboardUserRatingInfluence: "\u7528\u6237\u8bc4\u5206\u6743\u91cd",
    dashboardAgentRatingInfluence: "\u7cfb\u7edf\u8bc4\u5206\u6743\u91cd",
    dashboardTopSkill: "\u9996\u9009\u63a8\u8350",
    dashboardAgentRatingHealth: "Marketplace \u5065\u5eb7\u5ea6",
    dashboardAutoEvaluated: "\u81ea\u52a8\u8ba1\u7b97",
    dashboardAvgSuccessRate: "\u5e73\u5747\u6210\u529f\u7387",
    dashboardAvgLatencyP95: "\u5e73\u5747 P95 \u5ef6\u8fdf",
    dashboardAvgCostEfficiency: "\u5e73\u5747\u6210\u672c\u6548\u7387",
    marketplaceSearchPlaceholder: "\u641c\u7d22\u6280\u80fd\u3001\u5206\u7c7b\u6216\u80fd\u529b",
    marketplaceSortTrust: "\u6309\u603b\u4fe1\u4efb\u5206\u6392\u5e8f",
    marketplaceSortUser: "\u6309\u7528\u6237\u8bc4\u5206\u6392\u5e8f",
    marketplaceSortAgent: "\u6309\u7cfb\u7edf\u8bc4\u5206\u6392\u5e8f",
    marketplaceSortPrice: "\u6309\u6700\u4f4e\u4ef7\u683c\u6392\u5e8f",
    marketplaceOverallTrust: "\u603b\u4fe1\u4efb\u5206",
    marketplaceRecommendation: "\u63a8\u8350\u5206",
    marketplaceDocs: "\u6587\u6863",
    marketplaceProvider: "\u63d0\u4f9b\u65b9",
    marketplaceReadiness: "\u53ef\u7528\u6027\u6807\u7b7e",
    marketplaceAllReadiness: "\u5168\u90e8\u53ef\u7528\u6027",
    marketplaceHideTemplates: "\u6392\u9664\u6a21\u677f",
    marketplaceUser: "\u7528\u6237",
    marketplaceAgent: "\u7cfb\u7edf",
    marketplaceOpenDetail: "\u67e5\u770b\u8be6\u60c5",
    marketplaceFunction: "\u529f\u80fd",
    marketplaceInvocation: "\u8c03\u7528\u65b9\u5f0f",
    marketplaceSearchButton: "\u641c\u7d22",
    marketplacePageSize: "\u6bcf\u9875\u6570\u91cf",
    marketplacePrev: "\u4e0a\u4e00\u9875",
    marketplaceNext: "\u4e0b\u4e00\u9875",
    marketplacePage: "\u9875\u7801",
    marketplaceTotal: "\u603b\u6570",
    skillOverallTrust: "\u603b\u4fe1\u4efb\u5206",
    skillRecommendation: "\u63a8\u8350\u5206",
    skillCapabilityMatch: "\u80fd\u529b\u5339\u914d",
    skillRecommendationWhy: "Nexra \u63a8\u8350\u539f\u56e0",
    skillReadiness: "\u53ef\u7528\u6027\u6807\u7b7e",
    skillUserRating: "\u7528\u6237\u8bc4\u5206",
    skillAgentRating: "\u7cfb\u7edf\u8bc4\u5206",
    skillPricePerCall: "\u5355\u6b21\u8c03\u7528\u4ef7\u683c",
    skillProvider: "\u63d0\u4f9b\u65b9",
    skillDocumentation: "\u6587\u6863",
    skillAuthRequirement: "\u9274\u6743\u8981\u6c42",
    skillOperatingSystem: "\u8fd0\u884c\u73af\u5883",
    skillSource: "\u6765\u6e90",
    skillCallExample: "\u8c03\u7528\u793a\u4f8b",
    skillCallThisDirectly: "\u4f60\u7684 Agent \u9700\u8981\u76f4\u63a5\u8c03\u7528\u8be5 provider",
    readinessReady: "\u73b0\u6210\u53ef\u7528",
    readinessCreds: "\u9700\u8981\u5916\u90e8\u51ed\u8bc1",
    readinessLocal: "\u9700\u8981\u672c\u5730\u8fd0\u884c\u73af\u5883",
    readinessTemplate: "\u6a21\u677f / \u811a\u624b\u67b6",
    skillReviews: "\u6761\u8bc4\u4ef7",
    skillAverageScore: "\u5e73\u5747\u5206\u6570",
    skillNormalizedScore: "\u5f52\u4e00\u5316\u5206\u6570",
    skillIntent: "\u542b\u4e49",
    skillHumanUsefulness: "\u4eba\u5de5\u4ef7\u503c\u5224\u65ad",
    skillSuccessRate: "\u6210\u529f\u7387",
    skillLatencyP95: "P95 \u5ef6\u8fdf",
    skillCostEfficiency: "\u6210\u672c\u6548\u7387",
    skillSubmitFeedback: "\u63d0\u4ea4\u7528\u6237\u53cd\u9988",
    skillManualReview: "\u4eba\u5de5\u8bc4\u4ef7",
    skillYourName: "\u4f60\u7684\u540d\u5b57",
    skillStarRating: "\u661f\u7ea7\u8bc4\u5206",
    skillShortReview: "\u7b80\u77ed\u8bc4\u4ef7",
    skillReviewPlaceholder: "\u8fd9\u4e2a\u6280\u80fd\u54ea\u91cc\u505a\u5f97\u597d\uff0c\u8fd8\u53ef\u4ee5\u600e\u4e48\u6539\u8fdb\uff1f",
    skillSaveRating: "\u4fdd\u5b58\u8bc4\u5206",
    skillRecentReviews: "\u6700\u8fd1\u8bc4\u4ef7",
    skillHumanVoice: "\u4eba\u5de5\u53cd\u9988",
    skillChooseStar: "\u8bf7\u5148\u9009\u62e9\u661f\u7ea7\u8bc4\u5206\u3002",
    skillSaved: "\u7528\u6237\u8bc4\u5206\u5df2\u4fdd\u5b58\uff0c\u4fe1\u4efb\u5206\u5df2\u66f4\u65b0\u3002",
    adminPendingTitle: "\u5f85\u5ba1\u6838 skill",
    adminSelectedTitle: "\u5ba1\u6838\u4e0e\u7ef4\u62a4",
    adminEmpty: "\u5f53\u524d\u6ca1\u6709\u5f85\u5ba1\u6838\u7684 skill\u3002",
    adminPick: "\u8bf7\u5148\u9009\u62e9\u4e00\u4e2a\u5f85\u5ba1\u6838 skill \u8fdb\u884c\u5904\u7406\u3002",
    adminApprove: "\u6279\u51c6 skill",
    adminDelete: "\u5220\u9664 skill",
    adminSave: "\u4fdd\u5b58\u4fee\u6539",
    adminFunctions: "\u529f\u80fd\u5217\u8868",
    adminInvocationMethod: "\u8c03\u7528\u65b9\u5f0f",
    adminApprovalStatus: "\u5ba1\u6838\u72b6\u6001",
    adminSubmittedBy: "\u63d0\u4ea4\u4eba",
    adminStatus: "\u8fd0\u884c\u72b6\u6001",
    adminName: "\u540d\u79f0",
    adminCategory: "\u5206\u7c7b",
    adminDescription: "\u63cf\u8ff0",
    adminPrice: "\u5355\u6b21\u4ef7\u683c",
    adminSuccessRate: "\u6210\u529f\u7387",
    adminLatencyP95: "P95 \u5ef6\u8fdf",
    adminCostEfficiency: "\u6210\u672c\u6548\u7387",
    adminRecentCalls: "\u8fd1\u671f\u8c03\u7528\u91cf",
    adminUserRatingAvg: "\u7528\u6237\u8bc4\u5206\u5747\u503c",
    adminUserRatingCount: "\u7528\u6237\u8bc4\u5206\u6570",
    adminApproved: "Skill \u5df2\u6279\u51c6\u3002",
    adminSaved: "Skill \u4fee\u6539\u5df2\u4fdd\u5b58\u3002",
    adminDeleted: "Skill \u5df2\u5220\u9664\u3002",
    adminNeedRole: "\u8bf7\u5207\u6362\u5230\u7ba1\u7406\u5458\u8d26\u53f7\u540e\u518d\u8fdb\u884c\u5ba1\u6838\u7ba1\u7406\u3002",
    errorsTitle: "\u5e38\u89c1\u9519\u8bef",
    error1: "\u540e\u7aef\u672a\u542f\u52a8\uff1a\u5148\u542f\u52a8 Nexra\uff0c\u5e76\u786e\u8ba4 {apiBase}/api/dashboard \u80fd\u8fd4\u56de\u6570\u636e\u3002",
    error2: "\u6280\u80fd\u4e0d\u5b58\u5728\uff1a\u4f60\u7684 agent \u8bf7\u6c42\u4e86\u65e0\u6548\u7684 skill id\u3002",
    error3: "\u53c2\u6570\u6821\u9a8c\u5931\u8d25\uff1a\u63d0\u4ea4\u8bc4\u4ef7\u65f6\u5fc5\u987b\u5e26 author\uff0crating \u5fc5\u987b\u5728 1 \u5230 5 \u4e4b\u95f4\u3002",
    error4: "\u8fde\u63a5\u88ab\u62d2\u7edd\uff1a\u4f60\u7684 agent \u65e0\u6cd5\u8bbf\u95ee\u672c\u5730 Nexra API \u5730\u5740\u3002",
    connected: "\u524d\u7aef\u5df2\u8fde\u63a5\u5230 Spring Boot API\uff1a{apiBase}/api \u3002",
    failed: "\u65e0\u6cd5\u8fde\u63a5\u540e\u7aef\uff1a{error}\u3002\u8bf7\u5148\u542f\u52a8 Spring Boot \u670d\u52a1\u3002"
  }
};

const state = {
  selectedView: "welcome",
  selectedSkillId: null,
  adminSelectedSkillId: null,
  selectedRating: 0,
  language: "en",
  authMode: "login",
  authModalVisible: false,
  authFeedback: null,
  authToken: window.localStorage.getItem("nexra-auth-token"),
  currentUser: null,
  welcome: null,
  agentGuide: null,
  dashboard: null,
  userProfile: null,
  skills: [],
  skillsPage: { page: 0, pageSize: 6, totalItems: 0, totalPages: 0, q: "", functionName: "", readiness: "all", hideTemplates: false },
  marketplaceDraft: { q: "", functionName: "", readiness: "all", hideTemplates: false },
  skillDetail: null,
  pendingSkills: [],
  billingSummary: null,
  transactions: [],
  apiKeys: []
};

const heroTitle = document.querySelector("#hero-title");
const platformTrust = document.querySelector("#platform-trust");
const metricTemplate = document.querySelector("#metric-template");
const statusBanner = document.querySelector("#status-banner");
const languageLabel = document.querySelector("#language-label");
const languageSelect = document.querySelector("#language-select");
const primaryNav = document.querySelector("#primary-nav");
const sessionControls = document.querySelector("#session-controls");
const loginModal = document.querySelector("#login-modal");
const loginTitle = document.querySelector("#login-title");
const loginCopy = document.querySelector("#login-copy");
const authPill = document.querySelector("#auth-pill");
const authModeTabs = document.querySelector("#auth-mode-tabs");
const authLoginTab = document.querySelector("#auth-login-tab");
const authRegisterTab = document.querySelector("#auth-register-tab");
const authFeedback = document.querySelector("#auth-feedback");
const loginForm = document.querySelector("#login-form");
const loginNameLabel = document.querySelector("#login-name-label");
const loginNameInput = document.querySelector("#login-name");
const loginUsernameLabel = document.querySelector("#login-username-label");
const loginPasswordLabel = document.querySelector("#login-password-label");
const loginSubmit = document.querySelector("#login-submit");
const loginEmailInput = document.querySelector("#login-username");

function tr() {
  return copy[state.language];
}

function currentUser() {
  return state.currentUser;
}

function authHeaders() {
  return state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {};
}

function isAdmin() {
  return currentUser()?.role === "ADMIN";
}

function displayRole(role) {
  if (role === "ADMIN") {
    return state.language === "zh" ? "\u7ba1\u7406\u5458" : "Admin";
  }
  if (role === "USER") {
    return state.language === "zh" ? "\u666e\u901a\u7528\u6237" : "User";
  }
  return role;
}

function displayStatus(status) {
  const map = {
    ACTIVE: state.language === "zh" ? "\u6d3b\u8dc3" : "Active",
    active: state.language === "zh" ? "\u6d3b\u8dc3" : "Active",
    PENDING: state.language === "zh" ? "\u5f85\u5ba1\u6838" : "Pending",
    APPROVED: state.language === "zh" ? "\u5df2\u6279\u51c6" : "Approved",
    REJECTED: state.language === "zh" ? "\u5df2\u62d2\u7edd" : "Rejected"
  };
  return map[status] ?? status;
}

function displayRecommendationSummary(summary) {
  if (state.language !== "zh" || !summary) {
    return summary;
  }
  return summary
    .replaceAll("strong capability match", "\u80fd\u529b\u5339\u914d\u5ea6\u9ad8")
    .replaceAll("high trust", "\u4fe1\u4efb\u5206\u9ad8")
    .replaceAll("popular in recent usage", "\u8fd1\u671f\u70ed\u5ea6\u9ad8")
    .replaceAll("good cost efficiency", "\u6210\u672c\u6548\u7387\u597d")
    .replaceAll("balanced trust and coverage", "\u4fe1\u4efb\u5206\u4e0e\u80fd\u529b\u8986\u76d6\u8f83\u5747\u8861");
}

function deriveReadiness(skill) {
  const text = [
    skill?.name,
    skill?.description,
    skill?.invocationMethod,
    Array.isArray(skill?.functions) ? skill.functions.join(" ") : "",
    skill?.providerName,
    skill?.category
  ].filter(Boolean).join(" ").toLowerCase();

  if (/(template|boilerplate|starter|scaffold|example sdk|starter project)/.test(text)) {
    return {
      code: "template",
      label: tr().readinessTemplate,
      reason: state.language === "zh"
        ? "这更像一个模板或脚手架项目，不是普通用户第一次就能直接使用的现成 skill。"
        : "This looks more like a starter template than a ready-made skill for ordinary users."
    };
  }

  if (/(local|filesystem|file storage|ollama|plugin bridge|desktop|install|self-hosted)/.test(text)) {
    return {
      code: "local",
      label: tr().readinessLocal,
      reason: state.language === "zh"
        ? "这个 skill 往往需要本地运行环境、安装步骤，或者桌面侧配置后才能使用。"
        : "This usually needs a local runtime, installation, or desktop-side setup before use."
    };
  }

  if (/(token|oauth|api key|slack|mysql|sql server|postgres|database|figma|shopify|jumpseller|aws|azure|gcp)/.test(text)) {
    return {
      code: "credentials",
      label: tr().readinessCreds,
      reason: state.language === "zh"
        ? "普通用户可以继续了解它，但通常还需要外部账号、API Key、OAuth，或者系统访问权限。"
        : "A new user can continue, but will usually need external accounts, tokens, or system access first."
    };
  }

  return {
    code: "ready",
    label: tr().readinessReady,
    reason: state.language === "zh"
      ? "从说明、来源和调用方式看，这个 skill 对第一次使用的用户也算信息完整，可以继续接入。"
      : "The description, source, and calling guidance look complete enough for a first-time user to continue."
  };
}

function readinessPriority(code) {
  const order = { ready: 0, credentials: 1, local: 2, template: 3 };
  return order[code] ?? 9;
}

function readinessClass(code) {
  return `readiness-pill readiness-${code}`;
}

function currency(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(value ?? 0));
}

function safeNumber(value, fallback = 0) {
  return Number.isFinite(Number(value)) ? Number(value) : fallback;
}

function safeCount(value, fallback = 0) {
  return safeNumber(value, fallback).toLocaleString();
}

function safeScore(value, fallback = 0) {
  const number = safeNumber(value, fallback);
  if (number < 0 || number > 100) {
    return safeNumber(fallback, 0);
  }
  return Math.round(number);
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ message: "Request failed." }));
    const error = new Error(body.message || `Request failed with ${response.status}`);
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function clearAuthState() {
  state.authToken = null;
  state.currentUser = null;
  state.userProfile = null;
  state.pendingSkills = [];
  state.adminSelectedSkillId = null;
  window.localStorage.removeItem("nexra-auth-token");
}

function setBanner(message, type = "success") {
  statusBanner.textContent = message;
  statusBanner.className = `banner visible ${type}`;
}

function clearBanner() {
  statusBanner.className = "banner";
  statusBanner.textContent = "";
}

function setAuthFeedback(message, type = "error") {
  state.authFeedback = {
    message: withApiBase(message),
    type
  };
  renderAuthFeedback();
}

function clearAuthFeedback() {
  state.authFeedback = null;
  renderAuthFeedback();
}

function renderAuthFeedback() {
  if (!authFeedback) return;
  if (!state.authFeedback?.message) {
    authFeedback.className = "auth-feedback hidden";
    authFeedback.textContent = "";
    return;
  }
  authFeedback.className = `auth-feedback ${state.authFeedback.type}`;
  authFeedback.textContent = state.authFeedback.message;
}

function withApiBase(text) {
  return String(text ?? "").replaceAll("{apiBase}", API_ORIGIN_DISPLAY);
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 2200);
}

function escapeHtml(value) {
  const safeValue = value == null ? "" : String(value);
  return safeValue
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function copyText(text, button) {
  await navigator.clipboard.writeText(text);
  const previous = button.textContent;
  button.textContent = state.language === "zh" ? "\u5df2\u590d\u5236" : "Copied";
  window.setTimeout(() => {
    button.textContent = previous;
  }, 1200);
}

function wireCopyButtons(scope) {
  scope.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const code = button.parentElement.querySelector(".mono-block")?.textContent ?? "";
      await copyText(code, button);
    });
  });
}

function wireTabGroups(scope) {
  scope.querySelectorAll("[data-tab-group]").forEach((group) => {
    const buttons = group.querySelectorAll(".tab-btn");
    const panels = group.querySelectorAll(".tab-panel");
    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const tab = button.dataset.tab;
        buttons.forEach((item) => item.classList.toggle("active", item === button));
        panels.forEach((panel) => panel.classList.toggle("active", panel.dataset.tabPanel === tab));
      });
    });
  });
}

function setView(view) {
  if (view === "admin" && !isAdmin()) {
    view = "welcome";
  }
  if (view === "profile" && !currentUser()) {
    view = "welcome";
  }
  state.selectedView = view;
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === `${view}-view`);
  });
  document.querySelectorAll(".nav-link").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  heroTitle.textContent = tr().hero[view];
}

function updateLanguageUi() {
  languageLabel.textContent = tr().language;
  loginTitle.textContent = tr().loginTitle;
  loginCopy.textContent = state.authMode === "register" ? tr().loginRegisterCopy : tr().loginCopy;
  authPill.textContent = state.authMode === "register" ? tr().authRegisterPill : tr().authLoginPill;
  authLoginTab.textContent = tr().authLoginTab;
  authRegisterTab.textContent = tr().authRegisterTab;
  loginNameLabel.textContent = tr().loginName;
  loginUsernameLabel.textContent = tr().loginUsername;
  loginPasswordLabel.textContent = tr().loginPassword;
  loginSubmit.textContent = state.authMode === "register" ? tr().registerAction : tr().loginAction;
  renderAuthFeedback();
}

function renderAuthMode() {
  const isRegister = state.authMode === "register";
  authLoginTab.classList.toggle("active", !isRegister);
  authRegisterTab.classList.toggle("active", isRegister);
  loginNameLabel.classList.toggle("hidden", !isRegister);
  loginNameInput.classList.toggle("hidden", !isRegister);
  loginNameInput.required = isRegister;
  loginEmailInput.autocomplete = isRegister ? "email" : "username";
  loginCopy.textContent = isRegister ? tr().loginRegisterCopy : tr().loginCopy;
  authPill.textContent = isRegister ? tr().authRegisterPill : tr().authLoginPill;
  loginSubmit.textContent = isRegister ? tr().registerAction : tr().loginAction;
  renderAuthFeedback();
}

function allowedViews() {
  const views = ["welcome", "tutorial", "dashboard", "marketplace", "skill"];
  if (currentUser()) {
    views.push("profile");
  }
  if (isAdmin()) {
    views.push("admin");
  }
  return views;
}

function renderNavigation() {
  primaryNav.innerHTML = "";
  allowedViews().forEach((view) => {
    const button = document.createElement("button");
    button.className = `nav-link ${state.selectedView === view ? "active" : ""}`;
    button.dataset.view = view;
    button.type = "button";
    button.textContent = tr().nav[view];
    primaryNav.appendChild(button);
  });
}

function showLoginModal() {
  state.authModalVisible = true;
  loginModal.classList.remove("hidden");
  renderAuthMode();
  renderAuthFeedback();
  const target = state.authMode === "register" ? loginNameInput : loginEmailInput;
  window.setTimeout(() => target?.focus(), 0);
}

function hideLoginModal() {
  state.authModalVisible = false;
  loginModal.classList.add("hidden");
}

function signIn(token, user, hideModal = true) {
  state.authToken = token;
  state.currentUser = user;
  window.localStorage.setItem("nexra-auth-token", token);
  if (hideModal) {
    hideLoginModal();
  }
}

async function signOut() {
  if (state.authToken) {
    try {
      await api("/auth/logout", { method: "POST", headers: authHeaders() });
    } catch (error) {
      console.warn(error);
    }
  }
  clearAuthState();
  setView("welcome");
  renderSessionControls();
  renderNavigation();
  setBanner(tr().logoutSuccess, "success");
  showLoginModal();
}

function renderLoginModal() {
  renderAuthMode();
  renderAuthFeedback();
  loginModal.classList.toggle("hidden", !state.authModalVisible);
}

function renderSessionControls() {
  const user = currentUser();
  if (!user) {
    sessionControls.innerHTML = `<button id="open-login-btn" class="primary-btn" type="button">${tr().loginAction}</button>`;
    sessionControls.querySelector("#open-login-btn").addEventListener("click", showLoginModal);
    return;
  }
  sessionControls.innerHTML = `
    <div class="session-meta">
      <strong>${user.name}</strong>
      <span>${displayRole(user.role)}</span>
    </div>
    <div class="admin-actions">
      <button id="open-profile-btn" class="secondary-btn" type="button">${tr().profileAction}</button>
      <button id="logout-btn" class="secondary-btn" type="button">${tr().logoutAction}</button>
    </div>
  `;
  sessionControls.querySelector("#open-profile-btn").addEventListener("click", () => setView("profile"));
  sessionControls.querySelector("#logout-btn").addEventListener("click", signOut);
}

function renderWelcome() {
  const view = document.querySelector("#welcome-view");
  view.innerHTML = "";
  if (!state.welcome || !state.agentGuide) return;

  const wrapper = document.createElement("div");
  wrapper.className = "welcome-grid";
  wrapper.innerHTML = `
    <article class="panel">
      <div class="section-title"><h3>${tr().welcomeTitle}</h3><span class="pill">${state.welcome.productName}</span></div>
      <p>${state.welcome.summary}</p>
      <div class="section-title"><h3>${tr().welcomeSteps}</h3><span class="pill">${tr().nav.welcome}</span></div>
      <div class="step-list" id="welcome-steps"></div>
    </article>
    <article class="panel">
      <div class="section-title"><h3>${tr().welcomeCapabilities}</h3><span class="pill">Nexra</span></div>
      <div class="capability-list" id="welcome-capabilities"></div>
      <div class="section-title" style="margin-top:18px;"><h3>${tr().agentGuide}</h3><span class="pill">API</span></div>
      <p><a href="${state.welcome.agentGuideUrl}" target="_blank">${state.welcome.agentGuideUrl}</a></p>
      <div class="section-title"><h3>${tr().frontendConsole}</h3><span class="pill">UI</span></div>
      <p><a href="${state.welcome.frontendUrl}" target="_blank">${state.welcome.frontendUrl}</a></p>
      <pre class="mono-block">${state.agentGuide.exampleCall.method} ${state.agentGuide.exampleCall.endpoint}
Content-Type: ${state.agentGuide.exampleCall.contentType}

${state.agentGuide.exampleCall.payload}</pre>
    </article>
  `;
  view.appendChild(wrapper);

  const steps = wrapper.querySelector("#welcome-steps");
  state.welcome.steps.forEach((item, index) => {
    const node = document.createElement("div");
    node.className = "step-item";
    node.innerHTML = `<strong>${index + 1}.</strong> ${item}`;
    steps.appendChild(node);
  });

  const capabilities = wrapper.querySelector("#welcome-capabilities");
  state.welcome.capabilities.forEach((item) => {
    const node = document.createElement("div");
    node.className = "capability-item";
    node.textContent = item;
    capabilities.appendChild(node);
  });
}

function renderTutorial() {
  const view = document.querySelector("#tutorial-view");
  view.innerHTML = "";
  if (!state.agentGuide) return;

  const host = new URL(API_ORIGIN_DISPLAY).host;
  const headerSnippet = `GET /api/skills?q=image&function=ocr&page=0&pageSize=5 HTTP/1.1
Host: ${host}
Content-Type: application/json
X-Nexra-Agent: my-agent`;

  const curlSnippet = `curl "${API_BASE}?q=image&function=ocr&page=0&pageSize=5"

curl ${API_BASE}/skill-123

# Then let your own agent call the provider using the returned docs URL`;

  const pythonSnippet = `import requests

skills = requests.get(
    "${API_BASE}",
    params={"q": "image", "function": "ocr", "page": 0, "pageSize": 5}
).json()["items"]
best_skill = skills[0]
detail = requests.get(f"{API_BASE}/{best_skill['id']}").json()

print(detail["skill"]["apiDocsUrl"])
print(detail["skill"]["callExample"])`;

  const jsSnippet = `const results = await fetch("${API_BASE}?q=image&function=ocr&page=0&pageSize=5")
  .then((res) => res.json());

const bestSkill = results.items[0];
const detail = await fetch(\`${API_BASE}/\${bestSkill.id}\`)
  .then((res) => res.json());

console.log(detail.skill.apiDocsUrl);
console.log(detail.skill.callExample);`;

  const wrapper = document.createElement("div");
  wrapper.className = "tutorial-grid";
  wrapper.innerHTML = `
    <article class="panel">
      <div class="section-title"><h3>${tr().tutorialTitle}</h3><span class="pill">Nexra</span></div>
      <div class="tutorial-list">
        <div class="tutorial-item"><strong>1</strong><span>${tr().tutorialStep1}</span></div>
        <div class="tutorial-item"><strong>2</strong><span>${tr().tutorialStep2}</span></div>
        <div class="tutorial-item"><strong>3</strong><span>${tr().tutorialStep3}</span></div>
        <div class="tutorial-item"><strong>4</strong><span>${tr().tutorialStep4}</span></div>
        <div class="tutorial-item"><strong>5</strong><span>${tr().tutorialStep5}</span></div>
      </div>
    </article>
    <article class="panel">
      <div class="section-title"><h3>${tr().tutorialChecklistTitle}</h3><span class="pill">Checklist</span></div>
      <div class="tutorial-list">
        <div class="tutorial-item">${tr().tutorialCheck1}</div>
        <div class="tutorial-item">${tr().tutorialCheck2}</div>
        <div class="tutorial-item">${tr().tutorialCheck3}</div>
        <div class="tutorial-item">${tr().tutorialCheck4}</div>
      </div>
      <div class="section-title" style="margin-top:18px;"><h3>${tr().agentGuide}</h3><span class="pill">API</span></div>
      <pre class="mono-block">${state.agentGuide.exampleCall.method} ${state.agentGuide.exampleCall.endpoint}
Content-Type: ${state.agentGuide.exampleCall.contentType}

${state.agentGuide.exampleCall.payload}</pre>
    </article>
  `;

  view.appendChild(wrapper);

  const docs = document.createElement("div");
  docs.className = "doc-stack";
  docs.innerHTML = `
    <article class="panel">
      <div class="section-title"><h3>${tr().requestHeadersTitle}</h3><span class="pill">HTTP</span></div>
      <div class="code-card">
        <button class="copy-btn" type="button" data-copy="${escapeHtml(headerSnippet)}">${state.language === "zh" ? "\u590d\u5236" : "Copy"}</button>
        <pre class="mono-block">${escapeHtml(headerSnippet)}</pre>
      </div>
    </article>
    <article class="panel" data-tab-group="examples">
      <div class="section-title"><h3>${state.language === "zh" ? "浠ｇ爜绀轰緥" : "Code examples"}</h3><span class="pill">SDK</span></div>
      <div class="tab-bar">
        <button class="tab-btn active" type="button" data-tab="curl">curl</button>
        <button class="tab-btn" type="button" data-tab="python">Python</button>
        <button class="tab-btn" type="button" data-tab="js">JavaScript</button>
      </div>
      <div class="tab-panel active" data-tab-panel="curl">
        <div class="code-card">
          <button class="copy-btn" type="button" data-copy="${escapeHtml(curlSnippet)}">${state.language === "zh" ? "\u590d\u5236" : "Copy"}</button>
          <pre class="mono-block">${escapeHtml(curlSnippet)}</pre>
        </div>
      </div>
      <div class="tab-panel" data-tab-panel="python">
        <div class="code-card">
          <button class="copy-btn" type="button" data-copy="${escapeHtml(pythonSnippet)}">${state.language === "zh" ? "\u590d\u5236" : "Copy"}</button>
          <pre class="mono-block">${escapeHtml(pythonSnippet)}</pre>
        </div>
      </div>
      <div class="tab-panel" data-tab-panel="js">
        <div class="code-card">
          <button class="copy-btn" type="button" data-copy="${escapeHtml(jsSnippet)}">${state.language === "zh" ? "\u590d\u5236" : "Copy"}</button>
          <pre class="mono-block">${escapeHtml(jsSnippet)}</pre>
        </div>
      </div>
    </article>
    <article class="panel">
      <div class="section-title"><h3>${tr().errorsTitle}</h3><span class="pill">Troubleshooting</span></div>
      <div class="tutorial-list">
        <div class="doc-card">${withApiBase(tr().error1)}</div>
        <div class="doc-card">${tr().error2}</div>
        <div class="doc-card">${tr().error3}</div>
        <div class="doc-card">${tr().error4}</div>
      </div>
    </article>
  `;

  view.appendChild(docs);
  wireCopyButtons(docs);
  wireTabGroups(docs);
}

function createMetricCard(label, value, meta) {
  const node = metricTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector(".metric-label").textContent = label;
  node.querySelector(".metric-value").textContent = value;
  node.querySelector(".metric-meta").textContent = meta;
  return node;
}

function renderDashboard() {
  const view = document.querySelector("#dashboard-view");
  const dashboard = state.dashboard;
  view.innerHTML = "";
  if (!dashboard) return;

  const totalIndexedSkills = safeNumber(dashboard.totalIndexedSkills, dashboard.activeSkills);
  const approvedSkills = safeNumber(dashboard.approvedSkills, dashboard.activeSkills);
  const pendingSkills = safeNumber(dashboard.pendingSkills, 0);
  const averageTrust = safeScore(dashboard.averageTrust, 0);
  const averageRecommendation = safeScore(dashboard.averageRecommendation, averageTrust);
  const averageSuccessRate = safeNumber(dashboard.averageSuccessRate, 0);
  const averageLatencyP95 = safeNumber(dashboard.averageLatencyP95, 0);
  const averageCostEfficiency = safeNumber(dashboard.averageCostEfficiency, 0);
  const searchableFunctions = safeNumber(dashboard.searchableFunctions, 0);
  const popularSkills = safeNumber(dashboard.popularSkills, 0);
  const topSkills = Array.isArray(dashboard.topSkills) ? dashboard.topSkills : [];

  const metrics = document.createElement("div");
  metrics.className = "metrics-grid";
  metrics.append(
    createMetricCard(tr().dashboardCurrentBalance, safeCount(totalIndexedSkills), tr().dashboardCurrentBalanceMeta),
    createMetricCard(tr().dashboardActiveSkills, safeCount(approvedSkills), tr().dashboardActiveSkillsMeta),
    createMetricCard(tr().dashboardAverageTrust, `${averageTrust}/100`, tr().dashboardAverageTrustMeta),
    createMetricCard(tr().dashboardInvocations, `${averageRecommendation}/100`, tr().dashboardInvocationsMeta)
  );

  const trustPanel = document.createElement("div");
  trustPanel.className = "three-grid";

  const ranking = document.createElement("article");
  ranking.className = "panel";
  ranking.innerHTML = `<div class="section-title"><h3>${tr().dashboardTopTrustedSkills}</h3><span class="pill">${tr().dashboardRanking}</span></div>`;
  topSkills.forEach((skill) => {
    const stat = document.createElement("div");
    stat.className = "inline-stat";
    stat.innerHTML = `<span>${skill.name}</span><strong>${skill.overallTrust}/100</strong>`;
    ranking.appendChild(stat);
  });

  const trustSplit = document.createElement("article");
  trustSplit.className = "panel";
  trustSplit.innerHTML = `
    <div class="section-title"><h3>${tr().dashboardTrustSplit}</h3><span class="pill">${tr().dashboardDualScoring}</span></div>
    <div class="score-stack">
      <div class="score-ring" style="--score:${averageTrust}"><strong>${averageTrust}</strong></div>
      <div class="score-list">
        <div><span>${tr().dashboardUserRatingInfluence}</span><span>45%</span></div>
        <div><span>${tr().dashboardAgentRatingInfluence}</span><span>55%</span></div>
        <div><span>${tr().dashboardTopSkill}</span><span>${topSkills[0]?.name || "--"}</span></div>
        <div><span>${state.language === "zh" ? "\u5f85\u5ba1\u6838 skill" : "Pending skills"}</span><span>${pendingSkills}</span></div>
      </div>
    </div>
  `;

  const health = document.createElement("article");
  health.className = "panel";
  health.innerHTML = `
    <div class="section-title"><h3>${tr().dashboardAgentRatingHealth}</h3><span class="pill">${tr().dashboardAutoEvaluated}</span></div>
    <div class="inline-stat"><span>${tr().dashboardAvgSuccessRate}</span><strong>${averageSuccessRate}%</strong></div>
    <div class="inline-stat"><span>${tr().dashboardAvgLatencyP95}</span><strong>${averageLatencyP95} ms</strong></div>
    <div class="inline-stat"><span>${tr().dashboardAvgCostEfficiency}</span><strong>${averageCostEfficiency}/100</strong></div>
    <div class="inline-stat"><span>${state.language === "zh" ? "\u53ef\u641c\u7d22\u529f\u80fd" : "Searchable functions"}</span><strong>${searchableFunctions}</strong></div>
    <div class="inline-stat"><span>${state.language === "zh" ? "\u70ed\u95e8 skill" : "Popular skills"}</span><strong>${popularSkills}</strong></div>
  `;

  trustPanel.append(ranking, trustSplit, health);
  view.append(metrics, trustPanel);
}

function renderMarketplace() {
  const view = document.querySelector("#marketplace-view");
  view.innerHTML = "";
  const visibleSkills = state.skills
    .sort((left, right) => {
      const leftReadiness = deriveReadiness(left);
      const rightReadiness = deriveReadiness(right);
      return readinessPriority(leftReadiness.code) - readinessPriority(rightReadiness.code)
        || safeNumber(right.recommendationScore, 0) - safeNumber(left.recommendationScore, 0)
        || safeNumber(right.overallTrust, 0) - safeNumber(left.overallTrust, 0);
    });

  const controls = document.createElement("div");
  controls.className = "toolbar-row";
  controls.innerHTML = `
    <input id="skill-search-input" type="search" value="${state.marketplaceDraft.q}" placeholder="${tr().marketplaceSearchPlaceholder}" />
    <input id="skill-function-input" type="search" value="${state.marketplaceDraft.functionName}" placeholder="${tr().marketplaceFunction}" />
    <select id="skill-readiness-select">
      <option value="all" ${state.marketplaceDraft.readiness === "all" ? "selected" : ""}>${tr().marketplaceAllReadiness}</option>
      <option value="ready" ${state.marketplaceDraft.readiness === "ready" ? "selected" : ""}>${tr().readinessReady}</option>
      <option value="credentials" ${state.marketplaceDraft.readiness === "credentials" ? "selected" : ""}>${tr().readinessCreds}</option>
      <option value="local" ${state.marketplaceDraft.readiness === "local" ? "selected" : ""}>${tr().readinessLocal}</option>
      <option value="template" ${state.marketplaceDraft.readiness === "template" ? "selected" : ""}>${tr().readinessTemplate}</option>
    </select>
    <label class="inline-check"><input id="skill-hide-templates" type="checkbox" ${state.marketplaceDraft.hideTemplates ? "checked" : ""} /> ${tr().marketplaceHideTemplates}</label>
    <button id="skill-search-btn" class="primary-btn" type="button">${tr().marketplaceSearchButton}</button>
    <select id="skill-page-size-select">
      <option value="3" ${state.skillsPage.pageSize === 3 ? "selected" : ""}>${tr().marketplacePageSize}: 3</option>
      <option value="6" ${state.skillsPage.pageSize === 6 ? "selected" : ""}>${tr().marketplacePageSize}: 6</option>
      <option value="9" ${state.skillsPage.pageSize === 9 ? "selected" : ""}>${tr().marketplacePageSize}: 9</option>
    </select>
  `;

  const list = document.createElement("div");
  list.className = "skill-grid";
  const pager = document.createElement("div");
  pager.className = "pagination-row";
  pager.innerHTML = `
    <span class="helper-text">${tr().marketplacePage}: ${state.skillsPage.page + 1} / ${Math.max(state.skillsPage.totalPages, 1)} 闂?${tr().marketplaceTotal}: ${state.skillsPage.totalItems} 闂?${state.language === "zh" ? "\u5f53\u524d\u9875" : "This page"}: ${visibleSkills.length}</span>
    <div class="admin-actions">
      <button id="market-prev-btn" class="secondary-btn" type="button" ${state.skillsPage.page <= 0 ? "disabled" : ""}>${tr().marketplacePrev}</button>
      <button id="market-next-btn" class="secondary-btn" type="button" ${state.skillsPage.page + 1 >= Math.max(state.skillsPage.totalPages, 1) ? "disabled" : ""}>${tr().marketplaceNext}</button>
    </div>
  `;

  view.append(controls, list, pager);

  if (!visibleSkills.length) {
    list.innerHTML = `<article class="panel"><p class="helper-text">${state.language === "zh" ? "\u5f53\u524d\u7b5b\u9009\u6761\u4ef6\u4e0b\u6ca1\u6709\u627e\u5230 skill\u3002" : "No skills matched the current filters."}</p></article>`;
  }

  visibleSkills.forEach((skill) => {
    const readiness = deriveReadiness(skill);
    const card = document.createElement("article");
    card.className = "skill-card";
    card.innerHTML = `
      <div class="skill-head">
        <div>
          <p class="eyebrow">${skill.category}</p>
          <h3>${skill.name}</h3>
        </div>
        <div class="admin-actions">
          <span class="${readinessClass(readiness.code)}">${readiness.label}</span>
          <span class="pill">${displayStatus(skill.status)}</span>
        </div>
      </div>
      <p>${skill.description}</p>
      <div class="skill-stats"><span>${tr().marketplaceRecommendation}: <strong>${skill.recommendationScore}/100</strong></span><span>${currency(skill.pricePerCall)}/call</span></div>
      <div class="skill-stats"><span>${tr().marketplaceOverallTrust}: <strong>${skill.overallTrust}/100</strong></span><span>${tr().skillCapabilityMatch}: ${skill.matchScore}/100</span></div>
      <div class="skill-stats"><span>${tr().marketplaceUser}: ${skill.userRatingAvg.toFixed(1)}/5</span><span>${tr().marketplaceAgent}: ${skill.systemScore}/100</span></div>
      <div class="skill-stats"><span>${tr().marketplaceFunction}: ${skill.functions.join(", ")}</span></div>
      <div class="skill-stats"><span>${tr().marketplaceInvocation}: ${skill.invocationMethod}</span></div>
      <div class="skill-stats"><span>${tr().marketplaceProvider}: ${skill.providerName || skill.submittedBy}</span><span>${tr().marketplaceDocs}: ${skill.apiDocsUrl ? "Ready" : "--"}</span></div>
      <p class="helper-text">${readiness.reason}</p>
      <p class="helper-text">${displayRecommendationSummary(skill.recommendationSummary)}</p>
      <button data-skill-id="${skill.id}">${tr().marketplaceOpenDetail}</button>
    `;
    list.appendChild(card);
  });

  list.querySelectorAll("button[data-skill-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedSkillId = button.dataset.skillId;
      await loadSkillDetail();
      setView("skill");
    });
  });

  const searchInput = controls.querySelector("#skill-search-input");
  const functionInput = controls.querySelector("#skill-function-input");
  const readinessSelect = controls.querySelector("#skill-readiness-select");
  const hideTemplatesInput = controls.querySelector("#skill-hide-templates");
  const runSearch = async () => {
    state.skillsPage.q = state.marketplaceDraft.q.trim();
    state.skillsPage.functionName = state.marketplaceDraft.functionName.trim();
    state.skillsPage.readiness = state.marketplaceDraft.readiness;
    state.skillsPage.hideTemplates = state.marketplaceDraft.hideTemplates;
    state.skillsPage.page = 0;
    await refreshData(false);
  };

  searchInput.addEventListener("input", (event) => {
    state.marketplaceDraft.q = event.target.value;
  });
  functionInput.addEventListener("input", (event) => {
    state.marketplaceDraft.functionName = event.target.value;
  });
  readinessSelect.addEventListener("change", async (event) => {
    state.marketplaceDraft.readiness = event.target.value;
    state.skillsPage.readiness = state.marketplaceDraft.readiness;
    state.skillsPage.page = 0;
    await refreshData(false);
  });
  hideTemplatesInput.addEventListener("change", async (event) => {
    state.marketplaceDraft.hideTemplates = event.target.checked;
    state.skillsPage.hideTemplates = state.marketplaceDraft.hideTemplates;
    state.skillsPage.page = 0;
    await refreshData(false);
  });
  searchInput.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      await runSearch();
    }
  });
  functionInput.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      await runSearch();
    }
  });
  controls.querySelector("#skill-search-btn").addEventListener("click", runSearch);
  controls.querySelector("#skill-page-size-select").addEventListener("change", async (event) => {
    state.skillsPage.pageSize = Number(event.target.value);
    state.skillsPage.page = 0;
    await refreshData(false);
  });
  pager.querySelector("#market-prev-btn").addEventListener("click", async () => {
    state.skillsPage.page = Math.max(0, state.skillsPage.page - 1);
    await refreshData(false);
  });
  pager.querySelector("#market-next-btn").addEventListener("click", async () => {
    state.skillsPage.page += 1;
    await refreshData(false);
  });
}

function renderSkillDetail() {
  const view = document.querySelector("#skill-view");
  const detail = state.skillDetail;
  view.innerHTML = "";
  if (!detail) return;
  const skill = detail.skill;
  const readiness = deriveReadiness(skill);

  view.innerHTML = `
    <div class="detail-layout">
      <div class="panel">
        <div class="detail-hero">
        <div>
          <p class="eyebrow">${skill.category}</p>
          <h3>${skill.name}</h3>
        </div>
          <div class="admin-actions">
            <span class="${readinessClass(readiness.code)}">${readiness.label}</span>
            <span class="pill">${displayStatus(skill.status)}</span>
          </div>
        </div>
        <p>${skill.description}</p>
        <div class="score-stack">
          <div class="score-ring" style="--score:${skill.overallTrust}"><strong>${skill.overallTrust}</strong></div>
          <div class="score-list">
            <div><span>${tr().skillRecommendation}</span><span>${skill.recommendationScore}/100</span></div>
            <div><span>${tr().skillCapabilityMatch}</span><span>${skill.matchScore}/100</span></div>
            <div><span>${tr().skillOverallTrust}</span><span>${skill.overallTrust}/100</span></div>
            <div><span>${tr().skillUserRating}</span><span>${skill.userRatingAvg.toFixed(1)}/5 (${skill.normalizedUserRating}/100)</span></div>
            <div><span>${tr().skillAgentRating}</span><span>${skill.agentScore}/100</span></div>
            <div><span>${tr().skillPricePerCall}</span><span>${currency(skill.pricePerCall)}</span></div>
          </div>
        </div>
        <article class="panel">
          <div class="section-title"><h3>${tr().skillRecommendationWhy}</h3><span class="pill">${tr().marketplaceRecommendation}</span></div>
          <p>${displayRecommendationSummary(skill.recommendationSummary)}</p>
          <div class="inline-stat"><span>${tr().skillReadiness}</span><strong>${readiness.label}</strong></div>
          <div class="inline-stat"><span>${state.language === "zh" ? "\u666e\u901a\u7528\u6237\u89c6\u89d2" : "First-time user view"}</span><strong>${readiness.reason}</strong></div>
          <div class="inline-stat"><span>${tr().skillProvider}</span><strong>${skill.providerName || skill.submittedBy}</strong></div>
          <div class="inline-stat"><span>${tr().skillOperatingSystem}</span><strong>${skill.operatingSystem || "--"}</strong></div>
          <div class="inline-stat"><span>${tr().skillSource}</span><strong>${skill.source || "--"}</strong></div>
          <div class="inline-stat"><span>${tr().skillDocumentation}</span><strong>${skill.apiDocsUrl ? `<a href="${skill.apiDocsUrl}" target="_blank">${skill.apiDocsUrl}</a>` : "--"}</strong></div>
          <div class="inline-stat"><span>${tr().skillAuthRequirement}</span><strong>${skill.authRequirement}</strong></div>
        </article>
        <div class="two-grid">
          <article class="panel">
            <div class="section-title"><h3>${tr().skillUserRating}</h3><span class="pill">${skill.userRatingCount} ${tr().skillReviews}</span></div>
            <div class="inline-stat"><span>${tr().skillAverageScore}</span><strong>${skill.userRatingAvg.toFixed(1)}/5</strong></div>
            <div class="inline-stat"><span>${tr().skillNormalizedScore}</span><strong>${skill.normalizedUserRating}/100</strong></div>
            <div class="inline-stat"><span>${tr().skillIntent}</span><strong>${tr().skillHumanUsefulness}</strong></div>
          </article>
          <article class="panel">
            <div class="section-title"><h3>${tr().skillAgentRating}</h3><span class="pill">${tr().dashboardAutoEvaluated}</span></div>
            <div class="inline-stat"><span>${tr().skillSuccessRate}</span><strong>${skill.successRate}%</strong></div>
            <div class="inline-stat"><span>${tr().skillLatencyP95}</span><strong>${skill.latencyP95} ms</strong></div>
            <div class="inline-stat"><span>${tr().skillCostEfficiency}</span><strong>${skill.costEfficiency}/100</strong></div>
          </article>
        </div>
        <article class="panel" style="margin-top:18px;">
          <div class="section-title"><h3>${tr().skillCallThisDirectly}</h3><span class="pill">${tr().marketplaceInvocation}</span></div>
          <p>${skill.invocationMethod}</p>
          <div class="section-title"><h3>${tr().skillCallExample}</h3><span class="pill">JSON</span></div>
          <pre class="mono-block">${escapeHtml(skill.callExample)}</pre>
        </article>
      </div>
      <div class="panel">
        <div class="section-title"><h3>${tr().skillSubmitFeedback}</h3><span class="pill">${tr().skillManualReview}</span></div>
        <form id="review-form" class="review-form">
          <label for="review-author">${tr().skillYourName}</label>
          <input id="review-author" value="${currentUser()?.name ?? ""}" ${currentUser() ? "disabled" : ""} placeholder="${state.language === "zh" ? "\u63a7\u5236\u53f0\u7528\u6237" : "Console User"}" />
          <label>${tr().skillStarRating}</label>
          <div class="stars" id="stars"></div>
          <label for="review-comment">${tr().skillShortReview}</label>
          <textarea id="review-comment" rows="5" placeholder="${tr().skillReviewPlaceholder}"></textarea>
          <button class="primary-btn" type="submit">${tr().skillSaveRating}</button>
        </form>
      </div>
    </div>
    <div class="panel" style="margin-top:18px;">
      <div class="section-title"><h3>${tr().skillRecentReviews}</h3><span class="pill">${tr().skillHumanVoice}</span></div>
      <div class="review-list" id="review-list"></div>
    </div>
  `;

  const stars = document.querySelector("#stars");
  const reviewList = document.querySelector("#review-list");
  state.selectedRating = 0;

  for (let i = 1; i <= 5; i += 1) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "star";
    button.textContent = "\u2605";
    button.addEventListener("click", () => {
      state.selectedRating = i;
      [...stars.children].forEach((child, index) => child.classList.toggle("active", index < i));
    });
    stars.appendChild(button);
  }

  detail.reviews.forEach((review) => {
    const card = document.createElement("article");
    card.className = "review-card";
    card.innerHTML = `
      <div class="row-between">
        <strong>${review.author}</strong>
        <small>${review.timestamp}</small>
      </div>
      <p>${"\u2605".repeat(review.rating)}${"\u2606".repeat(5 - review.rating)}</p>
      <p>${review.comment}</p>
    `;
    reviewList.appendChild(card);
  });

  document.querySelector("#review-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.selectedRating) {
      showToast(tr().skillChooseStar);
      return;
    }
    if (!currentUser()) {
      showLoginModal();
      return;
    }
    const author = currentUser()?.name || document.querySelector("#review-author").value.trim() || (state.language === "zh" ? "\u63a7\u5236\u53f0\u7528\u6237" : "Console User");
    const comment = document.querySelector("#review-comment").value.trim();

    await api(`/skills/${skill.id}/reviews`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ author, rating: state.selectedRating, comment })
    });

    showToast(tr().skillSaved);
    await refreshData(true);
  });
}

function renderProfile() {
  const view = document.querySelector("#profile-view");
  view.innerHTML = "";
  const profile = state.userProfile;
  const user = currentUser();
  if (!user) {
    view.innerHTML = `<article class="panel"><p>${tr().loginCopy}</p></article>`;
    return;
  }
  if (!profile) {
    view.innerHTML = `<article class="panel"><p class="helper-text">Loading...</p></article>`;
    return;
  }

  const submittedSkills = Array.isArray(profile.submittedSkills) ? profile.submittedSkills : [];
  const submittedReviews = Array.isArray(profile.submittedReviews) ? profile.submittedReviews : [];

  view.innerHTML = `
    <div class="two-grid">
      <article class="panel">
        <div class="section-title"><h3>${tr().profileTitle}</h3><span class="pill">${displayRole(user.role)}</span></div>
        <div class="inline-stat"><span>${tr().profileMemberSince}</span><strong>${user.name}</strong></div>
        <div class="inline-stat"><span>${tr().profileEmail}</span><strong>${user.email || "--"}</strong></div>
        <div class="inline-stat"><span>${tr().role}</span><strong>${displayRole(user.role)}</strong></div>
        <div class="inline-stat"><span>${tr().profileSubmittedSkills}</span><strong>${submittedSkills.length}</strong></div>
        <div class="inline-stat"><span>${tr().profileReviewCount}</span><strong>${submittedReviews.length}</strong></div>
      </article>
      <article class="panel">
        <div class="section-title"><h3>${tr().profileSubmittedSkills}</h3><span class="pill">${submittedSkills.length}</span></div>
        <div id="profile-skill-list" class="admin-list"></div>
      </article>
    </div>
    <article class="panel" style="margin-top:18px;">
      <div class="section-title"><h3>${tr().profileSubmittedReviews}</h3><span class="pill">${submittedReviews.length}</span></div>
      <div id="profile-review-list" class="review-list"></div>
    </article>
  `;

  const skillList = view.querySelector("#profile-skill-list");
  if (!submittedSkills.length) {
    skillList.innerHTML = `<p class="helper-text">${tr().profileNoSkills}</p>`;
  } else {
    submittedSkills.forEach((skill) => {
      const card = document.createElement("article");
      card.className = "review-card";
      card.innerHTML = `
        <div class="row-between">
          <strong>${skill.name}</strong>
          <span class="pill">${displayStatus(skill.approvalStatus)}</span>
        </div>
        <p>${skill.description}</p>
        <small>${tr().profileSkillStatus}: ${displayStatus(skill.status)}</small>
      `;
      skillList.appendChild(card);
    });
  }

  const reviewList = view.querySelector("#profile-review-list");
  if (!submittedReviews.length) {
    reviewList.innerHTML = `<p class="helper-text">${tr().profileNoReviews}</p>`;
  } else {
    submittedReviews.forEach((review) => {
      const card = document.createElement("article");
      card.className = "review-card";
      card.innerHTML = `
        <div class="row-between">
          <strong>${tr().profileReviewFor}: ${review.skillName}</strong>
          <small>${review.timestamp}</small>
        </div>
        <p>${"\u2605".repeat(review.rating)}${"\u2606".repeat(5 - review.rating)}</p>
        <p>${review.comment}</p>
      `;
      reviewList.appendChild(card);
    });
  }
}

function renderAdmin() {
  const view = document.querySelector("#admin-view");
  view.innerHTML = "";

  if (!isAdmin()) {
    const panel = document.createElement("article");
    panel.className = "panel";
    panel.innerHTML = `<p>${tr().adminNeedRole}</p>`;
    view.appendChild(panel);
    return;
  }

  const manageableSkills = [...state.pendingSkills, ...state.skills.filter((skill) => !state.pendingSkills.some((pending) => pending.id === skill.id))];
  const selected = manageableSkills.find((skill) => skill.id === state.adminSelectedSkillId) ?? manageableSkills[0] ?? null;
  if (selected && !state.adminSelectedSkillId) {
    state.adminSelectedSkillId = selected.id;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "admin-grid";
  wrapper.innerHTML = `
    <article class="panel">
      <div class="section-title"><h3>${tr().adminPendingTitle}</h3><span class="pill">${tr().adminOnly}</span></div>
      <div class="admin-list" id="admin-pending-list"></div>
    </article>
    <article class="panel">
      <div class="section-title"><h3>${tr().adminSelectedTitle}</h3><span class="pill">${displayStatus(selected?.approvalStatus || "PENDING")}</span></div>
      <div id="admin-editor"></div>
    </article>
  `;
  view.appendChild(wrapper);

  const list = wrapper.querySelector("#admin-pending-list");
  if (!manageableSkills.length) {
    list.innerHTML = `<p class="helper-text">${tr().adminEmpty}</p>`;
  } else {
    manageableSkills.forEach((skill) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = `admin-item ${skill.id === state.adminSelectedSkillId ? "active" : ""}`;
      item.innerHTML = `<strong>${skill.name}</strong><div class="helper-text">${skill.category} 闂?${tr().adminSubmittedBy}: ${skill.submittedBy}</div><div class="helper-text">${tr().adminApprovalStatus}: ${displayStatus(skill.approvalStatus)}</div><div class="helper-text">${tr().adminFunctions}: ${skill.functions.join(", ")}</div>`;
      item.addEventListener("click", () => {
        state.adminSelectedSkillId = skill.id;
        renderAdmin();
      });
      list.appendChild(item);
    });
  }

  const editor = wrapper.querySelector("#admin-editor");
  if (!selected) {
    editor.innerHTML = `<p class="helper-text">${tr().adminPick}</p>`;
    return;
  }

  editor.innerHTML = `
    <form id="admin-skill-form" class="form-grid">
      <label>${tr().adminName}<input name="name" value="${selected.name}" /></label>
      <label>${tr().adminCategory}<input name="category" value="${selected.category}" /></label>
      <label>${tr().adminDescription}<textarea name="description" rows="4">${selected.description}</textarea></label>
      <label>${tr().adminFunctions}<input name="functions" value="${selected.functions.join(", ")}" /></label>
      <label>${tr().adminInvocationMethod}<input name="invocationMethod" value="${selected.invocationMethod}" /></label>
      <div class="two-grid">
        <label>${tr().skillSource}<input name="source" value="${selected.source || ""}" /></label>
        <label>${tr().skillProvider}<input name="sourceAuthor" value="${selected.sourceAuthor || ""}" /></label>
      </div>
      <div class="two-grid">
        <label>${tr().skillDocumentation}<input name="sourceUrl" value="${selected.sourceUrl || ""}" /></label>
        <label>License<input name="license" value="${selected.license || ""}" /></label>
      </div>
      <label>${tr().skillOperatingSystem}<input name="operatingSystem" value="${selected.operatingSystem || ""}" /></label>
      <div class="two-grid">
        <label>${tr().adminPrice}<input name="pricePerCall" type="number" step="0.01" value="${selected.pricePerCall}" /></label>
        <label>${tr().adminStatus}<input name="status" value="${selected.status}" /></label>
      </div>
      <div class="two-grid">
        <label>${tr().adminApprovalStatus}<input name="approvalStatus" value="${selected.approvalStatus}" /></label>
        <label>${tr().adminSubmittedBy}<input name="submittedBy" value="${selected.submittedBy}" disabled /></label>
      </div>
      <div class="two-grid">
        <label>${tr().adminSuccessRate}<input name="successRate" type="number" value="${selected.successRate}" /></label>
        <label>${tr().adminLatencyP95}<input name="latencyP95" type="number" value="${selected.latencyP95}" /></label>
      </div>
      <div class="two-grid">
        <label>${tr().adminCostEfficiency}<input name="costEfficiency" type="number" value="${selected.costEfficiency}" /></label>
        <label>${tr().adminRecentCalls}<input name="recentCalls" type="number" value="${selected.recentCalls}" /></label>
      </div>
      <div class="two-grid">
        <label>${tr().adminUserRatingAvg}<input name="userRatingAvg" type="number" step="0.1" value="${selected.userRatingAvg}" /></label>
        <label>${tr().adminUserRatingCount}<input name="userRatingCount" type="number" value="${selected.userRatingCount}" /></label>
      </div>
      <div class="admin-actions">
        <button class="primary-btn" type="button" id="admin-approve-btn">${tr().adminApprove}</button>
        <button class="secondary-btn" type="submit">${tr().adminSave}</button>
        <button class="danger-btn" type="button" id="admin-delete-btn">${tr().adminDelete}</button>
      </div>
    </form>
  `;

  const form = editor.querySelector("#admin-skill-form");
  editor.querySelector("#admin-approve-btn").addEventListener("click", async () => {
    await api(`/admin/skills/${selected.id}/approve`, {
      method: "POST",
      headers: authHeaders()
    });
    showToast(tr().adminApproved);
    await refreshData(false);
  });
  editor.querySelector("#admin-delete-btn").addEventListener("click", async () => {
    await api(`/admin/skills/${selected.id}`, {
      method: "DELETE",
      headers: authHeaders()
    });
    state.adminSelectedSkillId = null;
    showToast(tr().adminDeleted);
    await refreshData(false);
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const payload = {
      name: data.get("name"),
      category: data.get("category"),
      description: data.get("description"),
      pricePerCall: Number(data.get("pricePerCall")),
      status: data.get("status"),
      approvalStatus: data.get("approvalStatus"),
      successRate: Number(data.get("successRate")),
      latencyP95: Number(data.get("latencyP95")),
      costEfficiency: Number(data.get("costEfficiency")),
      recentCalls: Number(data.get("recentCalls")),
      userRatingAvg: Number(data.get("userRatingAvg")),
      userRatingCount: Number(data.get("userRatingCount")),
      functions: String(data.get("functions")).split(",").map((item) => item.trim()).filter(Boolean),
      invocationMethod: data.get("invocationMethod"),
      source: data.get("source"),
      sourceUrl: data.get("sourceUrl"),
      sourceAuthor: data.get("sourceAuthor"),
      license: data.get("license"),
      operatingSystem: data.get("operatingSystem")
    };
    await api(`/admin/skills/${selected.id}`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    showToast(tr().adminSaved);
    await refreshData(false);
  });
}

async function loadSkillDetail() {
  if (!state.selectedSkillId && state.skills.length) {
    state.selectedSkillId = state.skills[0].id;
  }
  if (!state.selectedSkillId) return;
  state.skillDetail = await api(`/skills/${state.selectedSkillId}`);
  renderSkillDetail();
}

function rerenderViews() {
  updateLanguageUi();
  renderNavigation();
  renderSessionControls();
  renderLoginModal();
  renderWelcome();
  renderTutorial();
  renderDashboard();
  renderMarketplace();
  renderSkillDetail();
  renderProfile();
  renderAdmin();
  if (state.dashboard) {
    platformTrust.textContent = `${state.dashboard.averageTrust}/100`;
  }
  setView(state.selectedView);
}

async function refreshData(alsoReloadSkill) {
  const skillPath = `/skills?q=${encodeURIComponent(state.skillsPage.q)}&function=${encodeURIComponent(state.skillsPage.functionName)}&readiness=${encodeURIComponent(state.skillsPage.readiness)}&hideTemplates=${state.skillsPage.hideTemplates}&page=${state.skillsPage.page}&pageSize=${state.skillsPage.pageSize}`;
  const baseRequests = [
    api(""),
    api("/agent-guide"),
    api("/dashboard"),
    api(skillPath)
  ];
  const userProfileRequest = state.authToken
    ? api("/users/me", { headers: authHeaders() }).catch((error) => {
        if (error.status === 401) {
          clearAuthState();
          return null;
        }
        throw error;
      })
    : Promise.resolve(null);

  const [welcome, agentGuide, dashboard, skillsResponse, userProfile] = await Promise.all([
    ...baseRequests,
    userProfileRequest
  ]);

  state.welcome = welcome;
  state.agentGuide = agentGuide;
  state.dashboard = dashboard;
  state.skills = Array.isArray(skillsResponse) ? skillsResponse : (skillsResponse.items || []);
  state.skillsPage.totalItems = skillsResponse.totalItems ?? state.skills.length;
  state.skillsPage.totalPages = skillsResponse.totalPages ?? 1;
  const maxValidPage = Math.max((state.skillsPage.totalPages || 1) - 1, 0);
  if (state.skillsPage.page > maxValidPage) {
    state.skillsPage.page = maxValidPage;
    await refreshData(alsoReloadSkill);
    return;
  }
  state.userProfile = userProfile;
  if (userProfile?.user) {
    state.currentUser = userProfile.user;
  }
  const pendingSkillsPromise = isAdmin()
    ? api("/admin/skills/pending", { headers: authHeaders() }).catch((error) => {
        if (error.status === 401 || error.status === 403) {
          return [];
        }
        throw error;
      })
    : Promise.resolve([]);

  if (alsoReloadSkill || (state.selectedView === "skill" && (state.selectedSkillId || state.skills.length))) {
    await loadSkillDetail();
  }
  rerenderViews();
  state.pendingSkills = await pendingSkillsPromise;
  rerenderViews();
}

function initNavigation() {
  primaryNav.addEventListener("click", async (event) => {
    const button = event.target.closest(".nav-link");
    if (!button) return;
    if (button.dataset.view === "skill" && !state.skillDetail) {
        await loadSkillDetail();
    }
    setView(button.dataset.view);
  });
}

function initLanguageSwitcher() {
  languageSelect.value = state.language;
  languageSelect.addEventListener("change", () => {
    state.language = languageSelect.value;
    rerenderViews();
  });
}

function initAuthModeTabs() {
  authModeTabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-auth-mode]");
    if (!button) return;
    state.authMode = button.dataset.authMode;
    clearAuthFeedback();
    renderLoginModal();
    updateLanguageUi();
  });
}

function initLoginForm() {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAuthFeedback();
    const formData = new FormData(loginForm);
    const name = String(formData.get("name") || "").trim();
    const email = String(formData.get("username") || "").trim();
    const password = String(formData.get("password") || "");
    const isRegister = state.authMode === "register";
    try {
      const path = isRegister ? "/auth/register" : "/auth/login";
      const payload = isRegister
        ? { name, email, password }
        : { email, password };
      const response = await api(path, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      signIn(response.token, response.user, false);
      loginForm.reset();
      state.authMode = "login";
      const successMessage = isRegister ? tr().registerSuccess : tr().loginSuccess;
      setAuthFeedback(successMessage, "success");
      await refreshData(true);
      setBanner(withApiBase(successMessage), "success");
      window.setTimeout(() => {
        clearAuthFeedback();
        hideLoginModal();
      }, 900);
    } catch (error) {
      const failureCopy = isRegister ? tr().registerFailed : tr().loginFailed;
      const failureMessage = failureCopy.replace("{error}", error.message);
      setAuthFeedback(failureMessage, "error");
      setBanner(withApiBase(failureMessage), "error");
      showLoginModal();
    }
  });
}

async function init() {
  initNavigation();
  initLanguageSwitcher();
  initAuthModeTabs();
  initLoginForm();
  updateLanguageUi();
  setView("welcome");
  rerenderViews();
  if (!state.authToken) {
    showLoginModal();
  }
  try {
    clearBanner();
    await refreshData(false);
    if (currentUser()) {
      setBanner(withApiBase(tr().connected), "success");
    } else {
      showLoginModal();
    }
  } catch (error) {
    setBanner(withApiBase(tr().failed.replace("{error}", error.message)), "error");
  }
}

init();

