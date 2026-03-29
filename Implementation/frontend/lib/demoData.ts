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

// ── helpers ───────────────────────────────────────────────────────────────────
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
