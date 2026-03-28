import * as XLSX from "xlsx";
import path from "path";
import fs from "fs";
import type { Creator, Post, DashboardStats, CreatorStats } from "./types";

// ── Paths ──────────────────────────────────────────────────────────────────────

const DATA_DIR = path.resolve(process.cwd(), "data");

function readSheet(filename: string): unknown[][] {
  const filePath = path.join(DATA_DIR, filename);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Data file not found: ${filePath}`);
  }
  // Read as buffer and pass to XLSX.read to avoid Turbopack's readFile sandbox
  const buffer = fs.readFileSync(filePath);
  const workbook = XLSX.read(buffer, { type: "buffer", raw: false });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  // header: 1 returns array-of-arrays; raw: false coerces dates to strings
  return XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false, defval: null }) as unknown[][];
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function str(v: unknown): string | null {
  if (v === null || v === undefined || v === "") return null;
  return String(v).trim();
}

function num(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null;
  const n = typeof v === "number" ? v : parseFloat(String(v).replace(/,/g, ""));
  return isNaN(n) ? null : n;
}

function bool(v: unknown): boolean | null {
  if (v === null || v === undefined || v === "") return null;
  const s = String(v).trim().toUpperCase();
  if (s === "Y" || s === "YES" || s === "TRUE") return true;
  if (s === "N" || s === "NO" || s === "FALSE") return false;
  return null;
}

// ── getCreators ────────────────────────────────────────────────────────────────

export function getCreators(): Creator[] {
  const rows = readSheet("DB1_Creator_Profiles.xlsx");

  // Row 0 = headers, Row 1 = descriptions, Row 2+ = data
  const dataRows = rows.slice(2);

  return dataRows
    .filter((row) => row[0] !== null)
    .map((row) => ({
      name:                str(row[0])!,
      bio:                 str(row[1]),
      followerCountRange:  str(row[2]),
      followerCount:       num(row[3]),
      location:            str(row[4]),
      firmAffiliation:     str(row[5]),
      dateAdded:           str(row[6]),
      overallNotes:        str(row[7]),
      primaryRole:         str(row[8]),
      contentNiche:        str(row[9]),
      growthStage:         str(row[10]),
      geographyFocus:      str(row[11]),
      crossPlatformCount:  num(row[12]),
      topVoiceStyle:       str(row[13]),
      credibility:         num(row[14]),
      collaborationPotential: str(row[15]),
      postingFrequency:    str(row[16]),
      connectionStatus:    str(row[17]),
      haveInteracted:      str(row[18]),
      haveDMed:            str(row[19]),
      relationshipNotes:   str(row[20]),
      linkedinUrl:         str(row[21]),
    }));
}

// ── getPosts ───────────────────────────────────────────────────────────────────

export function getPosts(): Post[] {
  const rows = readSheet("DB2_Post_Analysis.xlsx");

  // Row 0 = headers, Row 1 = descriptions, Row 2+ = data
  const dataRows = rows.slice(2);

  return dataRows
    .filter((row) => row[0] !== null)
    .map((row) => ({
      name:             str(row[0])!,
      postDate:         str(row[1]),
      postFormat:       str(row[2]),
      primaryTopic:     str(row[3]),
      topicSubject:     str(row[4]),
      containsData:     bool(row[5]),
      relevance:        str(row[6]),
      hook:             str(row[7]),
      hookStyle:        str(row[8]),
      hookStrength:     num(row[9]),
      tone:             str(row[10]),
      containsCTA:      bool(row[11]),
      ctaText:          str(row[12]),
      likes:            num(row[13]),
      comments:         num(row[14]),
      reposts:          num(row[15]),
      shareability:     num(row[16]),
      engagementScore:  num(row[17]),
      postPerformance:  str(row[18]),
      topicPopularity:  str(row[19]),
      postFrequency:    str(row[20]),
      postUrl:          str(row[21]),
      postWorkAnalysis: str(row[22]),
    }));
}

// ── getCreatorFollowerMap ──────────────────────────────────────────────────────

export function getCreatorFollowerMap(): Record<string, number> {
  return Object.fromEntries(
    getCreators()
      .filter((c) => c.followerCount !== null)
      .map((c) => [c.name, c.followerCount as number])
  );
}

// ── getCreatorStatsMap ─────────────────────────────────────────────────────────

export function getCreatorStatsMap(): Record<string, CreatorStats> {
  const creators = getCreators();
  const posts = getPosts();

  const creatorByName = new Map(creators.map((c) => [c.name, c]));
  const postsByName = new Map<string, Post[]>();
  for (const post of posts) {
    const arr = postsByName.get(post.name) ?? [];
    arr.push(post);
    postsByName.set(post.name, arr);
  }

  const result: Record<string, CreatorStats> = {};
  for (const creator of creators) {
    const creatorPosts = postsByName.get(creator.name) ?? [];
    const fc = creator.followerCount ?? 0;
    const totals = creatorPosts.map(
      (p) => (p.likes ?? 0) + (p.comments ?? 0) + (p.reposts ?? 0)
    );
    const rates = totals.map((t) => (fc > 0 ? t / fc : 0));

    result[creator.name] = {
      engagementRate:
        rates.length > 0 ? rates.reduce((a, b) => a + b, 0) / rates.length : 0,
      avgEngagement:
        totals.length > 0
          ? Math.round(totals.reduce((a, b) => a + b, 0) / totals.length)
          : 0,
      postCount: creatorPosts.length,
    };
  }

  // Silence unused import warning
  void creatorByName;

  return result;
}

// ── getStats ───────────────────────────────────────────────────────────────────

export function getStats(): DashboardStats {
  const creators = getCreators();
  const posts = getPosts();

  // Avg engagement rate: (likes + comments + reposts) / followerCount per post
  // Join post to creator to get follower count
  const creatorMap = new Map(creators.map((c) => [c.name, c]));
  const engagementRates: number[] = [];
  let viralPostCount = 0;

  for (const post of posts) {
    const creator = creatorMap.get(post.name);
    const fc = creator?.followerCount ?? 0;
    const total = (post.likes ?? 0) + (post.comments ?? 0) + (post.reposts ?? 0);
    if (fc > 0) {
      const rate = total / fc;
      engagementRates.push(rate);
    }
    if (post.postPerformance === "Above Average Engagement") {
      viralPostCount++;
    }
  }

  const avgEngagementRate =
    engagementRates.length > 0
      ? engagementRates.reduce((a, b) => a + b, 0) / engagementRates.length
      : 0;

  const credScores = creators.map((c) => c.credibility).filter((c): c is number => c !== null);
  const avgCredibility =
    credScores.length > 0 ? credScores.reduce((a, b) => a + b, 0) / credScores.length : 0;

  // Top topics
  const topicCounts = new Map<string, number>();
  for (const post of posts) {
    if (post.primaryTopic) {
      topicCounts.set(post.primaryTopic, (topicCounts.get(post.primaryTopic) ?? 0) + 1);
    }
  }
  const topTopics = [...topicCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([topic, count]) => ({ topic, count }));

  // Posts by format
  const formatCounts = new Map<string, number>();
  for (const post of posts) {
    const fmt = post.postFormat ?? "Unknown";
    formatCounts.set(fmt, (formatCounts.get(fmt) ?? 0) + 1);
  }
  const postsByFormat = [...formatCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([format, count]) => ({ format, count }));

  // Creators by role
  const roleCounts = new Map<string, number>();
  for (const creator of creators) {
    const role = creator.primaryRole ?? "Unknown";
    roleCounts.set(role, (roleCounts.get(role) ?? 0) + 1);
  }
  const creatorsByRole = [...roleCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([role, count]) => ({ role, count }));

  return {
    totalCreators: creators.length,
    totalPosts: posts.length,
    avgEngagementRate,
    viralPostCount,
    avgCredibility,
    topTopics,
    postsByFormat,
    creatorsByRole,
  };
}
