"use client";

import { useEffect, useState } from "react";
import { keywordsApi, channelsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import {
  Bell,
  Plus,
  Trash2,
  Edit,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Loader2,
  Search,
  Hash,
  Code,
  ToggleLeft,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface KeywordAlert {
  id: string;
  keyword: string;
  channel_id: string | null;
  channel_title: string | null;
  is_regex: boolean;
  is_case_sensitive: boolean;
  is_active: boolean;
  notify_webhook: string | null;
  match_count: number;
  last_match_at: string | null;
  created_at: string;
}

interface KeywordMatch {
  id: string;
  keyword_alert_id: string;
  keyword: string;
  message_id: string;
  channel_id: string;
  channel_title: string | null;
  matched_text: string | null;
  message_date: string | null;
  is_read: boolean;
  created_at: string;
}

interface Channel {
  id: string;
  title: string;
}

export default function KeywordsPage() {
  const [alerts, setAlerts] = useState<KeywordAlert[]>([]);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAlert, setEditingAlert] = useState<KeywordAlert | null>(null);
  const [matchesDialogOpen, setMatchesDialogOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<KeywordAlert | null>(null);
  const [matches, setMatches] = useState<KeywordMatch[]>([]);
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Form state
  const [keyword, setKeyword] = useState("");
  const [channelId, setChannelId] = useState<string>("");
  const [isRegex, setIsRegex] = useState(false);
  const [isCaseSensitive, setIsCaseSensitive] = useState(false);
  const [notifyWebhook, setNotifyWebhook] = useState("");
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [alertsRes, channelsRes, unreadRes] = await Promise.all([
        keywordsApi.getAlerts(),
        channelsApi.getChannels(),
        keywordsApi.getUnreadCount(),
      ]);
      setAlerts(alertsRes.alerts);
      setChannels(channelsRes.channels || []);
      setUnreadCount(unreadRes.unread_count);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setKeyword("");
    setChannelId("");
    setIsRegex(false);
    setIsCaseSensitive(false);
    setNotifyWebhook("");
    setFormError("");
    setEditingAlert(null);
  };

  const openCreateDialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const openEditDialog = (alert: KeywordAlert) => {
    setEditingAlert(alert);
    setKeyword(alert.keyword);
    setChannelId(alert.channel_id || "");
    setIsRegex(alert.is_regex);
    setIsCaseSensitive(alert.is_case_sensitive);
    setNotifyWebhook(alert.notify_webhook || "");
    setFormError("");
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!keyword.trim()) {
      setFormError("Keyword is required");
      return;
    }

    // Validate regex if enabled
    if (isRegex) {
      try {
        new RegExp(keyword);
      } catch {
        setFormError("Invalid regular expression");
        return;
      }
    }

    try {
      setSubmitting(true);
      setFormError("");

      const data = {
        keyword: keyword.trim(),
        channel_id: channelId || undefined,
        is_regex: isRegex,
        is_case_sensitive: isCaseSensitive,
        notify_webhook: notifyWebhook.trim() || undefined,
      };

      if (editingAlert) {
        await keywordsApi.updateAlert(editingAlert.id, data);
      } else {
        await keywordsApi.createAlert(data);
      }

      setDialogOpen(false);
      resetForm();
      loadData();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      setFormError(err.response?.data?.detail || "Failed to save alert");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (alertId: string) => {
    if (!confirm("Are you sure you want to delete this keyword alert?")) {
      return;
    }

    try {
      await keywordsApi.deleteAlert(alertId);
      loadData();
    } catch (error) {
      console.error("Failed to delete alert:", error);
    }
  };

  const handleToggleActive = async (alert: KeywordAlert) => {
    try {
      await keywordsApi.updateAlert(alert.id, { is_active: !alert.is_active });
      loadData();
    } catch (error) {
      console.error("Failed to toggle alert:", error);
    }
  };

  const openMatchesDialog = async (alert: KeywordAlert) => {
    setSelectedAlert(alert);
    setMatchesDialogOpen(true);
    setMatchesLoading(true);

    try {
      const res = await keywordsApi.getMatches(alert.id, 1, 50);
      setMatches(res.matches);
    } catch (error) {
      console.error("Failed to load matches:", error);
    } finally {
      setMatchesLoading(false);
    }
  };

  const handleMarkAllRead = async () => {
    if (!selectedAlert) return;

    try {
      await keywordsApi.markMatchesRead(selectedAlert.id);
      setMatches(matches.map((m) => ({ ...m, is_read: true })));
      loadData();
    } catch (error) {
      console.error("Failed to mark as read:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Keyword Alerts</h1>
          <p className="text-muted-foreground">
            Monitor channels for specific keywords and patterns
          </p>
        </div>
        <div className="flex items-center gap-4">
          {unreadCount > 0 && (
            <Badge variant="destructive" className="text-sm">
              {unreadCount} unread matches
            </Badge>
          )}
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={openCreateDialog}>
                <Plus className="h-4 w-4 mr-2" />
                New Alert
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>
                  {editingAlert ? "Edit Alert" : "Create Keyword Alert"}
                </DialogTitle>
                <DialogDescription>
                  Set up monitoring for specific keywords in your channels
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {formError && (
                  <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    {formError}
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="keyword">Keyword or Pattern</Label>
                  <Input
                    id="keyword"
                    placeholder={isRegex ? "bitcoin|crypto|btc" : "bitcoin"}
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    {isRegex
                      ? "Enter a valid regular expression"
                      : "Enter the keyword to search for"}
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="channel">Channel</Label>
                  <Select value={channelId || "all"} onValueChange={(val) => setChannelId(val === "all" ? "" : val)}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Channels" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Channels</SelectItem>
                      {channels.map((channel) => (
                        <SelectItem key={channel.id} value={channel.id}>
                          {channel.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="regex">Regular Expression</Label>
                    <p className="text-xs text-muted-foreground">
                      Enable regex pattern matching
                    </p>
                  </div>
                  <Switch
                    id="regex"
                    checked={isRegex}
                    onCheckedChange={setIsRegex}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="case">Case Sensitive</Label>
                    <p className="text-xs text-muted-foreground">
                      Match exact case
                    </p>
                  </div>
                  <Switch
                    id="case"
                    checked={isCaseSensitive}
                    onCheckedChange={setIsCaseSensitive}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="webhook">Webhook URL (Optional)</Label>
                  <Input
                    id="webhook"
                    type="url"
                    placeholder="https://hooks.slack.com/..."
                    value={notifyWebhook}
                    onChange={(e) => setNotifyWebhook(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Receive notifications when matches are found
                  </p>
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button onClick={handleSubmit} disabled={submitting}>
                  {submitting && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  {editingAlert ? "Save Changes" : "Create Alert"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {alerts.filter((a) => a.is_active).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Matches</CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {alerts.reduce((sum, a) => sum + a.match_count, 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unread</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{unreadCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts List */}
      {alerts.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Bell className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Keyword Alerts</h3>
            <p className="text-muted-foreground text-center mb-4">
              Create your first alert to monitor channels for specific keywords
            </p>
            <Button onClick={openCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              Create Alert
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Your Alerts</CardTitle>
            <CardDescription>
              Click on an alert to view matches
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Keyword</TableHead>
                  <TableHead>Channel</TableHead>
                  <TableHead>Options</TableHead>
                  <TableHead className="text-right">Matches</TableHead>
                  <TableHead>Last Match</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alerts.map((alert) => (
                  <TableRow
                    key={alert.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => openMatchesDialog(alert)}
                  >
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {alert.is_regex ? (
                          <Code className="h-4 w-4 text-purple-500" />
                        ) : (
                          <Hash className="h-4 w-4 text-blue-500" />
                        )}
                        <code className="text-sm bg-muted px-2 py-0.5 rounded">
                          {alert.keyword}
                        </code>
                      </div>
                    </TableCell>
                    <TableCell>{alert.channel_title || "All Channels"}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {alert.is_regex && (
                          <Badge variant="outline" className="text-xs">
                            Regex
                          </Badge>
                        )}
                        {alert.is_case_sensitive && (
                          <Badge variant="outline" className="text-xs">
                            Case
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {alert.match_count}
                    </TableCell>
                    <TableCell>
                      {alert.last_match_at ? (
                        <span className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(alert.last_match_at), {
                            addSuffix: true,
                          })}
                        </span>
                      ) : (
                        <span className="text-sm text-muted-foreground">
                          Never
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={alert.is_active ? "default" : "secondary"}
                        className={alert.is_active ? "bg-green-500" : ""}
                      >
                        {alert.is_active ? "Active" : "Paused"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div
                        className="flex items-center justify-end gap-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleToggleActive(alert)}
                          title={alert.is_active ? "Pause" : "Activate"}
                        >
                          {alert.is_active ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(alert)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(alert.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Matches Dialog */}
      <Dialog open={matchesDialogOpen} onOpenChange={setMatchesDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              Matches for{" "}
              <code className="bg-muted px-2 py-0.5 rounded text-sm">
                {selectedAlert?.keyword}
              </code>
            </DialogTitle>
            <DialogDescription>
              {selectedAlert?.match_count} total matches
            </DialogDescription>
          </DialogHeader>

          <div className="max-h-[50vh] overflow-y-auto">
            {matchesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : matches.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No matches found yet
              </div>
            ) : (
              <Accordion type="single" collapsible className="w-full">
                {matches.map((match) => (
                  <AccordionItem key={match.id} value={match.id}>
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center gap-3 text-left">
                        {!match.is_read && (
                          <span className="h-2 w-2 rounded-full bg-blue-500" />
                        )}
                        <span className="font-medium">
                          {match.channel_title}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {match.message_date
                            ? formatDistanceToNow(new Date(match.message_date), {
                                addSuffix: true,
                              })
                            : ""}
                        </span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-sm whitespace-pre-wrap">
                          {match.matched_text || "No preview available"}
                        </p>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setMatchesDialogOpen(false)}>
              Close
            </Button>
            {matches.some((m) => !m.is_read) && (
              <Button onClick={handleMarkAllRead}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Mark All Read
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
