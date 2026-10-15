import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator, BackHandler, Linking, Pressable, ScrollView, Share,
  StyleSheet, Text, TextInput, View
} from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import * as Haptics from "expo-haptics";
import { WebView, type WebViewMessageEvent } from "react-native-webview";
import { GAME_HTML } from "./src/game.generated";
import { normalizeRoom, roomFromDeepLink, roomInviteUrl, safeOnlineOrigin } from "./src/rooms";

type Mode = "home" | "solo" | "online";
type BridgeEvent = { type: "touch" | "finished" | "invite" | "room"; code?: string };

const ORIGIN = safeOnlineOrigin(process.env.EXPO_PUBLIC_MEME_FIGHTER_URL);
const OFFLINE_HTML = GAME_HTML.replace(
  "</head>",
  "<style>.online-box{display:none!important}</style></head>"
);
const BRIDGE_SCRIPT = [
  "(function(){",
  "if(window.__memeFighterNativeBridge)return;",
  "window.__memeFighterNativeBridge=true;",
  "function post(type,code){try{window.ReactNativeWebView.postMessage(JSON.stringify({type:type,code:code}));}catch(e){}}",
  "document.addEventListener('pointerdown',function(e){if(e.target.closest('.touch-btn'))post('touch');},{passive:true});",
  "var local=document.getElementById('mode');",
  "if(local&&location.protocol!=='https:'){var opt=local.querySelector('option[value=local]');if(opt)opt.remove();}",
  "var codeEl=document.getElementById('room-code');",
  "if(codeEl){var notify=function(){var c=codeEl.textContent.trim().toUpperCase();if(/^[A-HJ-NP-Z2-9]{6}$/.test(c))post('room',c);};",
  "new MutationObserver(notify).observe(codeEl,{childList:true,characterData:true,subtree:true});notify();}",
  "var copy=document.getElementById('copy-room');",
  "if(copy)copy.addEventListener('click',function(e){",
  "var c=codeEl&&codeEl.textContent.trim().toUpperCase();",
  "if(/^[A-HJ-NP-Z2-9]{6}$/.test(c)){e.preventDefault();e.stopImmediatePropagation();post('invite',c);}",
  "},true);",
  "var result=document.getElementById('result');",
  "if(result)new MutationObserver(function(){if(!result.hidden)post('finished');}).observe(result,{attributes:true,attributeFilter:['hidden']});",
  "})();true;"
].join("");

function Control({ label, onPress, tone = "dark" }: {
  label: string; onPress: () => void; tone?: "dark" | "mint" | "pink";
}) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress}
      style={[styles.control, tone === "mint" ? styles.mint : tone === "pink" ? styles.pink : styles.dark]}>
      <Text style={[styles.controlText, tone === "mint" && styles.inkText]}>{label}</Text>
    </Pressable>
  );
}

function FighterApp() {
  const [mode, setMode] = useState<Mode>("home");
  const [roomInput, setRoomInput] = useState("");
  const [initialRoom, setInitialRoom] = useState<string | null>(null);
  const [activeRoom, setActiveRoom] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const lastHaptic = useRef(0);

  const openOnline = useCallback((room: string | null = null) => {
    setInitialRoom(room);
    setActiveRoom(room);
    setLoadError(null);
    setRetry(x => x + 1);
    setMode("online");
  }, []);

  useEffect(() => {
    const onLink = (url: string) => {
      const code = roomFromDeepLink(url, ORIGIN);
      if (code) openOnline(code);
    };
    Linking.getInitialURL().then(url => { if (url) onLink(url); }).catch(() => {});
    const listener = Linking.addEventListener("url", e => onLink(e.url));
    return () => listener.remove();
  }, [openOnline]);

  useEffect(() => {
    const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
      if (mode === "home") return false;
      setMode("home");
      setActiveRoom(null);
      return true;
    });
    return () => subscription.remove();
  }, [mode]);

  const webUrl = useMemo(() =>
    ORIGIN ? ORIGIN + (initialRoom ? "/?room=" + encodeURIComponent(initialRoom) : "/") : null,
    [initialRoom]
  );

  const shareRoom = useCallback(async (code: string) => {
    if (!ORIGIN) return;
    try {
      await Share.share({ message: "Fight me in Meme Fighter: " + roomInviteUrl(ORIGIN, code) });
    } catch {
      // The system share sheet was closed or not available.
    }
  }, []);

  const onGameMessage = useCallback((event: WebViewMessageEvent) => {
    let payload: BridgeEvent;
    try { payload = JSON.parse(event.nativeEvent.data) as BridgeEvent; }
    catch { return; }
    if (payload.type === "touch") {
      const now = Date.now();
      if (now - lastHaptic.current >= 140) {
        lastHaptic.current = now;
        void Haptics.selectionAsync().catch(() => {});
      }
    } else if (payload.type === "finished") {
      void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    } else if ((payload.type === "room" || payload.type === "invite") && typeof payload.code === "string") {
      const code = normalizeRoom(payload.code);
      if (!code) return;
      setActiveRoom(code);
      if (payload.type === "invite") void shareRoom(code);
    }
  }, [shareRoom]);

  const goHome = () => {
    setMode("home");
    setActiveRoom(null);
    setLoadError(null);
  };

  const canJoin = Boolean(ORIGIN && normalizeRoom(roomInput));

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="light" backgroundColor="#100d27" />
      {mode === "home" ? (
        <ScrollView contentContainerStyle={styles.home}>
          <Text style={styles.kicker}>ARCADE / MOBILE BETA 001</Text>
          <Text style={styles.title}>MEME <Text style={styles.star}>✳</Text> FIGHTER</Text>
          <Text style={styles.headline}>SETTLE THE COMMENTS.</Text>
          <Text style={styles.description}>
            Four fighters. Two arenas. Combo chains, signature specials, and a best-of-three knockout.
          </Text>
          <View style={styles.hero}>
            <Text style={styles.heroEmoji}>🐕  🔥</Text>
            <Text style={styles.heroTitle}>OFFLINE ARCADE</Text>
            <Text style={styles.heroDetail}>Fight the CPU on your iPhone. No account or internet required.</Text>
            <Control label="▶ PLAY SOLO" tone="mint" onPress={() => {
              setLoadError(null);
              setRetry(x => x + 1);
              setMode("solo");
            }} />
          </View>
          <View style={styles.onlinePanel}>
            <Text style={styles.panelLabel}>⚡ PRIVATE ONLINE 1 VS 1</Text>
            <Text style={styles.heroDetail}>Invite a friend, pick a fighter, and fight across two phones.</Text>
            {ORIGIN ? (
              <>
                <Control label="CREATE ONLINE ROOM" tone="pink" onPress={() => openOnline()} />
                <TextInput
                  accessibilityLabel="Six character room code"
                  autoCapitalize="characters"
                  autoCorrect={false}
                  maxLength={6}
                  placeholder="ENTER 6-CHARACTER ROOM CODE"
                  placeholderTextColor="#9686b0"
                  value={roomInput}
                  onChangeText={setRoomInput}
                  style={styles.input}
                />
                <Pressable accessibilityRole="button" disabled={!canJoin}
                  onPress={() => { const code = normalizeRoom(roomInput); if (code) openOnline(code); }}
                  style={[styles.control, styles.dark, !canJoin && styles.disabled]}>
                  <Text style={styles.controlText}>JOIN ROOM ↗</Text>
                </Pressable>
              </>
            ) : (
              <Text style={styles.warning}>
                Online rooms need a deployed HTTPS game server. Configure EXPO_PUBLIC_MEME_FIGHTER_URL to enable multiplayer.
              </Text>
            )}
          </View>
          <Text style={styles.tip}>TIP · Use the on-screen D-pad and attack buttons. Offline mode includes Easy, Normal and Hard CPU.</Text>
          <Text style={styles.footer}>CASUAL BETA · NO CASH MATCHES · ONLINE REQUIRES INTERNET</Text>
        </ScrollView>
      ) : (
        <View style={styles.playArea}>
          <View style={styles.toolbar}>
            <Pressable accessibilityRole="button" onPress={goHome} style={styles.back}>
              <Text style={styles.backText}>‹ HOME</Text>
            </Pressable>
            <View style={styles.toolbarTitle}>
              <Text style={styles.toolbarKicker}>{mode === "solo" ? "OFFLINE · CPU" : "ONLINE · 1V1"}</Text>
              <Text style={styles.toolbarBrand}>MEME FIGHTER</Text>
            </View>
            {mode === "online" && activeRoom ? (
              <Control label="SHARE" tone="mint" onPress={() => { void shareRoom(activeRoom); }} />
            ) : (
              <Control label="RESET" onPress={() => { setLoadError(null); setRetry(x => x + 1); }} />
            )}
          </View>
          {mode === "online" && !webUrl ? (
            <View style={styles.error}>
              <Text style={styles.heroTitle}>ONLINE NOT CONFIGURED</Text>
              <Text style={styles.description}>Set a valid HTTPS game server in the EAS environment before building.</Text>
              <Control label="BACK TO ARCADE" tone="mint" onPress={goHome} />
            </View>
          ) : loadError ? (
            <View style={styles.error}>
              <Text style={styles.heroTitle}>GAME CONNECTION LOST</Text>
              <Text style={styles.description}>{loadError}</Text>
              <Control label="TRY AGAIN" tone="mint" onPress={() => { setLoadError(null); setRetry(x => x + 1); }} />
              <Control label="PLAY OFFLINE" onPress={() => { setMode("solo"); setLoadError(null); }} />
            </View>
          ) : (
            <WebView
              key={mode + ":" + (initialRoom || "") + ":" + retry}
              style={styles.webview}
              source={mode === "solo" ? { html: OFFLINE_HTML } : { uri: webUrl! }}
              originWhitelist={["*"]}
              javaScriptEnabled
              domStorageEnabled
              startInLoadingState
              injectedJavaScript={BRIDGE_SCRIPT}
              onMessage={onGameMessage}
              onShouldStartLoadWithRequest={request => {
                if (request.url.startsWith("about:") || request.url.startsWith("data:")) return true;
                if (mode === "solo") return false;
                try { return Boolean(ORIGIN && new URL(request.url).origin === ORIGIN); }
                catch { return false; }
              }}
              onError={event => setLoadError(event.nativeEvent.description || "Unable to load game")}
              onHttpError={event => {
                if (event.nativeEvent.statusCode >= 400 && event.nativeEvent.url === webUrl)
                  setLoadError("Server returned HTTP " + event.nativeEvent.statusCode);
              }}
              renderLoading={() => <View style={styles.loading}><ActivityIndicator color="#61f5cf" size="large" /></View>}
            />
          )}
        </View>
      )}
    </SafeAreaView>
  );
}

export default function App() {
  return <SafeAreaProvider><FighterApp /></SafeAreaProvider>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#100d27" },
  home: { paddingHorizontal: 22, paddingTop: 30, paddingBottom: 44, gap: 15 },
  kicker: { color: "#61f5cf", fontSize: 11, fontWeight: "900", letterSpacing: 2 },
  title: { color: "#fff", fontSize: 36, fontWeight: "900", letterSpacing: -2 },
  star: { color: "#61f5cf" },
  headline: { color: "#f7de81", fontSize: 23, fontWeight: "900" },
  description: { color: "#cfc3e3", fontSize: 14, lineHeight: 22 },
  hero: { backgroundColor: "#2a1e49", borderWidth: 2, borderColor: "#715696", padding: 20, borderRadius: 22, gap: 10 },
  heroEmoji: { fontSize: 62, textAlign: "center", paddingVertical: 8 },
  heroTitle: { fontSize: 21, fontWeight: "900", color: "#fff" },
  heroDetail: { color: "#c5b8d7", lineHeight: 21, fontSize: 13 },
  onlinePanel: { padding: 18, borderWidth: 1, borderColor: "#655680", borderRadius: 20, gap: 12 },
  panelLabel: { color: "#ff86bc", fontWeight: "900", fontSize: 13, letterSpacing: 1 },
  control: { paddingVertical: 12, paddingHorizontal: 14, borderRadius: 12, justifyContent: "center", alignItems: "center", minHeight: 45 },
  controlText: { fontSize: 12, color: "#fff", fontWeight: "900", letterSpacing: 0.6 },
  inkText: { color: "#17202b" },
  mint: { backgroundColor: "#61f5cf" },
  pink: { backgroundColor: "#8c3374", borderWidth: 1, borderColor: "#ff77bc" },
  dark: { backgroundColor: "#302647", borderWidth: 1, borderColor: "#716187" },
  input: { backgroundColor: "#221b37", borderWidth: 1, borderColor: "#655680", color: "#fff", fontWeight: "800", textAlign: "center", fontSize: 15, letterSpacing: 1, padding: 13, borderRadius: 12 },
  disabled: { opacity: 0.4 },
  warning: { color: "#ffd49f", lineHeight: 20 },
  tip: { color: "#b8a9ce", fontSize: 12, lineHeight: 18 },
  footer: { color: "#8e80ac", fontSize: 10, letterSpacing: 1, marginTop: 12 },
  playArea: { flex: 1 },
  toolbar: { flexDirection: "row", alignItems: "center", paddingHorizontal: 10, paddingVertical: 8, backgroundColor: "#1b1532", gap: 7 },
  back: { borderRadius: 9, paddingHorizontal: 10, paddingVertical: 14 },
  backText: { color: "#61f5cf", fontWeight: "900", fontSize: 13 },
  toolbarTitle: { flex: 1, alignItems: "center" },
  toolbarKicker: { color: "#bba6de", fontSize: 9, letterSpacing: 1.2 },
  toolbarBrand: { color: "#fff", fontSize: 15, fontWeight: "900" },
  error: { flex: 1, justifyContent: "center", gap: 16, padding: 25 },
  webview: { flex: 1, backgroundColor: "#100d27" },
  loading: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#100d27" }
});
