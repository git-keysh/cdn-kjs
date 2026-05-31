const TIKWM_API = "https://www.tikwm.com/api/";

export async function onRequestGet(context) {
  const { request } = context;
  const { searchParams } = new URL(request.url);
  const videoUrl = searchParams.get("url");

  // Validate URL param
  if (!videoUrl) {
    return Response.json({ error: "Missing ?url= parameter" }, { status: 400 });
  }

  if (!isValidTikTokUrl(videoUrl)) {
    return Response.json({ error: "Invalid TikTok URL" }, { status: 400 });
  }

  // Fetch video info from tikwm.com
  let videoData;
  try {
    const apiRes = await fetch(TIKWM_API, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        url: videoUrl,
        hd: "1",
      }),
    });

    if (!apiRes.ok) throw new Error(`tikwm API returned ${apiRes.status}`);
    videoData = await apiRes.json();
  } catch (err) {
    return Response.json(
      { error: "Failed to fetch video metadata", details: String(err) },
      { status: 502 }
    );
  }

  // tikwm returns code 0 on success
  if (videoData.code !== 0 || !videoData.data) {
    return Response.json(
      { error: videoData.msg ?? "Could not retrieve video" },
      { status: 422 }
    );
  }

  // Prefer watermark-free HD, fall back to play, then wmplay
  const playUrl =
    videoData.data.hdplay ||
    videoData.data.play ||
    videoData.data.wmplay;

  if (!playUrl) {
    return Response.json(
      { error: "No playable URL found for this video" },
      { status: 422 }
    );
  }

  // Stream the video back to the client
  let videoRes;
  try {
    videoRes = await fetch(playUrl, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        Referer: "https://www.tiktok.com/",
      },
    });

    if (!videoRes.ok) throw new Error(`Video fetch returned ${videoRes.status}`);
  } catch (err) {
    return Response.json(
      { error: "Failed to fetch video file", details: String(err) },
      { status: 502 }
    );
  }

  const title = sanitizeFilename(videoData.data.title ?? "tiktok-video");

  const headers = new Headers({
    "Content-Type": "video/mp4",
    "Content-Disposition": `attachment; filename="${title}.mp4"`,
    "Access-Control-Allow-Origin": "*",
  });

  // Pass through content-length if available so browsers show progress
  const contentLength = videoRes.headers.get("content-length");
  if (contentLength) headers.set("Content-Length", contentLength);

  return new Response(videoRes.body, { status: 200, headers });
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function isValidTikTokUrl(url) {
  try {
    const { hostname } = new URL(url);
    return ["tiktok.com", "www.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"].includes(hostname);
  } catch {
    return false;
  }
}

function sanitizeFilename(name) {
  return name
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .substring(0, 100);
}