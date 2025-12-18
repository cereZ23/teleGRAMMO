"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  MessageSquare,
  Image,
  Folder,
  TrendingUp,
  Calendar,
  Users,
  Loader2,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { analyticsApi, channelsApi } from "@/lib/api";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

export default function AnalyticsPage() {
  const [selectedChannel, setSelectedChannel] = useState<string | undefined>(undefined);
  const [timeRange, setTimeRange] = useState(30);

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: analyticsApi.getOverview,
  });

  const { data: channels } = useQuery({
    queryKey: ["channels"],
    queryFn: channelsApi.getChannels,
  });

  const { data: messagesOverTime, isLoading: messagesLoading } = useQuery({
    queryKey: ["messages-over-time", selectedChannel, timeRange],
    queryFn: () => analyticsApi.getMessagesOverTime(selectedChannel, timeRange),
  });

  const { data: topSenders, isLoading: sendersLoading } = useQuery({
    queryKey: ["top-senders", selectedChannel],
    queryFn: () => analyticsApi.getTopSenders(selectedChannel),
  });

  const { data: mediaBreakdown, isLoading: mediaLoading } = useQuery({
    queryKey: ["media-breakdown", selectedChannel],
    queryFn: () => analyticsApi.getMediaBreakdown(selectedChannel),
  });

  const { data: activityHeatmap, isLoading: activityLoading } = useQuery({
    queryKey: ["activity-heatmap", selectedChannel],
    queryFn: () => analyticsApi.getActivityHeatmap(selectedChannel),
  });

  const { data: channelStats } = useQuery({
    queryKey: ["channel-stats"],
    queryFn: analyticsApi.getChannelStats,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Insights and statistics from your scraped data
          </p>
        </div>
        <div className="flex gap-2">
          <select
            className="rounded-md border px-3 py-2"
            value={selectedChannel || ""}
            onChange={(e) => setSelectedChannel(e.target.value || undefined)}
          >
            <option value="">All Channels</option>
            {channels?.channels?.map((channel: { id: string; title: string }) => (
              <option key={channel.id} value={channel.id}>
                {channel.title}
              </option>
            ))}
          </select>
          <select
            className="rounded-md border px-3 py-2"
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>
      </div>

      {/* Overview Stats */}
      {overviewLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-5">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Folder className="h-4 w-4 text-muted-foreground" />
                <span className="text-2xl font-bold">{overview?.total_channels || 0}</span>
              </div>
              <p className="text-xs text-muted-foreground">Channels</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
                <span className="text-2xl font-bold">
                  {(overview?.total_messages || 0).toLocaleString()}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">Total Messages</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Image className="h-4 w-4 text-muted-foreground" />
                <span className="text-2xl font-bold">
                  {(overview?.total_media || 0).toLocaleString()}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">Media Files</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span className="text-2xl font-bold">
                  {(overview?.messages_today || 0).toLocaleString()}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">Messages Today</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-blue-500" />
                <span className="text-2xl font-bold">
                  {(overview?.messages_this_week || 0).toLocaleString()}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">This Week</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts Row 1 */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Messages Over Time */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Messages Over Time
            </CardTitle>
            <CardDescription>Daily message count for the selected period</CardDescription>
          </CardHeader>
          <CardContent>
            {messagesLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : messagesOverTime?.data?.length ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={messagesOverTime.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return `${date.getMonth() + 1}/${date.getDate()}`;
                    }}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-64 items-center justify-center text-muted-foreground">
                No data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Media Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Image className="h-5 w-5" />
              Media Breakdown
            </CardTitle>
            <CardDescription>Distribution of media types</CardDescription>
          </CardHeader>
          <CardContent>
            {mediaLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : mediaBreakdown?.data?.length ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={mediaBreakdown.data}
                    dataKey="count"
                    nameKey="type"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ type, percent }) =>
                      `${type} (${(percent * 100).toFixed(0)}%)`
                    }
                  >
                    {mediaBreakdown.data.map((entry: { type: string }, index: number) => (
                      <Cell key={entry.type} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-64 items-center justify-center text-muted-foreground">
                No media data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Top Senders */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Top Senders
            </CardTitle>
            <CardDescription>Most active message senders</CardDescription>
          </CardHeader>
          <CardContent>
            {sendersLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : topSenders?.data?.length ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topSenders.data} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={120}
                    tickFormatter={(value) =>
                      value.length > 15 ? `${value.slice(0, 15)}...` : value
                    }
                  />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-64 items-center justify-center text-muted-foreground">
                No sender data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Activity by Hour */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Activity by Hour
            </CardTitle>
            <CardDescription>Message distribution by hour of day</CardDescription>
          </CardHeader>
          <CardContent>
            {activityLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : activityHeatmap?.hourly?.length ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={activityHeatmap.hourly}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="hour"
                    tickFormatter={(value) => `${value}:00`}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => `${value}:00 - ${value}:59`}
                  />
                  <Bar dataKey="count" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-64 items-center justify-center text-muted-foreground">
                No activity data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Activity by Day of Week */}
      <Card>
        <CardHeader>
          <CardTitle>Activity by Day of Week</CardTitle>
          <CardDescription>Message distribution across days of the week</CardDescription>
        </CardHeader>
        <CardContent>
          {activityLoading ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : activityHeatmap?.daily?.length ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={activityHeatmap.daily}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-48 items-center justify-center text-muted-foreground">
              No activity data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Channel Stats Table */}
      <Card>
        <CardHeader>
          <CardTitle>Channel Statistics</CardTitle>
          <CardDescription>Overview of all tracked channels</CardDescription>
        </CardHeader>
        <CardContent>
          {channelStats?.data?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="pb-2 text-left font-medium">Channel</th>
                    <th className="pb-2 text-right font-medium">Messages</th>
                    <th className="pb-2 text-right font-medium">Media</th>
                    <th className="pb-2 text-right font-medium">Auto-Scrape</th>
                  </tr>
                </thead>
                <tbody>
                  {channelStats.data.map((channel: {
                    id: string;
                    title: string;
                    username: string;
                    message_count: number;
                    media_count: number;
                    schedule_enabled: boolean;
                  }) => (
                    <tr key={channel.id} className="border-b">
                      <td className="py-2">
                        <div>
                          <p className="font-medium">{channel.title}</p>
                          <p className="text-sm text-muted-foreground">@{channel.username}</p>
                        </div>
                      </td>
                      <td className="py-2 text-right">{channel.message_count.toLocaleString()}</td>
                      <td className="py-2 text-right">{channel.media_count.toLocaleString()}</td>
                      <td className="py-2 text-right">
                        <span
                          className={`rounded px-2 py-1 text-xs ${
                            channel.schedule_enabled
                              ? "bg-green-100 text-green-700"
                              : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {channel.schedule_enabled ? "Enabled" : "Disabled"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              No channels tracked yet
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
