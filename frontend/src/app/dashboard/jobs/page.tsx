"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  Play,
  Square,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { jobsApi } from "@/lib/api";

interface Job {
  id: string;
  channel_id: string;
  job_type: string;
  status: string;
  progress_percent: number;
  messages_processed: number;
  media_downloaded: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

const statusConfig: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
  pending: { icon: Clock, color: "text-yellow-600", bg: "bg-yellow-100" },
  running: { icon: RefreshCw, color: "text-blue-600", bg: "bg-blue-100" },
  completed: { icon: CheckCircle2, color: "text-green-600", bg: "bg-green-100" },
  failed: { icon: XCircle, color: "text-red-600", bg: "bg-red-100" },
  cancelled: { icon: Square, color: "text-gray-600", bg: "bg-gray-100" },
};

export default function JobsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["jobs"],
    queryFn: jobsApi.getJobs,
    refetchInterval: 5000, // Poll every 5 seconds for updates
  });

  const cancelMutation = useMutation({
    mutationFn: (jobId: string) => jobsApi.cancelJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const jobs: Job[] = data?.jobs || [];
  const activeJobs = jobs.filter((j) => j.status === "running" || j.status === "pending");
  const completedJobs = jobs.filter((j) => j.status === "completed");
  const failedJobs = jobs.filter((j) => j.status === "failed" || j.status === "cancelled");

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleString();
  };

  const formatDuration = (start: string | null, end: string | null) => {
    if (!start) return "N/A";
    const startDate = new Date(start);
    const endDate = end ? new Date(end) : new Date();
    const seconds = Math.floor((endDate.getTime() - startDate.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Jobs</h1>
          <p className="text-muted-foreground">
            Monitor your scraping jobs and their progress
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{jobs.length}</div>
            <p className="text-xs text-muted-foreground">Total Jobs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-blue-600">{activeJobs.length}</div>
            <p className="text-xs text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">{completedJobs.length}</div>
            <p className="text-xs text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-red-600">{failedJobs.length}</div>
            <p className="text-xs text-muted-foreground">Failed</p>
          </CardContent>
        </Card>
      </div>

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Jobs</CardTitle>
            <CardDescription>Currently running scraping tasks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeJobs.map((job) => {
              const config = statusConfig[job.status] || statusConfig.pending;
              const StatusIcon = config.icon;

              return (
                <div key={job.id} className="rounded-lg border p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${config.bg}`}>
                        <StatusIcon className={`h-4 w-4 ${config.color} ${job.status === "running" ? "animate-spin" : ""}`} />
                      </div>
                      <div>
                        <p className="font-medium capitalize">{job.job_type.replace("_", " ")}</p>
                        <p className="text-xs text-muted-foreground">
                          Started: {formatDate(job.started_at)}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => cancelMutation.mutate(job.id)}
                      disabled={cancelMutation.isPending}
                    >
                      <Square className="mr-2 h-3 w-3" />
                      Cancel
                    </Button>
                  </div>
                  <Progress value={job.progress_percent} className="mb-2" />
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>{Math.round(job.progress_percent)}% complete</span>
                    <span>{job.messages_processed} messages</span>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Job History */}
      <Card>
        <CardHeader>
          <CardTitle>Job History</CardTitle>
          <CardDescription>All scraping jobs</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              <p>No jobs yet</p>
              <p className="text-sm">Start a scrape from the Channels page</p>
            </div>
          ) : (
            <div className="space-y-2">
              {jobs.map((job) => {
                const config = statusConfig[job.status] || statusConfig.pending;
                const StatusIcon = config.icon;

                return (
                  <div
                    key={job.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${config.bg}`}>
                        <StatusIcon className={`h-4 w-4 ${config.color}`} />
                      </div>
                      <div>
                        <p className="font-medium capitalize">
                          {job.job_type.replace("_", " ")}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(job.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {job.messages_processed} messages
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Duration: {formatDuration(job.started_at, job.completed_at)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
