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
} from "lucide-react";
import { channelsApi, jobsApi, exportApi } from "@/lib/api";

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

  const { data: channel, isLoading: channelLoading } = useQuery({
    queryKey: ["channel", channelId],
    queryFn: async () => {
      const response = await channelsApi.getChannels();
      return response.channels?.find((c: { id: string }) => c.id === channelId);
    },
  });

  const { data: messagesData, isLoading: messagesLoading } = useQuery({
    queryKey: ["messages", channelId, page, searchQuery],
    queryFn: () => channelsApi.getMessages(channelId, page, 50),
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
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Messages</CardTitle>
              <CardDescription>{totalMessages} total messages</CardDescription>
            </div>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search messages..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                className="pl-9"
              />
            </div>
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
