import { json } from '@astrojs/cloudflare';

const ZIP_URL = 'https://cdn-kjs.pages.dev/bin/ipf.zip';

export async function GET({ url }) {
  const pathname = url.pathname; 
  const query = pathname.split('=')[1]; 

  if (query === 'info') {
    const readme = {
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
    };
    return json(readme);
  }

  if (query === 'download') {
    const headers = new Headers();
    headers.set('Content-Type', 'application/zip');
    headers.set('Content-Disposition', 'attachment; filename="ipf.zip"');

    return Response.redirect(ZIP_URL, 302, { headers });
  }

  return json({ error: "Invalid request. Use =info or =download" });
}