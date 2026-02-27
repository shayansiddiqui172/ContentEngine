-- CreateEnum
CREATE TYPE "PrimaryRole" AS ENUM ('LP', 'FOUNDER', 'VC', 'OPERATOR', 'JOURNALIST', 'ADVISOR');

-- CreateEnum
CREATE TYPE "WatchStatus" AS ENUM ('ACTIVE_WATCH', 'PASSIVE', 'ARCHIVED');

-- CreateEnum
CREATE TYPE "ConnectionStatus" AS ENUM ('FIRST', 'SECOND', 'NOT_CONNECTED');

-- CreateEnum
CREATE TYPE "Format" AS ENUM ('TEXT_ONLY', 'CAROUSEL', 'VIDEO', 'POLL', 'ARTICLE', 'RESHARE');

-- CreateEnum
CREATE TYPE "Angle" AS ENUM ('CONTRARIAN', 'EDUCATIONAL', 'INSPIRATIONAL', 'TACTICAL', 'OPINION', 'NARRATIVE');

-- CreateTable
CREATE TABLE "Creator" (
    "id" TEXT NOT NULL,
    "fullName" TEXT NOT NULL,
    "linkedinUrl" TEXT NOT NULL,
    "handle" TEXT,
    "location" TEXT,
    "firmOrCompany" TEXT,
    "bio" TEXT,
    "primaryRole" "PrimaryRole" NOT NULL,
    "contentNiche" TEXT,
    "stageFocus" TEXT,
    "geographyFocus" TEXT,
    "tags" TEXT[],
    "followerCount" INTEGER,
    "followerCountUpdatedAt" TIMESTAMP(3),
    "estimatedEngagementRate" DOUBLE PRECISION,
    "hasTwitter" BOOLEAN NOT NULL DEFAULT false,
    "twitterUrl" TEXT,
    "hasSubstack" BOOLEAN NOT NULL DEFAULT false,
    "substackUrl" TEXT,
    "hasYoutube" BOOLEAN NOT NULL DEFAULT false,
    "youtubeUrl" TEXT,
    "hasPodcast" BOOLEAN NOT NULL DEFAULT false,
    "podcastUrl" TEXT,
    "voiceStyle" TEXT,
    "credibilityScore" INTEGER,
    "relevanceScore" INTEGER,
    "collaborationPotential" BOOLEAN NOT NULL DEFAULT false,
    "collaborationNotes" TEXT,
    "watchStatus" "WatchStatus" NOT NULL,
    "connectionStatus" "ConnectionStatus" NOT NULL,
    "hasInteractedWithContent" BOOLEAN NOT NULL DEFAULT false,
    "hasDMedOrMet" BOOLEAN NOT NULL DEFAULT false,
    "relationshipNotes" TEXT,
    "addedBy" TEXT,
    "source" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Creator_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Post" (
    "id" TEXT NOT NULL,
    "creatorId" TEXT NOT NULL,
    "postUrl" TEXT NOT NULL,
    "publishedAt" TIMESTAMP(3),
    "capturedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "format" "Format" NOT NULL,
    "primaryTopic" TEXT,
    "secondaryTopics" TEXT[],
    "containsData" BOOLEAN NOT NULL DEFAULT false,
    "containsCTA" BOOLEAN NOT NULL DEFAULT false,
    "ctaType" TEXT,
    "isOriginal" BOOLEAN NOT NULL DEFAULT true,
    "reactions" INTEGER NOT NULL DEFAULT 0,
    "comments" INTEGER NOT NULL DEFAULT 0,
    "reposts" INTEGER NOT NULL DEFAULT 0,
    "estimatedImpressions" INTEGER,
    "engagementRate" DOUBLE PRECISION,
    "viralFlag" BOOLEAN NOT NULL DEFAULT false,
    "hookStrength" INTEGER,
    "angle" "Angle" NOT NULL,
    "keyInsight" TEXT,
    "relevanceToStrategy" INTEGER,
    "swipeFileFlag" BOOLEAN NOT NULL DEFAULT false,
    "notes" TEXT,

    CONSTRAINT "Post_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Creator_linkedinUrl_key" ON "Creator"("linkedinUrl");

-- CreateIndex
CREATE UNIQUE INDEX "Post_postUrl_key" ON "Post"("postUrl");

-- AddForeignKey
ALTER TABLE "Post" ADD CONSTRAINT "Post_creatorId_fkey" FOREIGN KEY ("creatorId") REFERENCES "Creator"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
