import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Door Face Panels — Smart entrance dashboard",
  description:
    "Unified smart door: face access, object safety, fall monitoring, and compliance audit trail from one camera at the threshold.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-transparent text-slate-600 font-sans flex h-screen overflow-hidden antialiased">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-y-auto p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
