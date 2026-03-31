import { json, redirect } from '@astrojs/cloudflare';

export async function GET({ url }) {
  const info = url.searchParams.get('info');
  const download = url.searchParams.get('download');

  if (info !== null) {
    return json({
      name: "IPF CLI",
      description: "Command-line tool for IP info, logging, and Discord webhook reporting.",
      features: [
        "Lookup IP geolocation, ISP, timezone, and Google Maps link",
        "View local PC network info (ipf -m)",
        "Save logs to Documents folder (ipf -l)",
        "Send IP info via Discord webhook (ipf -s {webhook} {ip})",
        "Portable CLI with setup batch for global PATH"
      ],
      usage: [
        "https://cdn-kjs.pages.dev/bin/ipf/dist/ipf.exe <ip>",
        "https://cdn-kjs.pages.dev/bin/ipf/dist/ipf.exe -m",
        "https://cdn-kjs.pages.dev/bin/ipf/dist/ipf.exe -l <ip>",
        "https://cdn-kjs.pages.dev/bin/ipf/dist/ipf.exe -s <webhook> <ip>"
      ]
    });
  }

  if (download !== null) {
    return redirect("https://cdn-kjs.pages.dev/bin/ipf.zip", 302);
  }

  return json({ error: "Invalid query. Use ?info or ?download" });
}