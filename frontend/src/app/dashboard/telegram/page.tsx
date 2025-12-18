"use client";

import { useState } from "react";
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
import { Label } from "@/components/ui/label";
import {
  Radio,
  Plus,
  Trash2,
  CheckCircle2,
  XCircle,
  Loader2,
  ExternalLink,
  HelpCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { telegramApi } from "@/lib/api";

interface Session {
  id: string;
  api_id: number;
  phone_number?: string;
  is_authenticated: boolean;
  session_name?: string;
  created_at: string;
}

export default function TelegramPage() {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [showTutorial, setShowTutorial] = useState(true);
  const [apiId, setApiId] = useState("");
  const [apiHash, setApiHash] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [phoneCodeHash, setPhoneCodeHash] = useState("");
  const [pendingSessionId, setPendingSessionId] = useState<string | null>(null);
  const [authStep, setAuthStep] = useState<"credentials" | "phone" | "code">(
    "credentials"
  );

  const { data: sessions, isLoading } = useQuery({
    queryKey: ["telegram-sessions"],
    queryFn: telegramApi.getSessions,
  });

  const createSessionMutation = useMutation({
    mutationFn: () => telegramApi.createSession(parseInt(apiId), apiHash),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["telegram-sessions"] });
      setPendingSessionId(data.id);
      setAuthStep("phone");
    },
  });

  const sendCodeMutation = useMutation({
    mutationFn: () => telegramApi.sendCode(pendingSessionId!, phoneNumber),
    onSuccess: (data) => {
      setPhoneCodeHash(data.phone_code_hash);
      setAuthStep("code");
    },
  });

  const verifyCodeMutation = useMutation({
    mutationFn: () =>
      telegramApi.verifyCode(pendingSessionId!, verificationCode, phoneCodeHash),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["telegram-sessions"] });
      resetForm();
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => telegramApi.deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["telegram-sessions"] });
    },
  });

  const resetForm = () => {
    setShowAddForm(false);
    setApiId("");
    setApiHash("");
    setPhoneNumber("");
    setVerificationCode("");
    setPhoneCodeHash("");
    setPendingSessionId(null);
    setAuthStep("credentials");
  };

  const handleCreateSession = (e: React.FormEvent) => {
    e.preventDefault();
    createSessionMutation.mutate();
  };

  const handleSendCode = (e: React.FormEvent) => {
    e.preventDefault();
    sendCodeMutation.mutate();
  };

  const handleVerifyCode = (e: React.FormEvent) => {
    e.preventDefault();
    verifyCodeMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Telegram Sessions</h1>
          <p className="text-muted-foreground">
            Manage your Telegram API connections
          </p>
        </div>
        <Button onClick={() => setShowAddForm(true)} disabled={showAddForm}>
          <Plus className="mr-2 h-4 w-4" />
          Add Session
        </Button>
      </div>

      {/* Tutorial Card */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HelpCircle className="h-5 w-5 text-blue-600" />
              <CardTitle className="text-lg text-blue-900">How to Connect Telegram</CardTitle>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowTutorial(!showTutorial)}
              className="text-blue-600 hover:text-blue-800"
            >
              {showTutorial ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardHeader>
        {showTutorial && (
          <CardContent className="text-blue-900">
            <div className="space-y-4">
              {/* Step 1 */}
              <div className="flex gap-3">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  1
                </div>
                <div>
                  <p className="font-medium">Get your Telegram API credentials</p>
                  <p className="mt-1 text-sm text-blue-700">
                    Go to{" "}
                    <a
                      href="https://my.telegram.org/apps"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium underline hover:text-blue-900"
                    >
                      my.telegram.org/apps
                      <ExternalLink className="ml-1 inline h-3 w-3" />
                    </a>{" "}
                    and log in with your phone number.
                  </p>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex gap-3">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  2
                </div>
                <div>
                  <p className="font-medium">Create a new application</p>
                  <p className="mt-1 text-sm text-blue-700">
                    Click &quot;Create new application&quot; and fill in the form:
                  </p>
                  <ul className="mt-2 list-inside list-disc text-sm text-blue-700">
                    <li><strong>App title:</strong> Any name (e.g., &quot;My Scraper&quot;)</li>
                    <li><strong>Short name:</strong> Any short name (e.g., &quot;scraper&quot;)</li>
                    <li><strong>Platform:</strong> Desktop</li>
                    <li><strong>Description:</strong> Optional</li>
                  </ul>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex gap-3">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  3
                </div>
                <div>
                  <p className="font-medium">Copy your API ID and API Hash</p>
                  <p className="mt-1 text-sm text-blue-700">
                    After creating the app, you&apos;ll see your <strong>api_id</strong> (a number) and <strong>api_hash</strong> (a string). Copy both values.
                  </p>
                </div>
              </div>

              {/* Step 4 */}
              <div className="flex gap-3">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  4
                </div>
                <div>
                  <p className="font-medium">Add session here</p>
                  <p className="mt-1 text-sm text-blue-700">
                    Click &quot;Add Session&quot; above, paste your API ID and Hash, then verify with your phone number. You&apos;ll receive a code in your Telegram app.
                  </p>
                </div>
              </div>

              {/* Tips */}
              <div className="mt-4 rounded-lg bg-blue-100 p-3">
                <p className="text-sm font-medium text-blue-800">Important Notes:</p>
                <ul className="mt-1 list-inside list-disc text-sm text-blue-700">
                  <li>Your credentials are encrypted and stored securely</li>
                  <li>Each Telegram account needs its own session</li>
                  <li>You can only scrape channels you have access to</li>
                  <li>Respect Telegram&apos;s rate limits to avoid account restrictions</li>
                </ul>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Add Session Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle>Connect Telegram Account</CardTitle>
            <CardDescription>
              {authStep === "credentials" && (
                <>
                  Enter your Telegram API credentials. Get them from{" "}
                  <a
                    href="https://my.telegram.org/apps"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    my.telegram.org
                    <ExternalLink className="ml-1 inline h-3 w-3" />
                  </a>
                </>
              )}
              {authStep === "phone" &&
                "Enter your phone number to receive a verification code"}
              {authStep === "code" &&
                "Enter the verification code sent to your Telegram app"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {authStep === "credentials" && (
              <form onSubmit={handleCreateSession} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="api-id">API ID</Label>
                    <Input
                      id="api-id"
                      type="number"
                      placeholder="12345678"
                      value={apiId}
                      onChange={(e) => setApiId(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="api-hash">API Hash</Label>
                    <Input
                      id="api-hash"
                      type="password"
                      placeholder="Your API hash"
                      value={apiHash}
                      onChange={(e) => setApiHash(e.target.value)}
                      required
                    />
                  </div>
                </div>
                {createSessionMutation.isError && (
                  <p className="text-sm text-destructive">
                    {(createSessionMutation.error as Error)?.message ||
                      "Failed to create session"}
                  </p>
                )}
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    disabled={createSessionMutation.isPending}
                  >
                    {createSessionMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      "Continue"
                    )}
                  </Button>
                  <Button type="button" variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                </div>
              </form>
            )}

            {authStep === "phone" && (
              <form onSubmit={handleSendCode} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="+1234567890"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Include country code (e.g., +1 for US)
                  </p>
                </div>
                {sendCodeMutation.isError && (
                  <p className="text-sm text-destructive">
                    {(sendCodeMutation.error as Error)?.message ||
                      "Failed to send code"}
                  </p>
                )}
                <div className="flex gap-2">
                  <Button type="submit" disabled={sendCodeMutation.isPending}>
                    {sendCodeMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      "Send Code"
                    )}
                  </Button>
                  <Button type="button" variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                </div>
              </form>
            )}

            {authStep === "code" && (
              <form onSubmit={handleVerifyCode} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="code">Verification Code</Label>
                  <Input
                    id="code"
                    type="text"
                    placeholder="12345"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Check your Telegram app for the code
                  </p>
                </div>
                {verifyCodeMutation.isError && (
                  <p className="text-sm text-destructive">
                    {(verifyCodeMutation.error as Error)?.message ||
                      "Invalid code"}
                  </p>
                )}
                <div className="flex gap-2">
                  <Button type="submit" disabled={verifyCodeMutation.isPending}>
                    {verifyCodeMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Verifying...
                      </>
                    ) : (
                      "Verify"
                    )}
                  </Button>
                  <Button type="button" variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {/* Sessions List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : sessions?.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Radio className="mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="mb-2 text-lg font-semibold">No Telegram Sessions</h3>
            <p className="mb-4 text-center text-muted-foreground">
              Connect your Telegram account to start scraping channels
            </p>
            <Button onClick={() => setShowAddForm(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Session
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sessions?.map((session: Session) => (
            <Card key={session.id}>
              <CardHeader className="flex flex-row items-start justify-between space-y-0">
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                      session.is_authenticated
                        ? "bg-green-100"
                        : "bg-yellow-100"
                    }`}
                  >
                    <Radio
                      className={`h-5 w-5 ${
                        session.is_authenticated
                          ? "text-green-600"
                          : "text-yellow-600"
                      }`}
                    />
                  </div>
                  <div>
                    <CardTitle className="text-base">
                      {session.session_name || `Session ${session.api_id}`}
                    </CardTitle>
                    <CardDescription>
                      {session.phone_number || "Not authenticated"}
                    </CardDescription>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-destructive"
                  onClick={() => deleteSessionMutation.mutate(session.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 text-sm">
                  {session.is_authenticated ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span className="text-green-600">Connected</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4 text-yellow-500" />
                      <span className="text-yellow-600">
                        Authentication required
                      </span>
                    </>
                  )}
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  API ID: {session.api_id}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
