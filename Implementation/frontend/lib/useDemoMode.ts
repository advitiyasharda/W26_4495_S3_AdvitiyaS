"use client";

/**
 * Demo-mode toggle — persisted to localStorage so it survives page reloads.
 *
 * Storage key : "facedoor_demo_mode"  ("true" | "false")
 * Custom event: "facedoor-demo-change" — fired on every write so all mounted
 *               components update instantly without a page reload.
 *
 * Default when no value is stored: demo data ON (same as the previous env-var
 * default of NEXT_PUBLIC_USE_DEMO_DATA !== "false").
 */

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "facedoor_demo_mode";
const CHANGE_EVENT = "facedoor-demo-change";

/** Read the current demo-mode value from localStorage (SSR-safe, defaults to true). */
export function isDemoEnabled(): boolean {
  if (typeof window === "undefined") return true;
  const v = window.localStorage.getItem(STORAGE_KEY);
  return v === null ? true : v === "true";
}

/** Persist the value and notify all listeners on the same page. */
export function setDemoEnabled(enabled: boolean): void {
  window.localStorage.setItem(STORAGE_KEY, String(enabled));
  window.dispatchEvent(new CustomEvent<boolean>(CHANGE_EVENT, { detail: enabled }));
}

/**
 * Hook: returns the current demo-mode state and a stable toggle function.
 * Re-renders automatically when the toggle is changed from any component or
 * from another browser tab.
 */
export function useDemoMode() {
  // Initialise to `true` — the default "demo ON" state.
  // For users who have never set the toggle, this means no hydration flash.
  // For users who explicitly turned it OFF (localStorage = "false"), the effect
  // below will snap it to false after mount (~100ms), which is acceptable.
  const [demoEnabled, setEnabled] = useState(true);

  useEffect(() => {
    // On first ever visit (localStorage key missing), write the default "true"
    // so all subsequent reads (including demoFallbackEnabled) always find a value.
    // After that, whatever the user set is respected and never overridden.
    if (window.localStorage.getItem(STORAGE_KEY) === null) {
      window.localStorage.setItem(STORAGE_KEY, "true");
    }
    setEnabled(isDemoEnabled());

    // Same-tab updates (from toggle button).
    const onCustom = (e: Event) => setEnabled((e as CustomEvent<boolean>).detail);

    // Cross-tab updates (user has another window open).
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setEnabled(e.newValue !== "false");
    };

    window.addEventListener(CHANGE_EVENT, onCustom);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(CHANGE_EVENT, onCustom);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  const toggle = useCallback(() => {
    const next = !isDemoEnabled();
    setDemoEnabled(next);
    setEnabled(next);
  }, []);

  return { demoEnabled, toggle };
}
