"use client";

import { useState } from "react";
import Link from "next/link";
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
  Folder,
  Plus,
  Trash2,
  Play,
  Search,
  MessageSquare,
  Image,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { channelsApi, jobsApi, telegramApi } from "@/lib/api";

interface Channel {
  id: string;
  telegram_id: number;
  username: string;
  title: string;
  channel_type: string;
  message_count?: number;
  media_count?: number;
  last_scraped_at?: string;
}

interface TelegramChannel {
  id: number;
  username: string;
  title: string;
  type: string;
}

export default function ChannelsPage() {
  const queryClient = useQueryClient();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  const { data: sessions } = useQuery({
    queryKey: ["telegram-sessions"],
    queryFn: telegramApi.getSessions,
  });

  const { data: channels, isLoading: channelsLoading } = useQuery({
    queryKey: ["channels"],
    queryFn: channelsApi.getChannels,
  });

  const { data: availableChannels, isLoading: availableLoading } = useQuery({
    queryKey: ["available-channels", selectedSessionId],
    queryFn: () => channelsApi.getAvailable(selectedSessionId!),
    enabled: !!selectedSessionId && showAddDialog,
  });

  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: jobsApi.getJobs,
    refetchInterval: 5000,
  });

  const addChannelMutation = useMutation({
    mutationFn: ({ sessionId, telegramId }: { sessionId: string; telegramId: number }) =>
      channelsApi.addChannel(sessionId, telegramId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
      setShowAddDialog(false);
    },
  });

  const removeChannelMutation = useMutation({
    mutationFn: (channelId: string) => channelsApi.removeChannel(channelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
    },
  });

  const startScrapeMutation = useMutation({
    mutationFn: (channelId: string) => jobsApi.startScrape(channelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const authenticatedSessions = sessions?.filter(
    (s: { is_authenticated: boolean }) => s.is_authenticated
  );

  const getChannelJob = (channelId: string) => {
    return jobs?.jobs?.find(
      (job: { channel_id: string; status: string }) =>
        job.channel_id === channelId &&
        (job.status === "running" || job.status === "pending")
    );
  };

  const filteredChannels = channels?.channels?.filter((channel: Channel) =>
    channel.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    channel.username?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Channels</h1>
          <p className="text-muted-foreground">
            Manage your tracked Telegram channels
          </p>
        </div>
        <Button
          onClick={() => {
            if (authenticatedSessions?.length > 0) {
              setSelectedSessionId(authenticatedSessions[0].id);
              setShowAddDialog(true);
            }
          }}
          disabled={!authenticatedSessions?.length}
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Channel
        </Button>
      </div>

      {/* Search */}
      {channels?.channels?.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search channels..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      )}

      {/* Add Channel Dialog */}
      {showAddDialog && (
        <Card>
          <CardHeader>
            <CardTitle>Add Channel</CardTitle>
            <CardDescription>
              Select a channel from your Telegram account to track
            </CardDescription>
          </CardHeader>
          <CardContent>
            {authenticatedSessions?.length > 1 && (
              <div className="mb-4">
                <label className="mb-2 block text-sm font-medium">
                  Select Session
                </label>
                <select
                  className="w-full rounded-md border p-2"
                  value={selectedSessionId || ""}
                  onChange={(e) => setSelectedSessionId(e.target.value)}
                >
                  {authenticatedSessions.map((session: { id: string; phone_number?: string; api_id: number }) => (
                    <option key={session.id} value={session.id}>
                      {session.phone_number || `Session ${session.api_id}`}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {availableLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="ml-2">Loading channels...</span>
              </div>
            ) : availableChannels?.length === 0 ? (
              <p className="py-4 text-center text-muted-foreground">
                No channels found in your Telegram account
              </p>
            ) : (
              <div className="max-h-96 space-y-2 overflow-y-auto">
                {availableChannels?.map((channel: TelegramChannel) => (
                  <div
                    key={channel.id}
                    className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted"
                  >
                    <div>
                      <p className="font-medium">{channel.title}</p>
                      <p className="text-sm text-muted-foreground">
                        @{channel.username} ({channel.type})
                      </p>
                    </div>
                    <Button
                      size="sm"
                      onClick={() =>
                        addChannelMutation.mutate({
                          sessionId: selectedSessionId!,
                          telegramId: channel.id,
                        })
                      }
                      disabled={addChannelMutation.isPending}
                    >
                      Add
                    </Button>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-4 flex justify-end">
              <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Channels List */}
      {channelsLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !channels?.channels?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Folder className="mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="mb-2 text-lg font-semibold">No Channels</h3>
            <p className="mb-4 text-center text-muted-foreground">
              {authenticatedSessions?.length
                ? "Add a channel to start scraping messages"
                : "Connect a Telegram session first to add channels"}
            </p>
            {authenticatedSessions?.length > 0 && (
              <Button
                onClick={() => {
                  setSelectedSessionId(authenticatedSessions[0].id);
                  setShowAddDialog(true);
                }}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Channel
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredChannels?.map((channel: Channel) => {
            const activeJob = getChannelJob(channel.id);
            return (
              <Card key={channel.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                  <Link
                    href={`/dashboard/channels/${channel.id}`}
                    className="flex items-center gap-3 flex-1 cursor-pointer"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
                      <Folder className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="text-base line-clamp-1 hover:text-primary">
                        {channel.title}
                      </CardTitle>
                      <CardDescription>@{channel.username}</CardDescription>
                    </div>
                  </Link>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-destructive"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      removeChannelMutation.mutate(channel.id);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">
                        {channel.message_count || 0} messages
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Image className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">
                        {channel.media_count || 0} media
                      </span>
                    </div>
                  </div>

                  {activeJob ? (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2">
                          <RefreshCw className="h-4 w-4 animate-spin" />
                          Scraping...
                        </span>
                        <span>{Math.round(activeJob.progress_percent)}%</span>
                      </div>
                      <Progress value={activeJob.progress_percent} />
                    </div>
                  ) : (
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={() => startScrapeMutation.mutate(channel.id)}
                      disabled={startScrapeMutation.isPending}
                    >
                      <Play className="mr-2 h-4 w-4" />
                      Start Scrape
                    </Button>
                  )}

                  {channel.last_scraped_at && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Last scraped:{" "}
                      {new Date(channel.last_scraped_at).toLocaleDateString()}
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
