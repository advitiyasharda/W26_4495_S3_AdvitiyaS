/**
 * Single module for all FaceDoor UI demo/sample data and demo fallback helpers.
 * Add new demo rows here only — do not scatter demo fixtures across other files.
 */
import type {
  Threat,
  AuditEntry,
  AccessLog,
  FallEvent,
  ObjectDetectionEvent,
  ObjectStatusResponse,
  FallStatusResponse,
  User,
  ObjectCategory,
} from "./api";
import { OBJECT_CATEGORIES, normalizeObjectCategory } from "./objectAnalytics";

// ── timestamp helpers (demo rows only) ───────────────────────────────────────
function ago(minutes: number) {
  return new Date(Date.now() - minutes * 60 * 1000).toISOString();
}

/** Wall-clock offset: h hours + extraMinutes ago (e.g. hoursAgo(1, 20) = 1h20m ago). */
function hoursAgo(h: number, extraMinutes = 0): string {
  return new Date(Date.now() - (h * 60 + extraMinutes) * 60 * 1000).toISOString();
}

/** Calendar day offset from today, local time */
function daysAgo(dayOffset: number, hour: number, minute = 0): string {
  const d = new Date();
  d.setDate(d.getDate() - dayOffset);
  d.setHours(hour, minute, 0, 0);
  return d.toISOString();
}

/** Timestamp pinned to today at a specific hour:minute — keeps chart spread across the day */
function todayAt(hour: number, minute = 0): string {
  const d = new Date();
  d.setHours(hour, minute, 0, 0);
  return d.toISOString();
}

// ── Demo Threats ──────────────────────────────────────────────────────────────
export const DEMO_THREATS: Threat[] = [
  {
    threat_type: "Multiple Failed Access Attempts",
    message: "Person ID #4821 failed face recognition 5 times in the last 10 minutes at the main entrance.",
    severity: "CRITICAL",
    timestamp: ago(3),
  },
  {
    threat_type: "Unusual Access Time",
    message: "Door access detected at 02:47 AM — outside permitted hours (06:00–22:00) for resident wing.",
    severity: "HIGH",
    timestamp: ago(18),
  },
  {
    threat_type: "Unrecognised Face Detected",
    message: "An unknown individual was detected at the east wing entrance. No match found in resident or staff database.",
    severity: "HIGH",
    timestamp: ago(34),
  },
  {
    threat_type: "Access Frequency Spike",
    message: "Room 204 door accessed 22 times in 30 minutes — 3× above normal threshold. Possible tailgating.",
    severity: "MEDIUM",
    timestamp: ago(51),
  },
  {
    threat_type: "Extended Inactivity Detected",
    message: "Resident Margaret T. (ID #1102) has not accessed any door in 28 hours — last seen in common room.",
    severity: "MEDIUM",
    timestamp: ago(90),
  },
  {
    threat_type: "Anomalous Behavioural Pattern",
    message: "Resident John D. (ID #0832) accessed the pharmacy corridor at 11:15 PM — first occurrence in 6 months.",
    severity: "MEDIUM",
    timestamp: ago(130),
  },
  {
    threat_type: "Camera Feed Interruption",
    message: "Door camera at North Entrance B lost video feed for 4 minutes. Auto-recovered at 14:22.",
    severity: "LOW",
    timestamp: ago(200),
  },
  {
    threat_type: "Low Confidence Recognition",
    message: "Staff member Dr. Patel recognised with 61% confidence — just above the acceptance threshold. Recommend re-registration.",
    severity: "LOW",
    timestamp: ago(310),
  },
  // Recent density for hourly / spark charts
  {
    threat_type: "Tailgating Suspected",
    message: "Two heat signatures crossed within 1.2s at west-wing reader — second crossing had no face match.",
    severity: "HIGH",
    timestamp: hoursAgo(1, 12),
  },
  {
    threat_type: "Door Held Open",
    message: "Main entrance magnetic contact open longer than 45s while reader showed no active session.",
    severity: "MEDIUM",
    timestamp: hoursAgo(2, 40),
  },
  {
    threat_type: "Badge Replay Pattern",
    message: "Same credential payload observed twice in 200ms — possible relay at pharmacy door.",
    severity: "HIGH",
    timestamp: hoursAgo(3, 5),
  },
  {
    threat_type: "After-Hours Motion",
    message: "PIR motion in lobby with no corresponding access event (02:18 AM).",
    severity: "MEDIUM",
    timestamp: hoursAgo(5, 18),
  },
  {
    threat_type: "Network Latency Spike",
    message: "Face API round-trip exceeded 2.8s for 6 consecutive frames — falls back to local cache.",
    severity: "LOW",
    timestamp: hoursAgo(8, 0),
  },

  // ── Previous 7 days (fills 7d dashboard alert chart) ─────────────────────
  {
    threat_type: "Unrecognised Face Detected",
    message: "Unknown individual at west wing entrance — no database match. Camera footage saved.",
    severity: "HIGH",
    timestamp: daysAgo(1, 14, 30),
  },
  {
    threat_type: "Multiple Failed Access Attempts",
    message: "3 failed recognition attempts in 10 minutes at pharmacy corridor.",
    severity: "HIGH",
    timestamp: daysAgo(1, 9, 15),
  },
  {
    threat_type: "Fall Detected",
    message: "High-confidence fall event near service elevator — staff notified immediately.",
    severity: "CRITICAL",
    timestamp: daysAgo(2, 11, 20),
  },
  {
    threat_type: "Unusual Access Time",
    message: "Night-time door access at 01:32 AM — outside permitted hours for resident wing.",
    severity: "HIGH",
    timestamp: daysAgo(2, 1, 32),
  },
  {
    threat_type: "Weapon Detected",
    message: "Object detection flagged possible knife at main entrance. Camera footage retained.",
    severity: "CRITICAL",
    timestamp: daysAgo(3, 15, 45),
  },
  {
    threat_type: "Tailgating Suspected",
    message: "Two persons entered within 0.8 seconds at east wing — second had no face match.",
    severity: "HIGH",
    timestamp: daysAgo(3, 12, 0),
  },
  {
    threat_type: "Wandering Resident",
    message: "Resident John D. (#0832) exited restricted corridor during night hours (22:40).",
    severity: "HIGH",
    timestamp: daysAgo(4, 22, 40),
  },
  {
    threat_type: "Unrecognised Face Detected",
    message: "Unknown person detected at main entrance — possible unregistered visitor.",
    severity: "MEDIUM",
    timestamp: daysAgo(4, 10, 5),
  },
  {
    threat_type: "Door Held Open",
    message: "Main entrance held open 60s with no active session — auto-alert triggered.",
    severity: "MEDIUM",
    timestamp: daysAgo(5, 14, 15),
  },
  {
    threat_type: "Fall Detected",
    message: "Near-fall event — resident self-corrected. No injury reported.",
    severity: "HIGH",
    timestamp: daysAgo(5, 9, 0),
  },
  {
    threat_type: "Camera Feed Interruption",
    message: "West entrance camera offline for 8 minutes — network connectivity fault.",
    severity: "LOW",
    timestamp: daysAgo(6, 16, 0),
  },
  {
    threat_type: "Badge Replay Pattern",
    message: "Duplicate credential replay detected at pharmacy door — access blocked.",
    severity: "HIGH",
    timestamp: daysAgo(6, 11, 20),
  },

  // ── Weeks 2-4 (fills 30d alert filter) ───────────────────────────────────
  {
    threat_type: "Weapon Detected",
    message: "Scissors-shaped object flagged at service entrance — security review initiated.",
    severity: "CRITICAL",
    timestamp: daysAgo(9, 10, 0),
  },
  {
    threat_type: "Unusual Access Time",
    message: "Staff badge used at 03:15 AM — flagged for management review.",
    severity: "HIGH",
    timestamp: daysAgo(11, 3, 15),
  },
  {
    threat_type: "Fall Detected",
    message: "Confirmed fall event — rapid lateral movement with high LSTM agreement.",
    severity: "CRITICAL",
    timestamp: daysAgo(14, 15, 5),
  },
  {
    threat_type: "Tailgating Suspected",
    message: "Dual entry event at west wing — one face unmatched in resident database.",
    severity: "HIGH",
    timestamp: daysAgo(16, 9, 0),
  },
  {
    threat_type: "Unrecognised Face Detected",
    message: "Visitor without badge detected at east corridor during peak hours.",
    severity: "HIGH",
    timestamp: daysAgo(19, 14, 20),
  },
  {
    threat_type: "Multiple Failed Access Attempts",
    message: "4 consecutive failed attempts at main entrance within 15 minutes.",
    severity: "CRITICAL",
    timestamp: daysAgo(22, 11, 0),
  },
  {
    threat_type: "Fall Detected",
    message: "Fall event near dining hall — caregiver assisted within 1 minute.",
    severity: "CRITICAL",
    timestamp: daysAgo(25, 10, 30),
  },
  {
    threat_type: "Anomalous Behavioural Pattern",
    message: "Resident accessed exit door 7 times in 2 hours — unusual repetitive pattern.",
    severity: "MEDIUM",
    timestamp: daysAgo(27, 15, 45),
  },
];

// ── Demo Audit Entries ────────────────────────────────────────────────────────
export const DEMO_AUDIT: AuditEntry[] = [
  { action: "FACE_REGISTRATION",    user: "Admin",         resource: "resident/Margaret_T",          result: "success", timestamp: ago(5)   },
  { action: "ACCESS_GRANTED",       user: "Margaret_T",    resource: "door/west-wing-entrance",      result: "success", timestamp: ago(12)  },
  { action: "ACCESS_DENIED",        user: "Unknown #4821", resource: "door/main-entrance",           result: "failed",  timestamp: ago(20)  },
  { action: "ACCESS_DENIED",        user: "Unknown #4821", resource: "door/main-entrance",           result: "failed",  timestamp: ago(22)  },
  { action: "THREAT_CREATED",       user: "system",        resource: "threat/failed-attempts",       result: "success", timestamp: ago(22)  },
  { action: "ACCESS_GRANTED",       user: "Dr_Patel",      resource: "door/pharmacy-corridor",       result: "success", timestamp: ago(35)  },
  { action: "ANOMALY_DETECTED",     user: "system",        resource: "resident/John_D",              result: "success", timestamp: ago(50)  },
  { action: "ACCESS_GRANTED",       user: "John_D",        resource: "door/room-204",                result: "success", timestamp: ago(55)  },
  { action: "FACE_REGISTRATION",    user: "Admin",         resource: "staff/Dr_Patel",               result: "success", timestamp: ago(120) },
  { action: "DATA_EXPORT",          user: "Admin",         resource: "compliance/audit-log",         result: "success", timestamp: ago(180) },
  { action: "ACCESS_GRANTED",       user: "Nurse_Clarke",  resource: "door/medication-room",         result: "success", timestamp: ago(210) },
  { action: "SYSTEM_CONFIG_CHANGE", user: "Admin",         resource: "config/recognition-threshold", result: "success", timestamp: ago(260) },
  { action: "ACCESS_GRANTED",       user: "Margaret_T",    resource: "door/dining-hall",             result: "success", timestamp: ago(300) },
  { action: "ACCESS_DENIED",        user: "Unknown",       resource: "door/staff-only-east",         result: "failed",  timestamp: ago(340) },
  { action: "THREAT_RESOLVED",      user: "Admin",         resource: "threat/inactivity-0832",       result: "success", timestamp: ago(390) },
  { action: "FACE_REGISTRATION",    user: "Admin",         resource: "resident/Robert_H",            result: "success", timestamp: ago(450) },
  { action: "ACCESS_GRANTED",       user: "Robert_H",      resource: "door/main-entrance",           result: "success", timestamp: ago(480) },
  { action: "BACKUP_COMPLETED",     user: "system",        resource: "database/doorface.db",         result: "success", timestamp: ago(540) },
  { action: "ACCESS_GRANTED",       user: "Nurse_Clarke",  resource: "door/west-wing-entrance",      result: "success", timestamp: ago(600) },
  { action: "ANOMALY_DETECTED",     user: "system",        resource: "resident/Margaret_T",          result: "success", timestamp: ago(660) },
  { action: "LOGIN_SUCCESS",        user: "Admin",         resource: "session/web-dashboard",        result: "success", timestamp: ago(700) },
  { action: "REPORT_GENERATED",     user: "Admin",         resource: "report/weekly-access",         result: "success", timestamp: ago(720) },
  { action: "POLICY_UPDATE",        user: "Admin",         resource: "policy/retention-90d",         result: "success", timestamp: ago(800) },
  { action: "SESSION_TIMEOUT",      user: "Nurse_Clarke",  resource: "session/web-dashboard",        result: "success", timestamp: ago(820) },
  { action: "CONFIG_VIEW",          user: "Dr_Patel",      resource: "config/camera-west",           result: "success", timestamp: ago(900) },
  { action: "ACCESS_GRANTED",       user: "James_K",       resource: "door/service-elevator",        result: "success", timestamp: ago(940) },
  { action: "ACCESS_DENIED",        user: "Vendor_12",     resource: "door/pharmacy-corridor",       result: "failed",  timestamp: ago(960) },
  { action: "DATA_EXPORT",          user: "Admin",         resource: "export/faces-encrypted",       result: "success", timestamp: ago(1000) },
  { action: "THREAT_CREATED",       user: "system",        resource: "threat/tailgate-0144",         result: "success", timestamp: ago(1020) },

  // ── Historical audit entries (extends compliance table to 30d) ────────────
  { action: "ACCESS_GRANTED",       user: "Nurse_Clarke",  resource: "door/main-entrance",           result: "success", timestamp: daysAgo(1,  8, 5)  },
  { action: "ACCESS_DENIED",        user: "Unknown #7731", resource: "door/west-wing-entrance",      result: "failed",  timestamp: daysAgo(1,  9, 18) },
  { action: "THREAT_CREATED",       user: "system",        resource: "threat/unrecognised-7731",     result: "success", timestamp: daysAgo(1,  9, 18) },
  { action: "ACCESS_GRANTED",       user: "Margaret_T",    resource: "door/dining-hall",             result: "success", timestamp: daysAgo(1, 12, 30) },
  { action: "FACE_REGISTRATION",    user: "Admin",         resource: "resident/James_K",             result: "success", timestamp: daysAgo(2, 10,  0) },
  { action: "ACCESS_GRANTED",       user: "James_K",       resource: "door/main-entrance",           result: "success", timestamp: daysAgo(2, 11, 15) },
  { action: "ANOMALY_DETECTED",     user: "system",        resource: "resident/Robert_H",            result: "success", timestamp: daysAgo(2, 14, 35) },
  { action: "LOGIN_SUCCESS",        user: "Admin",         resource: "session/web-dashboard",        result: "success", timestamp: daysAgo(3,  8, 45) },
  { action: "ACCESS_GRANTED",       user: "Dr_Patel",      resource: "door/medication-room",         result: "success", timestamp: daysAgo(3, 11, 50) },
  { action: "REPORT_GENERATED",     user: "Admin",         resource: "report/monthly-compliance",    result: "success", timestamp: daysAgo(3, 15, 20) },
  { action: "ACCESS_DENIED",        user: "Vendor_08",     resource: "door/staff-only-east",         result: "failed",  timestamp: daysAgo(4, 13,  5) },
  { action: "THREAT_RESOLVED",      user: "Admin",         resource: "threat/tailgate-0832",         result: "success", timestamp: daysAgo(4, 16, 40) },
  { action: "ACCESS_GRANTED",       user: "Night_Nurse_Sam", resource: "door/west-wing-entrance",   result: "success", timestamp: daysAgo(5,  7, 10) },
  { action: "SYSTEM_CONFIG_CHANGE", user: "Admin",         resource: "config/fall-threshold",        result: "success", timestamp: daysAgo(5, 14,  0) },
  { action: "DATA_EXPORT",          user: "Admin",         resource: "export/access-logs-monthly",   result: "success", timestamp: daysAgo(6,  9, 30) },
  { action: "ACCESS_GRANTED",       user: "Linda_W",       resource: "door/dining-hall",             result: "success", timestamp: daysAgo(6, 12, 55) },
  { action: "BACKUP_COMPLETED",     user: "system",        resource: "database/doorface.db",         result: "success", timestamp: daysAgo(7,  2,  0) },
  { action: "FACE_REGISTRATION",    user: "Admin",         resource: "staff/Night_Nurse_Sam",        result: "success", timestamp: daysAgo(7, 10, 20) },
  { action: "ACCESS_GRANTED",       user: "Robert_H",      resource: "door/common-room",             result: "success", timestamp: daysAgo(8, 15, 45) },
  { action: "POLICY_UPDATE",        user: "Admin",         resource: "policy/door-hours",            result: "success", timestamp: daysAgo(9, 11,  0) },
  { action: "ACCESS_DENIED",        user: "Unknown",       resource: "door/pharmacy-corridor",       result: "failed",  timestamp: daysAgo(10,  8, 30) },
  { action: "LOGIN_SUCCESS",        user: "Admin",         resource: "session/web-dashboard",        result: "success", timestamp: daysAgo(11,  9,  0) },
  { action: "REPORT_GENERATED",     user: "Admin",         resource: "report/incident-summary",      result: "success", timestamp: daysAgo(12, 14, 15) },
  { action: "FACE_REGISTRATION",    user: "Admin",         resource: "resident/Linda_W",             result: "success", timestamp: daysAgo(14,  9, 30) },
  { action: "BACKUP_COMPLETED",     user: "system",        resource: "database/doorface.db",         result: "success", timestamp: daysAgo(14,  2,  0) },
  { action: "ACCESS_GRANTED",       user: "John_D",        resource: "door/main-entrance",           result: "success", timestamp: daysAgo(15, 11, 40) },
  { action: "SYSTEM_CONFIG_CHANGE", user: "Admin",         resource: "config/recognition-threshold", result: "success", timestamp: daysAgo(16, 10,  5) },
  { action: "DATA_EXPORT",          user: "Admin",         resource: "export/faces-encrypted",       result: "success", timestamp: daysAgo(17, 15, 30) },
  { action: "ACCESS_GRANTED",       user: "Nurse_Clarke",  resource: "door/medication-room",         result: "success", timestamp: daysAgo(18,  8, 55) },
  { action: "POLICY_UPDATE",        user: "Admin",         resource: "policy/visitor-log",           result: "success", timestamp: daysAgo(20, 11, 20) },
  { action: "BACKUP_COMPLETED",     user: "system",        resource: "database/doorface.db",         result: "success", timestamp: daysAgo(21,  2,  0) },
  { action: "FACE_REGISTRATION",    user: "Admin",         resource: "resident/John_D",              result: "success", timestamp: daysAgo(22, 10, 10) },
  { action: "ACCESS_DENIED",        user: "Vendor_19",     resource: "door/main-entrance",           result: "failed",  timestamp: daysAgo(23, 14, 0)  },
  { action: "REPORT_GENERATED",     user: "Admin",         resource: "report/weekly-access",         result: "success", timestamp: daysAgo(24, 15, 45) },
  { action: "LOGIN_SUCCESS",        user: "Admin",         resource: "session/web-dashboard",        result: "success", timestamp: daysAgo(25,  8,  0) },
  { action: "BACKUP_COMPLETED",     user: "system",        resource: "database/doorface.db",         result: "success", timestamp: daysAgo(28,  2,  0) },
  { action: "ACCESS_GRANTED",       user: "Dr_Patel",      resource: "door/west-wing-entrance",      result: "success", timestamp: daysAgo(28, 13, 30) },
  { action: "SYSTEM_CONFIG_CHANGE", user: "Admin",         resource: "config/camera-east",           result: "success", timestamp: daysAgo(29,  9, 15) },
];

// ── Demo Access Logs ──────────────────────────────────────────────────────────
// Ordered most-recent-first so the table always shows the latest events at the top.
// Timestamps span the full working day for a rich bar chart.
export const DEMO_LOGS: AccessLog[] = [
  // ── Most recent (17:xx) ───────────────────────────────────────────────────
  { person_id: "0551", name: "Nurse Clarke",     type: "entry", status: "success", confidence: 0.97, timestamp: todayAt(17, 55) },
  { person_id: "1102", name: "Margaret T.",      type: "exit",  status: "success", confidence: 0.94, timestamp: todayAt(17, 40) },
  { person_id: "0203", name: "Dr. Patel",        type: "exit",  status: "success", confidence: 0.92, timestamp: todayAt(17, 25) },
  { person_id: "0408", name: "James K.",         type: "exit",  status: "success", confidence: 0.89, timestamp: todayAt(17, 10) },

  // ── 16:xx ─────────────────────────────────────────────────────────────────
  { person_id: "0720", name: "Linda W.",         type: "entry", status: "success", confidence: 0.95, timestamp: todayAt(16, 45) },
  { person_id: "0301", name: "Robert H.",        type: "entry", status: "success", confidence: 0.87, timestamp: todayAt(16, 30) },
  { person_id: "0915", name: "Night Nurse Sam",  type: "exit",  status: "success", confidence: 0.91, timestamp: todayAt(16, 18) },
  { person_id: "0832", name: "John D.",          type: "exit",  status: "success", confidence: 0.93, timestamp: todayAt(16,  5) },

  // ── 15:xx ─────────────────────────────────────────────────────────────────
  { person_id: "1102", name: "Margaret T.",      type: "entry", status: "success", confidence: 0.96, timestamp: todayAt(15, 48) },
  { person_id: "0203", name: "Dr. Patel",        type: "entry", status: "success", confidence: 0.88, timestamp: todayAt(15, 38) },
  { person_id: "0408", name: "James K.",         type: "entry", status: "success", confidence: 0.90, timestamp: todayAt(15, 20) },
  { person_id: "0551", name: "Nurse Clarke",     type: "exit",  status: "success", confidence: 0.94, timestamp: todayAt(15,  8) },

  // ── 14:xx — afternoon shift change (busiest) ──────────────────────────────
  { person_id: "1102", name: "Margaret T.",      type: "exit",  status: "success", confidence: 0.97, timestamp: todayAt(14, 55) },
  { person_id: "0832", name: "John D.",          type: "entry", status: "success", confidence: 0.92, timestamp: todayAt(14, 50) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.38, timestamp: todayAt(14, 37) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.35, timestamp: todayAt(14, 35) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.37, timestamp: todayAt(14, 33) },
  { person_id: "0301", name: "Robert H.",        type: "exit",  status: "success", confidence: 0.88, timestamp: todayAt(14, 25) },
  { person_id: "0720", name: "Linda W.",         type: "exit",  status: "success", confidence: 0.91, timestamp: todayAt(14, 18) },
  { person_id: "0915", name: "Night Nurse Sam",  type: "entry", status: "success", confidence: 0.95, timestamp: todayAt(14, 10) },
  { person_id: "0203", name: "Dr. Patel",        type: "exit",  status: "success", confidence: 0.93, timestamp: todayAt(14,  5) },

  // ── 13:xx ─────────────────────────────────────────────────────────────────
  { person_id: "0551", name: "Nurse Clarke",     type: "entry", status: "success", confidence: 0.96, timestamp: todayAt(13, 50) },
  { person_id: "1102", name: "Margaret T.",      type: "entry", status: "success", confidence: 0.98, timestamp: todayAt(13, 35) },
  { person_id: "0408", name: "James K.",         type: "exit",  status: "success", confidence: 0.87, timestamp: todayAt(13, 20) },
  { person_id: "0832", name: "John D.",          type: "exit",  status: "success", confidence: 0.94, timestamp: todayAt(13, 10) },

  // ── 12:xx — lunch ─────────────────────────────────────────────────────────
  { person_id: "0203", name: "Dr. Patel",        type: "entry", status: "success", confidence: 0.91, timestamp: todayAt(12, 45) },
  { person_id: "0720", name: "Linda W.",         type: "entry", status: "success", confidence: 0.92, timestamp: todayAt(12, 22) },
  { person_id: "0301", name: "Robert H.",        type: "entry", status: "success", confidence: 0.87, timestamp: todayAt(12,  8) },

  // ── 11:xx ─────────────────────────────────────────────────────────────────
  { person_id: null,   name: null,               type: "entry", status: "failed",  confidence: 0.22, timestamp: todayAt(11, 52) },
  { person_id: "0551", name: "Nurse Clarke",     type: "exit",  status: "success", confidence: 0.95, timestamp: todayAt(11, 40) },
  { person_id: "0408", name: "James K.",         type: "entry", status: "success", confidence: 0.88, timestamp: todayAt(11, 28) },
  { person_id: "1102", name: "Margaret T.",      type: "exit",  status: "success", confidence: 0.96, timestamp: todayAt(11, 15) },
  { person_id: "0832", name: "John D.",          type: "entry", status: "success", confidence: 0.93, timestamp: todayAt(11,  5) },

  // ── 10:xx ─────────────────────────────────────────────────────────────────
  { person_id: "0203", name: "Dr. Patel",        type: "exit",  status: "success", confidence: 0.90, timestamp: todayAt(10, 55) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.31, timestamp: todayAt(10, 46) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.29, timestamp: todayAt(10, 44) },
  { person_id: "0551", name: "Nurse Clarke",     type: "entry", status: "success", confidence: 0.99, timestamp: todayAt(10, 35) },
  { person_id: "0301", name: "Robert H.",        type: "exit",  status: "success", confidence: 0.89, timestamp: todayAt(10, 20) },
  { person_id: "0720", name: "Linda W.",         type: "exit",  status: "success", confidence: 0.94, timestamp: todayAt(10,  7) },

  // ── 09:xx ─────────────────────────────────────────────────────────────────
  { person_id: "0408", name: "James K.",         type: "exit",  status: "success", confidence: 0.86, timestamp: todayAt(9, 50) },
  { person_id: "1102", name: "Margaret T.",      type: "entry", status: "success", confidence: 0.97, timestamp: todayAt(9, 33) },
  { person_id: "0832", name: "John D.",          type: "exit",  status: "success", confidence: 0.91, timestamp: todayAt(9, 25) },
  { person_id: "0203", name: "Dr. Patel",        type: "entry", status: "success", confidence: 0.89, timestamp: todayAt(9, 12) },
  { person_id: "0551", name: "Nurse Clarke",     type: "exit",  status: "success", confidence: 0.97, timestamp: todayAt(9,  3) },

  // ── 08:xx ─────────────────────────────────────────────────────────────────
  { person_id: "1102", name: "Margaret T.",      type: "exit",  status: "success", confidence: 0.95, timestamp: todayAt(8, 50) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.34, timestamp: todayAt(8, 41) },
  { person_id: "0203", name: "Dr. Patel",        type: "exit",  status: "success", confidence: 0.92, timestamp: todayAt(8, 30) },
  { person_id: "0408", name: "James K.",         type: "entry", status: "success", confidence: 0.87, timestamp: todayAt(8, 18) },
  { person_id: "0720", name: "Linda W.",         type: "entry", status: "success", confidence: 0.93, timestamp: todayAt(8, 10) },
  { person_id: "0301", name: "Robert H.",        type: "entry", status: "success", confidence: 0.88, timestamp: todayAt(8,  5) },

  // ── 07:xx — morning shift starts ─────────────────────────────────────────
  { person_id: "0832", name: "John D.",          type: "entry", status: "success", confidence: 0.90, timestamp: todayAt(7, 45) },
  { person_id: "1102", name: "Margaret T.",      type: "entry", status: "success", confidence: 0.96, timestamp: todayAt(7, 22) },
  { person_id: "0203", name: "Dr. Patel",        type: "entry", status: "success", confidence: 0.91, timestamp: todayAt(7, 15) },
  { person_id: "0551", name: "Nurse Clarke",     type: "entry", status: "success", confidence: 0.98, timestamp: todayAt(7,  8) },
  { person_id: "0915", name: "Night Nurse Sam",  type: "exit",  status: "success", confidence: 0.94, timestamp: todayAt(7,  2) },

  // ── Prior calendar days (7d dashboards & daily bar charts) ─────────────────
  { person_id: "1102", name: "Margaret T.",      type: "entry", status: "success", confidence: 0.94, timestamp: daysAgo(1, 16, 20) },
  { person_id: "0203", name: "Dr. Patel",        type: "exit",  status: "success", confidence: 0.91, timestamp: daysAgo(1, 15, 5) },
  { person_id: "0551", name: "Nurse Clarke",     type: "entry", status: "success", confidence: 0.97, timestamp: daysAgo(1, 10, 40) },
  { person_id: "0832", name: "John D.",          type: "exit",  status: "success", confidence: 0.89, timestamp: daysAgo(1, 18, 12) },
  { person_id: "0301", name: "Robert H.",        type: "entry", status: "success", confidence: 0.86, timestamp: daysAgo(2, 11, 0) },
  { person_id: "0408", name: "James K.",         type: "exit",  status: "success", confidence: 0.92, timestamp: daysAgo(2, 14, 30) },
  { person_id: "0720", name: "Linda W.",         type: "entry", status: "success", confidence: 0.93, timestamp: daysAgo(2, 9, 15) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.33, timestamp: daysAgo(2, 13, 22) },
  { person_id: "1102", name: "Margaret T.",      type: "exit",  status: "success", confidence: 0.96, timestamp: daysAgo(3, 17, 45) },
  { person_id: "0203", name: "Dr. Patel",        type: "entry", status: "success", confidence: 0.90, timestamp: daysAgo(3, 8, 20) },
  { person_id: "0551", name: "Nurse Clarke",     type: "exit",  status: "success", confidence: 0.95, timestamp: daysAgo(4, 12, 10) },
  { person_id: "0832", name: "John D.",          type: "entry", status: "success", confidence: 0.91, timestamp: daysAgo(4, 15, 0) },
  { person_id: "0301", name: "Robert H.",        type: "exit",  status: "success", confidence: 0.88, timestamp: daysAgo(5, 10, 30) },
  { person_id: "0408", name: "James K.",         type: "entry", status: "success", confidence: 0.87, timestamp: daysAgo(5, 14, 50) },
  { person_id: "1102", name: "Margaret T.",      type: "entry", status: "success", confidence: 0.98, timestamp: daysAgo(6, 9, 0) },
  { person_id: "0203", name: "Dr. Patel",        type: "exit",  status: "success", confidence: 0.92, timestamp: daysAgo(6, 16, 25) },

  // ── Historical weeks 2-4 (fills 30d time-range selector) ─────────────────
  { person_id: "0551", name: "Nurse Clarke",     type: "entry", status: "success", confidence: 0.95, timestamp: daysAgo(7,  9, 10) },
  { person_id: "1102", name: "Margaret T.",      type: "exit",  status: "success", confidence: 0.92, timestamp: daysAgo(7, 14, 30) },
  { person_id: "0203", name: "Dr. Patel",        type: "entry", status: "success", confidence: 0.88, timestamp: daysAgo(7, 16,  0) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.30, timestamp: daysAgo(8, 10, 15) },
  { person_id: "0832", name: "John D.",          type: "entry", status: "success", confidence: 0.91, timestamp: daysAgo(8, 15, 45) },
  { person_id: "0301", name: "Robert H.",        type: "exit",  status: "success", confidence: 0.87, timestamp: daysAgo(9,  8, 20) },
  { person_id: "0720", name: "Linda W.",         type: "entry", status: "success", confidence: 0.93, timestamp: daysAgo(9, 13, 55) },
  { person_id: "0551", name: "Nurse Clarke",     type: "exit",  status: "success", confidence: 0.96, timestamp: daysAgo(9, 17, 40) },
  { person_id: "1102", name: "Margaret T.",      type: "entry", status: "success", confidence: 0.97, timestamp: daysAgo(10,  9,  5) },
  { person_id: "0203", name: "Dr. Patel",        type: "exit",  status: "success", confidence: 0.89, timestamp: daysAgo(10, 16, 50) },
  { person_id: "0408", name: "James K.",         type: "entry", status: "success", confidence: 0.86, timestamp: daysAgo(11, 10, 30) },
  { person_id: "0832", name: "John D.",          type: "exit",  status: "success", confidence: 0.90, timestamp: daysAgo(11, 14, 15) },
  { person_id: "0915", name: "Night Nurse Sam",  type: "entry", status: "success", confidence: 0.94, timestamp: daysAgo(12,  7,  0) },
  { person_id: "0301", name: "Robert H.",        type: "entry", status: "success", confidence: 0.88, timestamp: daysAgo(12, 11, 25) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.28, timestamp: daysAgo(13, 13, 10) },
  { person_id: "1102", name: "Margaret T.",      type: "exit",  status: "success", confidence: 0.95, timestamp: daysAgo(13, 17,  0) },
  { person_id: "0551", name: "Nurse Clarke",     type: "entry", status: "success", confidence: 0.98, timestamp: daysAgo(14,  8, 40) },
  { person_id: "0720", name: "Linda W.",         type: "exit",  status: "success", confidence: 0.92, timestamp: daysAgo(14, 15, 20) },
  { person_id: "0203", name: "Dr. Patel",        type: "entry", status: "success", confidence: 0.90, timestamp: daysAgo(16,  9, 30) },
  { person_id: "0832", name: "John D.",          type: "exit",  status: "success", confidence: 0.91, timestamp: daysAgo(16, 14, 45) },
  { person_id: null,   name: null,               type: "entry", status: "failed",  confidence: 0.19, timestamp: daysAgo(17, 11,  0) },
  { person_id: "0408", name: "James K.",         type: "entry", status: "success", confidence: 0.87, timestamp: daysAgo(18, 10, 15) },
  { person_id: "1102", name: "Margaret T.",      type: "entry", status: "success", confidence: 0.96, timestamp: daysAgo(18, 16, 30) },
  { person_id: "0301", name: "Robert H.",        type: "exit",  status: "success", confidence: 0.88, timestamp: daysAgo(20,  9,  0) },
  { person_id: "0551", name: "Nurse Clarke",     type: "exit",  status: "success", confidence: 0.97, timestamp: daysAgo(20, 13, 50) },
  { person_id: "0203", name: "Dr. Patel",        type: "entry", status: "success", confidence: 0.89, timestamp: daysAgo(22,  8, 10) },
  { person_id: "0720", name: "Linda W.",         type: "entry", status: "success", confidence: 0.93, timestamp: daysAgo(22, 15,  0) },
  { person_id: "0832", name: "John D.",          type: "entry", status: "success", confidence: 0.92, timestamp: daysAgo(24, 10, 20) },
  { person_id: "1102", name: "Margaret T.",      type: "exit",  status: "success", confidence: 0.95, timestamp: daysAgo(24, 14,  5) },
  { person_id: "4821", name: null,               type: "entry", status: "failed",  confidence: 0.32, timestamp: daysAgo(26, 11, 30) },
  { person_id: "0551", name: "Nurse Clarke",     type: "entry", status: "success", confidence: 0.99, timestamp: daysAgo(26, 16, 15) },
  { person_id: "0203", name: "Dr. Patel",        type: "exit",  status: "success", confidence: 0.88, timestamp: daysAgo(28,  9, 40) },
  { person_id: "0408", name: "James K.",         type: "entry", status: "success", confidence: 0.86, timestamp: daysAgo(28, 14, 55) },
  { person_id: "0301", name: "Robert H.",        type: "exit",  status: "success", confidence: 0.90, timestamp: daysAgo(29, 11,  0) },
];

// ── Demo Fall Events (when API buffer is empty) ───────────────────────────────
export const DEMO_FALL_EVENTS: FallEvent[] = [
  {
    anomaly_id: 1,
    user_id: "0832",
    anomaly_type: "fall",
    anomaly_score: 0.91,
    description: "Rapid vertical displacement — possible fall (main entrance)",
    timestamp: ago(12),
  },
  {
    anomaly_id: 2,
    user_id: "1102",
    anomaly_type: "fall",
    anomaly_score: 0.72,
    description: "Unusual floor contact pattern detected",
    timestamp: ago(45),
  },
  {
    anomaly_id: 3,
    user_id: "0301",
    anomaly_type: "fall",
    anomaly_score: 0.55,
    description: "Body not fully visible — reduced confidence",
    timestamp: ago(120),
  },
  {
    anomaly_id: 4,
    user_id: "0203",
    anomaly_type: "fall",
    anomaly_score: 0.38,
    description: "Partial pose — possible slip near seating area",
    timestamp: ago(360),
  },
  {
    anomaly_id: 5,
    user_id: "0408",
    anomaly_type: "fall",
    anomaly_score: 0.88,
    description: "High-velocity change in torso trajectory",
    timestamp: ago(1440),
  },
  {
    anomaly_id: 6,
    user_id: "1102",
    anomaly_type: "fall",
    anomaly_score: 0.79,
    description: "Sudden drop in head elevation — corridor near dining",
    timestamp: daysAgo(1, 11, 18),
  },
  {
    anomaly_id: 7,
    user_id: "0832",
    anomaly_type: "fall",
    anomaly_score: 0.62,
    description: "Possible assisted sit-to-floor; caregiver entered frame 3s later",
    timestamp: daysAgo(1, 15, 42),
  },
  {
    anomaly_id: 8,
    user_id: "0301",
    anomaly_type: "fall",
    anomaly_score: 0.84,
    description: "Rapid lateral lean — high LSTM agreement",
    timestamp: daysAgo(2, 9, 5),
  },
  {
    anomaly_id: 9,
    user_id: "0203",
    anomaly_type: "fall",
    anomaly_score: 0.41,
    description: "Partial occlusion by door frame — confidence capped",
    timestamp: daysAgo(2, 14, 28),
  },
  {
    anomaly_id: 10,
    user_id: "0551",
    anomaly_type: "fall",
    anomaly_score: 0.73,
    description: "Wheelchair stop followed by unexpected trunk angle",
    timestamp: daysAgo(3, 10, 12),
  },
  {
    anomaly_id: 11,
    user_id: "0408",
    anomaly_type: "fall",
    anomaly_score: 0.67,
    description: "Slip-like motion near wet-floor sign zone",
    timestamp: daysAgo(4, 13, 55),
  },
  {
    anomaly_id: 12,
    user_id: "1102",
    anomaly_type: "fall",
    anomaly_score: 0.52,
    description: "Body not fully visible — reduced confidence",
    timestamp: daysAgo(5, 8, 20),
  },
  {
    anomaly_id: 13,
    user_id: "0832",
    anomaly_type: "fall",
    anomaly_score: 0.91,
    description: "Confirmed fall pattern — staff alert auto-sent",
    timestamp: daysAgo(6, 16, 8),
  },

  // ── Historical falls (fills 30d confidence histogram & area chart) ─────────
  {
    anomaly_id: 14,
    user_id: "0301",
    anomaly_type: "fall",
    anomaly_score: 0.76,
    description: "Unstable gait sequence — possible near-miss at corridor junction",
    timestamp: daysAgo(7, 14, 20),
  },
  {
    anomaly_id: 15,
    user_id: "0832",
    anomaly_type: "fall",
    anomaly_score: 0.47,
    description: "Low torso trajectory — camera occlusion reduced confidence",
    timestamp: daysAgo(9, 10, 50),
  },
  {
    anomaly_id: 16,
    user_id: "1102",
    anomaly_type: "fall",
    anomaly_score: 0.89,
    description: "Rapid floor contact — high LSTM model confidence",
    timestamp: daysAgo(11, 15, 5),
  },
  {
    anomaly_id: 17,
    user_id: "0551",
    anomaly_type: "fall",
    anomaly_score: 0.61,
    description: "Lateral sway exceeding threshold near doorway",
    timestamp: daysAgo(14, 9, 35),
  },
  {
    anomaly_id: 18,
    user_id: "0408",
    anomaly_type: "fall",
    anomaly_score: 0.82,
    description: "Confirmed fall — caregiver response within 2 minutes",
    timestamp: daysAgo(17, 16, 0),
  },
  {
    anomaly_id: 19,
    user_id: "0203",
    anomaly_type: "fall",
    anomaly_score: 0.35,
    description: "Low-confidence event — background interference, inconclusive",
    timestamp: daysAgo(21, 11, 45),
  },
  {
    anomaly_id: 20,
    user_id: "0832",
    anomaly_type: "fall",
    anomaly_score: 0.70,
    description: "Velocity spike and hip drop near service elevator",
    timestamp: daysAgo(25, 13, 30),
  },

  // ── Additional today events (boosts "Falls today" stat & chart density) ────
  {
    anomaly_id: 21,
    user_id: "0720",
    anomaly_type: "fall",
    anomaly_score: 0.17,
    description: "Likely false positive — shadow movement near door frame",
    timestamp: ago(5),
  },
  {
    anomaly_id: 22,
    user_id: "0551",
    anomaly_type: "fall",
    anomaly_score: 0.93,
    description: "Very high confidence fall — sudden full-body drop, resident floor contact confirmed",
    timestamp: ago(65),
  },
  {
    anomaly_id: 23,
    user_id: "1102",
    anomaly_type: "fall",
    anomaly_score: 0.13,
    description: "Noise in pose model — curtain movement triggered low-confidence event",
    timestamp: ago(150),
  },
  {
    anomaly_id: 24,
    user_id: "0301",
    anomaly_type: "fall",
    anomaly_score: 0.57,
    description: "Moderate trunk lean with slow recovery — possible dizziness episode",
    timestamp: ago(210),
  },
  {
    anomaly_id: 25,
    user_id: "0408",
    anomaly_type: "fall",
    anomaly_score: 0.78,
    description: "Rapid downward torso trajectory at west-wing exit",
    timestamp: ago(290),
  },

  // ── Extra day-1 events (area chart density) ───────────────────────────────
  {
    anomaly_id: 26,
    user_id: "0720",
    anomaly_type: "fall",
    anomaly_score: 0.45,
    description: "Partial body occluded — possible seated fall near bench",
    timestamp: daysAgo(1, 8, 50),
  },
  {
    anomaly_id: 27,
    user_id: "0203",
    anomaly_type: "fall",
    anomaly_score: 0.11,
    description: "Background object motion — bin moved by cleaning staff",
    timestamp: daysAgo(1, 13, 10),
  },

  // ── Extra events days 2-6 ─────────────────────────────────────────────────
  {
    anomaly_id: 28,
    user_id: "0915",
    anomaly_type: "fall",
    anomaly_score: 0.66,
    description: "Rapid knee-bend to floor level — possible controlled sit-down",
    timestamp: daysAgo(2, 16, 0),
  },
  {
    anomaly_id: 29,
    user_id: "0832",
    anomaly_type: "fall",
    anomaly_score: 0.95,
    description: "Highest-confidence event this week — full fall with no recovery motion for 4s",
    timestamp: daysAgo(3, 14, 25),
  },
  {
    anomaly_id: 30,
    user_id: "1102",
    anomaly_type: "fall",
    anomaly_score: 0.29,
    description: "Low torso dip — resident tying shoelace, marked as reviewed",
    timestamp: daysAgo(4, 10, 40),
  },
  {
    anomaly_id: 31,
    user_id: "0301",
    anomaly_type: "fall",
    anomaly_score: 0.74,
    description: "Stumble-and-recover near entrance mat — staff checked on resident",
    timestamp: daysAgo(5, 15, 30),
  },
  {
    anomaly_id: 32,
    user_id: "0408",
    anomaly_type: "fall",
    anomaly_score: 0.53,
    description: "Sudden posture drop in corridor — recovered within 2s",
    timestamp: daysAgo(6, 9, 45),
  },

  // ── More historical events (richer 30d area chart) ────────────────────────
  {
    anomaly_id: 33,
    user_id: "0720",
    anomaly_type: "fall",
    anomaly_score: 0.88,
    description: "Confirmed fall — resident unresponsive for 8s before staff arrived",
    timestamp: daysAgo(8, 11, 0),
  },
  {
    anomaly_id: 34,
    user_id: "0551",
    anomaly_type: "fall",
    anomaly_score: 0.19,
    description: "Very low confidence — LSTM disagrees with pose model, flagged for review",
    timestamp: daysAgo(10, 14, 30),
  },
  {
    anomaly_id: 35,
    user_id: "0203",
    anomaly_type: "fall",
    anomaly_score: 0.63,
    description: "Moderate fall signature — resident was bending to pick up item",
    timestamp: daysAgo(12, 10, 55),
  },
  {
    anomaly_id: 36,
    user_id: "0832",
    anomaly_type: "fall",
    anomaly_score: 0.92,
    description: "High-confidence event — chair slide caused rapid floor contact",
    timestamp: daysAgo(15, 16, 20),
  },
  {
    anomaly_id: 37,
    user_id: "1102",
    anomaly_type: "fall",
    anomaly_score: 0.44,
    description: "Borderline score — seated transition near door, posture recovered quickly",
    timestamp: daysAgo(18, 9, 10),
  },
  {
    anomaly_id: 38,
    user_id: "0301",
    anomaly_type: "fall",
    anomaly_score: 0.77,
    description: "Lateral fall with delayed recovery — caregiver notified via alert",
    timestamp: daysAgo(22, 13, 0),
  },
  {
    anomaly_id: 39,
    user_id: "0408",
    anomaly_type: "fall",
    anomaly_score: 0.85,
    description: "Slip on wet floor — LSTM score high, pose model agreed",
    timestamp: daysAgo(26, 15, 15),
  },
  {
    anomaly_id: 40,
    user_id: "0720",
    anomaly_type: "fall",
    anomaly_score: 0.16,
    description: "False alarm — rapid arm gesture near camera triggered low-score event",
    timestamp: daysAgo(28, 12, 40),
  },

  // ── Gap-fill events (completes all 30 days for the area chart) ────────────
  {
    anomaly_id: 41,
    user_id: "0551",
    anomaly_type: "fall",
    anomaly_score: 0.69,
    description: "Stair descent — sudden deceleration flagged by velocity model",
    timestamp: daysAgo(13, 11, 10),
  },
  {
    anomaly_id: 42,
    user_id: "1102",
    anomaly_type: "fall",
    anomaly_score: 0.53,
    description: "Slow descent to floor — possibly intentional, low urgency",
    timestamp: daysAgo(16, 14, 0),
  },
  {
    anomaly_id: 43,
    user_id: "0301",
    anomaly_type: "fall",
    anomaly_score: 0.87,
    description: "High-confidence fall — resident found seated on floor, uninjured",
    timestamp: daysAgo(19, 10, 30),
  },
  {
    anomaly_id: 44,
    user_id: "0832",
    anomaly_type: "fall",
    anomaly_score: 0.42,
    description: "Partial occlusion — model flagged unusual posture near door frame",
    timestamp: daysAgo(20, 15, 45),
  },
  {
    anomaly_id: 45,
    user_id: "0203",
    anomaly_type: "fall",
    anomaly_score: 0.78,
    description: "Knee buckle detected — resident steadied themselves on handrail",
    timestamp: daysAgo(23, 9, 20),
  },
  {
    anomaly_id: 46,
    user_id: "0408",
    anomaly_type: "fall",
    anomaly_score: 0.33,
    description: "Low-confidence flag — cleaning trolley movement confused pose model",
    timestamp: daysAgo(24, 13, 55),
  },
  {
    anomaly_id: 47,
    user_id: "0720",
    anomaly_type: "fall",
    anomaly_score: 0.81,
    description: "Rapid floor contact at east wing — caregiver alerted within 30s",
    timestamp: daysAgo(27, 16, 5),
  },
  {
    anomaly_id: 48,
    user_id: "0915",
    anomaly_type: "fall",
    anomaly_score: 0.58,
    description: "Moderate trunk drop — resident was picking up dropped item",
    timestamp: daysAgo(29, 10, 15),
  },
];

export const DEMO_FALL_STATUS: FallStatusResponse = {
  detector_ready: true,
  active_mode: "lstm",
  requested_mode: "lstm",
  fall_threshold: 0.62,
  velocity_window: 14,
  sequence_length: 32,
  cooldown_frames: 120,
  history_length: 45,
  artifacts: {
    pose_model_exists: true,
    lstm_model_exists: true,
    lstm_scaler_exists: true,
  },
};

function obj(
  object_class: string,
  category: ObjectDetectionEvent["category"],
  severity: ObjectDetectionEvent["severity"],
  confidence: number,
  ts: string,
  unattended = 0,
  frames = 3
): ObjectDetectionEvent {
  return {
    object_class,
    category,
    severity,
    confidence,
    unattended_seconds: unattended,
    frame_count: frames,
    timestamp: ts,
  };
}

/**
 * Demo events aligned with smart-door ops: luggage → PARCEL, person/staff gear → OPERATIONAL,
 * ambiguous props → SECURITY_THREAT, clinical/mobility → MOBILITY_AID, weapons → WEAPON.
 */
export const DEMO_OBJECT_EVENTS: ObjectDetectionEvent[] = [
  obj("handbag", "PARCEL", "MEDIUM", 0.76, hoursAgo(0, 25), 0, 5),
  obj("backpack", "PARCEL", "HIGH", 0.82, hoursAgo(0, 22), 120, 8),
  obj("suitcase", "PARCEL", "LOW", 0.88, hoursAgo(0, 19), 45, 4),
  obj("box", "PARCEL", "INFO", 0.91, hoursAgo(0, 17), 0, 6),
  obj("amazon_package", "PARCEL", "LOW", 0.79, hoursAgo(0, 14), 900, 12),
  obj("wheelchair", "MOBILITY_AID", "INFO", 0.94, hoursAgo(0, 12), 0, 4),
  obj("walker", "MOBILITY_AID", "LOW", 0.87, hoursAgo(0, 11), 30, 5),
  obj("crutch", "MOBILITY_AID", "MEDIUM", 0.71, hoursAgo(0, 9), 0, 3),
  obj("knife", "WEAPON", "CRITICAL", 0.86, hoursAgo(0, 8), 0, 9),
  obj("scissors", "WEAPON", "CRITICAL", 0.68, hoursAgo(0, 6), 0, 4),
  obj("laptop", "OPERATIONAL", "LOW", 0.92, hoursAgo(0, 5), 0, 3),
  obj("cleaning_cart", "OPERATIONAL", "INFO", 0.84, hoursAgo(0, 3), 240, 7),
  obj("person", "OPERATIONAL", "INFO", 0.73, hoursAgo(1, 50), 0, 2),
  obj("umbrella", "OPERATIONAL", "LOW", 0.66, hoursAgo(1, 45), 0, 2),
  obj("delivery_tote", "PARCEL", "MEDIUM", 0.81, hoursAgo(1, 38), 60, 5),
  obj("shopping_bag", "PARCEL", "INFO", 0.77, hoursAgo(1, 30), 0, 4),
  obj("cane", "MOBILITY_AID", "LOW", 0.89, hoursAgo(1, 22), 0, 3),
  obj("fire_extinguisher", "OPERATIONAL", "LOW", 0.93, hoursAgo(1, 15), 0, 4),
  obj("unknown_long_object", "SECURITY_THREAT", "HIGH", 0.58, hoursAgo(1, 8), 0, 6),
  obj("bottle_glass", "OPERATIONAL", "LOW", 0.62, hoursAgo(2, 55), 0, 3),
  obj("mail_bundle", "PARCEL", "LOW", 0.85, hoursAgo(2, 40), 180, 5),
  obj("stroller", "MOBILITY_AID", "INFO", 0.8, hoursAgo(2, 28), 0, 4),
  obj("trash_bin", "OPERATIONAL", "LOW", 0.72, hoursAgo(2, 12), 0, 2),
  obj("phone", "OPERATIONAL", "INFO", 0.69, hoursAgo(3, 48), 0, 2),
  obj("keys", "OPERATIONAL", "LOW", 0.55, hoursAgo(3, 35), 0, 2),
  obj("parcel_locker_item", "PARCEL", "MEDIUM", 0.83, hoursAgo(3, 20), 420, 10),
  obj("rolled_carpet", "OPERATIONAL", "MEDIUM", 0.74, hoursAgo(3, 10), 0, 5),
  obj("wheelchair_ramp", "MOBILITY_AID", "INFO", 0.9, hoursAgo(4, 44), 0, 3),
  obj("oxygen_tank", "MOBILITY_AID", "HIGH", 0.79, hoursAgo(4, 30), 0, 6),
  obj("food_tray", "OPERATIONAL", "LOW", 0.87, hoursAgo(4, 15), 0, 3),
  obj("toolbox", "OPERATIONAL", "MEDIUM", 0.7, hoursAgo(5, 50), 0, 4),
  obj("flower_pot", "OPERATIONAL", "LOW", 0.81, hoursAgo(5, 33), 720, 8),
  obj("dolly", "OPERATIONAL", "INFO", 0.78, hoursAgo(5, 18), 0, 4),
  obj("medical_bag", "OPERATIONAL", "MEDIUM", 0.86, hoursAgo(6, 40), 0, 5),
  obj("poster_tube", "PARCEL", "LOW", 0.67, hoursAgo(6, 25), 0, 3),
  obj("baseball_bat", "WEAPON", "CRITICAL", 0.77, daysAgo(0, 20, 15), 0, 7),
  obj("crowbar", "WEAPON", "HIGH", 0.64, daysAgo(1, 14, 40), 0, 5),
  obj("plastic_bag_cluster", "PARCEL", "INFO", 0.72, daysAgo(1, 11, 5), 0, 3),
  obj("wet_floor_sign", "OPERATIONAL", "INFO", 0.95, daysAgo(2, 9, 0), 0, 2),
  obj("gurney", "MOBILITY_AID", "MEDIUM", 0.88, daysAgo(2, 15, 30), 0, 6),
  obj("iv_pole", "MOBILITY_AID", "LOW", 0.75, daysAgo(3, 10, 12), 0, 4),

  // ── Days 4-7 coverage (fills 7d dashboard range) ─────────────────────────
  obj("backpack",       "PARCEL",          "HIGH",     0.79, daysAgo(4,  8, 30),  60, 5),
  obj("wheelchair",     "MOBILITY_AID",    "INFO",     0.92, daysAgo(4, 11, 15),   0, 4),
  obj("unknown_object", "SECURITY_THREAT", "HIGH",     0.61, daysAgo(4, 14,  0),   0, 6),
  obj("suitcase",       "PARCEL",          "LOW",      0.84, daysAgo(5,  9, 40), 180, 4),
  obj("knife",          "WEAPON",          "CRITICAL", 0.72, daysAgo(5, 16, 25),   0, 7),
  obj("person",         "OPERATIONAL",     "INFO",     0.78, daysAgo(5, 13, 10),   0, 3),
  obj("cane",           "MOBILITY_AID",    "LOW",      0.88, daysAgo(6, 10,  5),   0, 4),
  obj("delivery_box",   "PARCEL",          "MEDIUM",   0.83, daysAgo(6, 14, 50),  90, 6),
  obj("cleaning_cart",  "OPERATIONAL",     "LOW",      0.76, daysAgo(7,  8, 20),   0, 3),
  obj("handbag",        "PARCEL",          "INFO",     0.81, daysAgo(7, 12,  0),   0, 4),
  obj("scissors",       "WEAPON",          "CRITICAL", 0.65, daysAgo(7, 15, 35),   0, 5),

  // ── Weeks 2-4 (fills 30d range) ──────────────────────────────────────────
  obj("backpack",       "PARCEL",          "HIGH",     0.77, daysAgo(10,  9,  0),  30, 5),
  obj("walker",         "MOBILITY_AID",    "INFO",     0.90, daysAgo(10, 13, 30),   0, 4),
  obj("knife",          "WEAPON",          "CRITICAL", 0.80, daysAgo(14, 10, 15),   0, 6),
  obj("suitcase",       "PARCEL",          "MEDIUM",   0.85, daysAgo(14, 16,  0),  60, 4),
  obj("unknown_object", "SECURITY_THREAT", "HIGH",     0.57, daysAgo(18, 11,  0),   0, 5),
  obj("wheelchair",     "MOBILITY_AID",    "INFO",     0.93, daysAgo(20,  8, 30),   0, 3),
  obj("handbag",        "PARCEL",          "LOW",      0.78, daysAgo(22, 14, 15),   0, 4),
  obj("baseball_bat",   "WEAPON",          "CRITICAL", 0.75, daysAgo(25, 10,  0),   0, 7),
  obj("crutch",         "MOBILITY_AID",    "MEDIUM",   0.70, daysAgo(28,  9, 20),   0, 3),
  obj("backpack",       "PARCEL",          "HIGH",     0.82, daysAgo(28, 15, 40), 120, 5),
];

function demoObjectCategoryCounts(events: ObjectDetectionEvent[]): Partial<Record<ObjectCategory, number>> {
  const o = {} as Record<ObjectCategory, number>;
  for (const c of OBJECT_CATEGORIES) o[c] = 0;
  for (const e of events) o[normalizeObjectCategory(e.category)]++;
  return o;
}

export const DEMO_OBJECT_STATUS: ObjectStatusResponse = {
  detector_ready: true,
  weapon_model_ready: true,
  confidence: 0.48,
  frame_threshold: 4,
  unattended_minutes: 12,
  events_logged: 2184,
  category_counts: demoObjectCategoryCounts(DEMO_OBJECT_EVENTS),
  message: "YOLOv8 + custom weapon head — same camera stream as face access",
};

export const DEMO_USERS: User[] = [
  { user_id: "usr_margaret", name: "Margaret T.", display_id: "1102", role: "resident" },
  { user_id: "usr_patel", name: "Dr. Patel", display_id: "0203", role: "staff" },
  { user_id: "usr_john", name: "John D.", display_id: "0832", role: "resident" },
  { user_id: "usr_robert", name: "Robert H.", display_id: "0301", role: "resident" },
  { user_id: "usr_clarke", name: "Nurse Clarke", display_id: "0551", role: "staff" },
  { user_id: "usr_linda", name: "Linda W.", display_id: "0720", role: "staff" },
  { user_id: "usr_james", name: "James K.", display_id: "0408", role: "resident" },
  { user_id: "usr_sam", name: "Night Nurse Sam", display_id: "0915", role: "staff" },
];

const byTimeDesc = <T extends { timestamp: string }>(a: T, b: T) =>
  new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();

DEMO_THREATS.sort(byTimeDesc);
DEMO_FALL_EVENTS.sort(byTimeDesc);
DEMO_OBJECT_EVENTS.sort(byTimeDesc);
DEMO_AUDIT.sort(byTimeDesc);

// ── Demo fallback behaviour (same file — no separate demoMode module) ─────────
/**
 * When the API returns empty data, optionally substitute the demo lists above.
 * - Default: empty responses are filled so charts and tables work without a backend.
 *   Opt out with `NEXT_PUBLIC_USE_DEMO_DATA=false`.
 * - `NEXT_PUBLIC_FORCE_DEMO_DATA=true`: always use demo lists (ignores non-empty API).
 */

export function forceDemoOnly(): boolean {
  return process.env.NEXT_PUBLIC_FORCE_DEMO_DATA === "true";
}

/**
 * Returns true when demo-data fallback is active.
 *
 * Priority (highest → lowest):
 *  1. localStorage "facedoor_demo_mode" key — set by the sidebar toggle.
 *  2. NEXT_PUBLIC_USE_DEMO_DATA env var — build-time opt-out.
 *  3. Default: true (show demo data when API returns empty results).
 */
export function demoFallbackEnabled(): boolean {
  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem("facedoor_demo_mode");
    if (stored !== null) return stored === "true";
  }
  return process.env.NEXT_PUBLIC_USE_DEMO_DATA !== "false";
}

/**
 * Return demo data when the toggle is ON, or as a fallback when the API list is
 * empty.  Pass `demoEnabled` from `useDemoMode()` as the third argument so the
 * decision is driven by the React state rather than a raw localStorage read.
 *
 * Priority:
 *   1. Force-demo env var → always demo
 *   2. demoEnabled === true → always demo (overrides real data too)
 *   3. API returned data  → use real data
 *   4. API empty + demo fallback from localStorage → demo
 *   5. Otherwise → empty
 */
export function emptyOrDemo<T>(
  api: T[] | undefined | null,
  demo: T[],
  demoEnabled?: boolean,
): T[] {
  if (forceDemoOnly()) return demo;
  const enabled = demoEnabled !== undefined ? demoEnabled : demoFallbackEnabled();
  if (enabled) return demo;
  return api ?? [];
}

export function nullOrDemo<T>(
  api: T | null | undefined,
  demo: T,
  demoEnabled?: boolean,
): T | null {
  if (forceDemoOnly()) return demo;
  const enabled = demoEnabled !== undefined ? demoEnabled : demoFallbackEnabled();
  if (enabled) return demo;
  return api ?? null;
}
