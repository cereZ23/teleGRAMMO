"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Radio,
  Folder,
  MessageSquare,
  Download,
  Plus,
  ArrowRight,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { channelsApi, jobsApi, telegramApi } from "@/lib/api";

export default function DashboardPage() {
  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ["telegram-sessions"],
    queryFn: telegramApi.getSessions,
  });

  const { data: channels, isLoading: channelsLoading } = useQuery({
    queryKey: ["channels"],
    queryFn: channelsApi.getChannels,
  });

  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: jobsApi.getJobs,
  });

  const activeJobs = jobs?.jobs?.filter(
    (job: { status: string }) => job.status === "running" || job.status === "pending"
  ) || [];

  const stats = [
    {
      title: "Telegram Sessions",
      value: sessions?.length || 0,
      icon: Radio,
      description: "Active connections",
      href: "/dashboard/telegram",
    },
    {
      title: "Tracked Channels",
      value: channels?.channels?.length || 0,
      icon: Folder,
      description: "Monitoring",
      href: "/dashboard/channels",
    },
    {
      title: "Messages Scraped",
      value: channels?.channels?.reduce(
        (acc: number, ch: { message_count?: number }) => acc + (ch.message_count || 0),
        0
      ) || 0,
      icon: MessageSquare,
      description: "Total collected",
      href: "/dashboard/channels",
    },
    {
      title: "Media Files",
      value: channels?.channels?.reduce(
        (acc: number, ch: { media_count?: number }) => acc + (ch.media_count || 0),
        0
      ) || 0,
      icon: Download,
      description: "Downloaded",
      href: "/dashboard/channels",
    },
  ];

  const isLoading = sessionsLoading || channelsLoading || jobsLoading;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your Telegram scraping activity
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/telegram">
            <Button variant="outline">
              <Radio className="mr-2 h-4 w-4" />
              Connect Telegram
            </Button>
          </Link>
          <Link href="/dashboard/channels">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Channel
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Link key={stat.title} href={stat.href}>
            <Card className="transition-shadow hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <>
                    <div className="text-2xl font-bold">{stat.value}</div>
                    <p className="text-xs text-muted-foreground">
                      {stat.description}
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Active Jobs */}
        <Card>
          <CardHeader>
            <CardTitle>Active Jobs</CardTitle>
            <CardDescription>Currently running scraping tasks</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : activeJobs.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                <p>No active jobs</p>
                <p className="text-sm">Start a scrape from the Channels page</p>
              </div>
            ) : (
              <div className="space-y-4">
                {activeJobs.slice(0, 5).map((job: {
                  id: string;
                  job_type: string;
                  status: string;
                  progress_percent: number;
                  messages_processed: number;
                }) => (
                  <div key={job.id} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{job.job_type}</span>
                      <span className="text-muted-foreground">
                        {job.status}
                      </span>
                    </div>
                    <Progress value={job.progress_percent} />
                    <p className="text-xs text-muted-foreground">
                      {job.messages_processed} messages processed
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks to get you started</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!sessions?.length && (
              <Link
                href="/dashboard/telegram"
                className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
                    <Radio className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium">Connect Telegram</p>
                    <p className="text-sm text-muted-foreground">
                      Add your Telegram API credentials
                    </p>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground" />
              </Link>
            )}

            <Link
              href="/dashboard/channels"
              className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
                  <Folder className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium">Add a Channel</p>
                  <p className="text-sm text-muted-foreground">
                    Start tracking a Telegram channel
                  </p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-muted-foreground" />
            </Link>

            <Link
              href="/dashboard/channels"
              className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
                  <Download className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="font-medium">Export Data</p>
                  <p className="text-sm text-muted-foreground">
                    Download messages as CSV or JSON
                  </p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-muted-foreground" />
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Recent Channels */}
      {channels?.channels?.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Channels</CardTitle>
              <CardDescription>Your tracked Telegram channels</CardDescription>
            </div>
            <Link href="/dashboard/channels">
              <Button variant="outline" size="sm">
                View All
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {channels.channels.slice(0, 5).map((channel: {
                id: string;
                title: string;
                username: string;
                message_count?: number;
              }) => (
                <div
                  key={channel.id}
                  className="flex items-center justify-between py-3"
                >
                  <div>
                    <p className="font-medium">{channel.title}</p>
                    <p className="text-sm text-muted-foreground">
                      @{channel.username}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {channel.message_count || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">messages</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
