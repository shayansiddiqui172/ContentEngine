// ── DB1: Creator Profiles ──────────────────────────────────────────────────────

export interface Creator {
  name: string;
  bio: string | null;
  followerCountRange: string | null;
  followerCount: number | null;
  location: string | null;
  firmAffiliation: string | null;
  dateAdded: string | null;
  overallNotes: string | null;
  primaryRole: "VC / Investor" | "Startup" | "AI" | "Ecosystem Partner" | "FOUNDER" | "VC" | "OPERATOR" | string | null;
  contentNiche: string | null;
  growthStage: "Established Creator" | "Emerging Creator" | string | null;
  geographyFocus: string | null;
  crossPlatformCount: number | null;
  topVoiceStyle: "Data Driven" | "Story Telling" | "Tactical" | "Contrarian" | string | null;
  credibility: number | null; // 1–5
  collaborationPotential: string | null;
  postingFrequency: "Daily" | "3-4/week" | "1-2/week" | "< a month" | string | null;
  connectionStatus: string | null;
  haveInteracted: string | null;
  haveDMed: string | null;
  relationshipNotes: string | null;
  linkedinUrl: string | null;
}

// ── DB2: Post Analysis ─────────────────────────────────────────────────────────

export interface Post {
  name: string;                    // creator name
  postDate: string | null;
  postFormat: "Short Text" | "Long Text" | "Long Text + Image" | "Image" | "Video" | string | null;
  primaryTopic: string | null;
  topicSubject: string | null;
  containsData: boolean | null;
  relevance: "Highly Relevant" | "Strongly Relevant" | "Moderately Relevant" | "Slightly Relevant" | string | null;
  hook: string | null;
  hookStyle: "Personal" | "Inspirational" | "Story Telling" | "Bold Statement" | "Question" | "Statistic" | "Tactical" | string | null;
  hookStrength: number | null;     // 1–5
  tone: "Personal" | "Educational" | "Inspirational" | "Contrarian" | "Tactical" | string | null;
  containsCTA: boolean | null;
  ctaText: string | null;
  likes: number | null;
  comments: number | null;
  reposts: number | null;
  shareability: number | null;     // 1–5
  engagementScore: number | null;  // 1–5
  postPerformance: "Above Average Engagement" | "Average Engagement" | "Below Average Engagement" | string | null;
  topicPopularity: string | null;
  postFrequency: string | null;
  postUrl: string | null;
  postWorkAnalysis: string | null;
}

// ── Per-creator computed stats (from posts) ────────────────────────────────────

export interface CreatorStats {
  engagementRate: number;   // avg (likes+comments+reposts) / followerCount per post
  avgEngagement: number;    // avg total interactions per post ("influence")
  postCount: number;
}

// ── Stats ──────────────────────────────────────────────────────────────────────

export interface DashboardStats {
  totalCreators: number;
  totalPosts: number;
  avgEngagementRate: number;       // as a percentage, e.g. 0.12 = 0.12%
  viralPostCount: number;
  avgCredibility: number;
  topTopics: { topic: string; count: number }[];
  postsByFormat: { format: string; count: number }[];
  creatorsByRole: { role: string; count: number }[];
}
