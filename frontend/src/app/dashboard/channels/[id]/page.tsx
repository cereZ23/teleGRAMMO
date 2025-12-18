"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  ArrowLeft,
  Search,
  Play,
  Download,
  MessageSquare,
  Image,
  User,
  Calendar,
  Eye,
  Share2,
  Loader2,
  RefreshCw,
  Clock,
  Settings,
  Filter,
  X,
} from "lucide-react";
import { channelsApi, jobsApi, exportApi, mediaApi, telegramApi } from "@/lib/api";

interface Message {
  id: string;
  telegram_message_id: number;
  date: string;
  sender_id: number | null;
  first_name: string | null;
  last_name: string | null;
  username: string | null;
  message_text: string | null;
  media_type: string | null;
  views: number | null;
  forwards: number | null;
}

export default function ChannelDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const channelId = params.id as string;

  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [mediaTypeFilter, setMediaTypeFilter] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  const hasActiveFilters = mediaTypeFilter || dateFrom || dateTo || searchQuery;

  const clearFilters = () => {
    setSearchQuery("");
    setMediaTypeFilter("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  };

  const { data: channel, isLoading: channelLoading } = useQuery({
    queryKey: ["channel", channelId],
    queryFn: async () => {
      const response = await channelsApi.getChannels();
      return response.channels?.find((c: { id: string }) => c.id === channelId);
    },
  });

  const { data: messagesData, isLoading: messagesLoading } = useQuery({
    queryKey: ["messages", channelId, page, searchQuery, mediaTypeFilter, dateFrom, dateTo],
    queryFn: () => channelsApi.getMessages(channelId, page, 50, {
      search: searchQuery || undefined,
      mediaType: mediaTypeFilter || undefined,
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
    }),
    enabled: !!channelId,
  });

  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: jobsApi.getJobs,
    refetchInterval: 5000,
  });

  const startScrapeMutation = useMutation({
    mutationFn: () => jobsApi.startScrape(channelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  // Schedule state
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [scheduleInterval, setScheduleInterval] = useState<number>(24);

  const { data: schedule, isLoading: scheduleLoading } = useQuery({
    queryKey: ["schedule", channelId],
    queryFn: () => channelsApi.getSchedule(channelId),
    enabled: !!channelId,
  });

  const updateScheduleMutation = useMutation({
    mutationFn: ({ enabled, intervalHours }: { enabled: boolean; intervalHours?: number }) =>
      channelsApi.updateSchedule(channelId, enabled, intervalHours),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule", channelId] });
      setShowScheduleDialog(false);
    },
  });

  const activeJob = jobs?.jobs?.find(
    (job: { channel_id: string; status: string }) =>
      job.channel_id === channelId &&
      (job.status === "running" || job.status === "pending")
  );

  const messages: Message[] = messagesData?.messages || [];
  const totalMessages = messagesData?.total || 0;
  const totalPages = Math.ceil(totalMessages / 50);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const getSenderName = (msg: Message) => {
    if (msg.first_name || msg.last_name) {
      return `${msg.first_name || ""} ${msg.last_name || ""}`.trim();
    }
    if (msg.username) return `@${msg.username}`;
    return "Unknown";
  };

  const [exporting, setExporting] = useState<"csv" | "json" | null>(null);
  const [downloadingMedia, setDownloadingMedia] = useState(false);

  // Get sessions for media download
  const { data: sessionsData } = useQuery({
    queryKey: ["sessions"],
    queryFn: telegramApi.getSessions,
  });

  const activeSession = sessionsData?.sessions?.find((s: { is_authenticated: boolean }) => s.is_authenticated);

  // Get media stats
  const { data: mediaStats, refetch: refetchMediaStats } = useQuery({
    queryKey: ["mediaStats", channelId],
    queryFn: () => mediaApi.getMediaStats(channelId),
    enabled: !!channelId,
  });

  const handleDownloadMedia = async () => {
    if (!activeSession) return;
    setDownloadingMedia(true);
    try {
      await mediaApi.startBatchDownload(channelId, activeSession.id, 20);
      setTimeout(() => refetchMediaStats(), 2000);
    } catch (error) {
      console.error("Failed to start media download:", error);
    } finally {
      setDownloadingMedia(false);
    }
  };

  const handleExportCSV = async () => {
    setExporting("csv");
    try {
      const response = await exportApi.downloadCSV(channelId);
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${channel?.username || channelId}_messages.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setExporting(null);
    }
  };

  const handleExportJSON = async () => {
    setExporting("json");
    try {
      const response = await exportApi.downloadJSON(channelId);
      const blob = new Blob([response.data], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${channel?.username || channelId}_messages.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setExporting(null);
    }
  };

  if (channelLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!channel) {
    return (
      <div className="py-8 text-center">
        <p>Channel not found</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>
          Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{channel.title}</h1>
          <p className="text-muted-foreground">@{channel.username}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExportCSV} disabled={exporting === "csv"}>
            {exporting === "csv" ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            CSV
          </Button>
          <Button variant="outline" onClick={handleExportJSON} disabled={exporting === "json"}>
            {exporting === "json" ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            JSON
          </Button>
          {activeJob ? (
            <Button disabled>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Scraping...
            </Button>
          ) : (
            <Button onClick={() => startScrapeMutation.mutate()}>
              <Play className="mr-2 h-4 w-4" />
              Start Scrape
            </Button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <span className="text-2xl font-bold">{channel.message_count || 0}</span>
            </div>
            <p className="text-xs text-muted-foreground">Messages</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Image className="h-4 w-4 text-muted-foreground" />
              <span className="text-2xl font-bold">{channel.media_count || 0}</span>
            </div>
            <p className="text-xs text-muted-foreground">Media Files</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold capitalize">{channel.channel_type}</div>
            <p className="text-xs text-muted-foreground">Type</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{channel.telegram_id}</div>
            <p className="text-xs text-muted-foreground">Telegram ID</p>
          </CardContent>
        </Card>
      </div>

      {/* Media Download */}
      {mediaStats && (mediaStats.by_status.pending > 0 || mediaStats.by_status.completed > 0) && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Image className="h-5 w-5" />
                <CardTitle>Media Downloads</CardTitle>
              </div>
              {mediaStats.by_status.pending > 0 && activeSession && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadMedia}
                  disabled={downloadingMedia}
                >
                  {downloadingMedia ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="mr-2 h-4 w-4" />
                  )}
                  Download Media
                </Button>
              )}
            </div>
            <CardDescription>
              {mediaStats.by_status.completed} downloaded, {mediaStats.by_status.pending} pending
              {mediaStats.by_status.failed > 0 && `, ${mediaStats.by_status.failed} failed`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-lg border p-3">
                <div className="text-2xl font-bold text-green-600">{mediaStats.by_status.completed}</div>
                <p className="text-xs text-muted-foreground">Completed</p>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-2xl font-bold text-yellow-600">{mediaStats.by_status.pending}</div>
                <p className="text-xs text-muted-foreground">Pending</p>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-2xl font-bold text-blue-600">{mediaStats.by_status.downloading}</div>
                <p className="text-xs text-muted-foreground">Downloading</p>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-2xl font-bold">
                  {mediaStats.total_downloaded_size
                    ? `${(mediaStats.total_downloaded_size / (1024 * 1024)).toFixed(1)} MB`
                    : "0 MB"}
                </div>
                <p className="text-xs text-muted-foreground">Total Size</p>
              </div>
            </div>
            {Object.keys(mediaStats.by_type || {}).length > 0 && (
              <div className="mt-4">
                <p className="mb-2 text-sm font-medium">Media Types</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(mediaStats.by_type).map(([type, count]) => (
                    <span key={type} className="rounded-full bg-muted px-3 py-1 text-sm">
                      {type}: {count as number}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Schedule Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              <CardTitle>Scheduled Scraping</CardTitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (schedule?.interval_hours) {
                  setScheduleInterval(schedule.interval_hours);
                }
                setShowScheduleDialog(!showScheduleDialog);
              }}
            >
              <Settings className="mr-2 h-4 w-4" />
              Configure
            </Button>
          </div>
          <CardDescription>
            {schedule?.enabled
              ? `Auto-scraping every ${schedule.interval_hours} hour${schedule.interval_hours > 1 ? "s" : ""}`
              : "Automatic scraping is disabled"}
          </CardDescription>
        </CardHeader>
        {showScheduleDialog && (
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium">Scrape Interval</label>
                <select
                  className="w-full rounded-md border p-2"
                  value={scheduleInterval}
                  onChange={(e) => setScheduleInterval(Number(e.target.value))}
                >
                  <option value={1}>Every hour</option>
                  <option value={6}>Every 6 hours</option>
                  <option value={12}>Every 12 hours</option>
                  <option value={24}>Every 24 hours (daily)</option>
                  <option value={168}>Every week</option>
                </select>
              </div>
              {schedule?.next_scheduled_at && schedule?.enabled && (
                <p className="text-sm text-muted-foreground">
                  Next scrape: {new Date(schedule.next_scheduled_at).toLocaleString()}
                </p>
              )}
              {schedule?.last_scheduled_at && (
                <p className="text-sm text-muted-foreground">
                  Last auto-scrape: {new Date(schedule.last_scheduled_at).toLocaleString()}
                </p>
              )}
              <div className="flex gap-2">
                {schedule?.enabled ? (
                  <Button
                    variant="destructive"
                    onClick={() => updateScheduleMutation.mutate({ enabled: false })}
                    disabled={updateScheduleMutation.isPending}
                  >
                    {updateScheduleMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : null}
                    Disable Auto-Scrape
                  </Button>
                ) : (
                  <Button
                    onClick={() => updateScheduleMutation.mutate({ enabled: true, intervalHours: scheduleInterval })}
                    disabled={updateScheduleMutation.isPending}
                  >
                    {updateScheduleMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Clock className="mr-2 h-4 w-4" />
                    )}
                    Enable Auto-Scrape
                  </Button>
                )}
                {schedule?.enabled && (
                  <Button
                    variant="outline"
                    onClick={() => updateScheduleMutation.mutate({ enabled: true, intervalHours: scheduleInterval })}
                    disabled={updateScheduleMutation.isPending}
                  >
                    Update Interval
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Active Job Progress */}
      {activeJob && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Scraping in Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <Progress value={activeJob.progress_percent} className="mb-2" />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{Math.round(activeJob.progress_percent)}% complete</span>
              <span>{activeJob.messages_processed} messages processed</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Messages */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Messages</CardTitle>
                <CardDescription>
                  {totalMessages} {hasActiveFilters ? "filtered" : "total"} messages
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Full-text search..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setPage(1);
                    }}
                    className="pl-9"
                  />
                </div>
                <Button
                  variant={showFilters ? "secondary" : "outline"}
                  size="icon"
                  onClick={() => setShowFilters(!showFilters)}
                >
                  <Filter className="h-4 w-4" />
                </Button>
                {hasActiveFilters && (
                  <Button variant="ghost" size="icon" onClick={clearFilters}>
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>

            {/* Filter Panel */}
            {showFilters && (
              <div className="flex flex-wrap items-end gap-4 rounded-lg border bg-muted/50 p-4">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-muted-foreground">Media Type</label>
                  <select
                    className="h-9 rounded-md border bg-background px-3 text-sm"
                    value={mediaTypeFilter}
                    onChange={(e) => {
                      setMediaTypeFilter(e.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="">All types</option>
                    <option value="photo">Photo</option>
                    <option value="video">Video</option>
                    <option value="document">Document</option>
                    <option value="audio">Audio</option>
                    <option value="voice">Voice</option>
                    <option value="sticker">Sticker</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-muted-foreground">Date From</label>
                  <Input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => {
                      setDateFrom(e.target.value);
                      setPage(1);
                    }}
                    className="h-9 w-40"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-muted-foreground">Date To</label>
                  <Input
                    type="date"
                    value={dateTo}
                    onChange={(e) => {
                      setDateTo(e.target.value);
                      setPage(1);
                    }}
                    className="h-9 w-40"
                  />
                </div>
                {hasActiveFilters && (
                  <Button variant="outline" size="sm" onClick={clearFilters}>
                    Clear Filters
                  </Button>
                )}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {messagesLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : messages.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              <p>No messages yet</p>
              <p className="text-sm">Start a scrape to collect messages</p>
            </div>
          ) : (
            <>
              <div className="space-y-3">
                {messages.map((msg) => (
                  <div key={msg.id} className="rounded-lg border p-4">
                    <div className="mb-2 flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{getSenderName(msg)}</span>
                        {msg.media_type && (
                          <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                            {msg.media_type}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        {msg.views && (
                          <span className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />
                            {msg.views.toLocaleString()}
                          </span>
                        )}
                        {msg.forwards && (
                          <span className="flex items-center gap-1">
                            <Share2 className="h-3 w-3" />
                            {msg.forwards.toLocaleString()}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(msg.date)}
                        </span>
                      </div>
                    </div>
                    {msg.message_text && (
                      <p className="whitespace-pre-wrap text-sm">{msg.message_text}</p>
                    )}
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-4 flex items-center justify-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
