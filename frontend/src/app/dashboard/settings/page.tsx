"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";
import { Settings, User, Shield, Database } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account and application settings
        </p>
      </div>

      <div className="grid gap-6">
        {/* Account Info */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
                <User className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <CardTitle>Account</CardTitle>
                <CardDescription>Your account information</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-1">
              <label className="text-sm font-medium text-muted-foreground">
                Email
              </label>
              <p>{user?.email}</p>
            </div>
            <div className="grid gap-1">
              <label className="text-sm font-medium text-muted-foreground">
                Account Created
              </label>
              <p>
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : "N/A"}
              </p>
            </div>
            <div className="grid gap-1">
              <label className="text-sm font-medium text-muted-foreground">
                Status
              </label>
              <p className="flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${
                    user?.is_active ? "bg-green-500" : "bg-red-500"
                  }`}
                />
                {user?.is_active ? "Active" : "Inactive"}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-100">
                <Shield className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <CardTitle>Security</CardTitle>
                <CardDescription>Manage your security settings</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Password</p>
                <p className="text-sm text-muted-foreground">
                  Last changed: Never
                </p>
              </div>
              <Button variant="outline" disabled>
                Change Password
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Two-Factor Authentication</p>
                <p className="text-sm text-muted-foreground">
                  Add extra security to your account
                </p>
              </div>
              <Button variant="outline" disabled>
                Enable 2FA
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Data */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
                <Database className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <CardTitle>Data</CardTitle>
                <CardDescription>Manage your scraped data</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Export All Data</p>
                <p className="text-sm text-muted-foreground">
                  Download all your scraped messages and media
                </p>
              </div>
              <Button variant="outline" disabled>
                Export
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-destructive">Delete All Data</p>
                <p className="text-sm text-muted-foreground">
                  Permanently delete all your scraped data
                </p>
              </div>
              <Button variant="destructive" disabled>
                Delete
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* App Info */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100">
                <Settings className="h-5 w-5 text-gray-600" />
              </div>
              <div>
                <CardTitle>Application</CardTitle>
                <CardDescription>App information and version</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid gap-1">
                <label className="text-sm font-medium text-muted-foreground">
                  Version
                </label>
                <p>4.0.0</p>
              </div>
              <div className="grid gap-1">
                <label className="text-sm font-medium text-muted-foreground">
                  API Status
                </label>
                <p className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  Connected
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
