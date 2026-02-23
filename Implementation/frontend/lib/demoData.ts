import { Threat, AuditEntry, AccessLog } from "./api";

// ── helpers ───────────────────────────────────────────────────────────────────
function ago(minutes: number) {
  return new Date(Date.now() - minutes * 60 * 1000).toISOString();
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
];
