export const ROOM_CODE = /^[A-HJ-NP-Z2-9]{6}$/;

export function normalizeRoom(value: string): string | null {
  const code = value.trim().toUpperCase();
  return ROOM_CODE.test(code) ? code : null;
}

export function safeOnlineOrigin(value: string | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value.trim());
    if (url.protocol !== "https:" || url.username || url.password ||
      url.search || url.hash || (url.pathname !== "/" && url.pathname !== "")) return null;
    return url.origin;
  } catch {
    return null;
  }
}

export function roomFromDeepLink(link: string, origin: string | null): string | null {
  try {
    const url = new URL(link);
    if (url.protocol === "memefighter:" && url.hostname === "room") {
      return normalizeRoom(decodeURIComponent(url.pathname.replace(/^\//, "")));
    }
    if (origin && url.protocol === "https:" && url.origin === origin &&
      (url.pathname === "/" || url.pathname === "")) {
      return normalizeRoom(url.searchParams.get("room") || "");
    }
  } catch {
    return null;
  }
  return null;
}

export function roomInviteUrl(origin: string, code: string): string {
  const room = normalizeRoom(code);
  if (!room || safeOnlineOrigin(origin) !== origin) throw new Error("Invalid room or online origin");
  return origin + "/?room=" + encodeURIComponent(room);
}
